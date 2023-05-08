"""
    Strategy base class
"""
from datetime import datetime
from v2realbot.utils.utils import AttributeDict, zoneNY, is_open_rush, is_close_rush, json_serial, print
from v2realbot.utils.tlog import tlog
from v2realbot.utils.ilog import insert_log, insert_log_multiple
from v2realbot.enums.enums import RecordType, StartBarAlign, Mode, Order, Account
from v2realbot.config import BT_DELAYS, get_key, HEARTBEAT_TIMEOUT, QUIET_MODE, LOG_RUNNER_EVENTS
import queue
#from rich import print
from v2realbot.loader.aggregator import TradeAggregator2Queue, TradeAggregator2List, TradeAggregator
from v2realbot.loader.order_updates_streamer import LiveOrderUpdatesStreamer
from v2realbot.loader.trade_offline_streamer import Trade_Offline_Streamer
from v2realbot.loader.trade_ws_streamer import Trade_WS_Streamer
from v2realbot.interfaces.general_interface import GeneralInterface
from v2realbot.interfaces.backtest_interface import BacktestInterface
from v2realbot.interfaces.live_interface import LiveInterface
from alpaca.trading.enums import OrderSide
from v2realbot.backtesting.backtester import Backtester
#from alpaca.trading.models import TradeUpdate
from v2realbot.common.model import TradeUpdate
from alpaca.trading.enums import TradeEvent, OrderStatus
from threading import Event, current_thread
import json
from uuid import UUID

# obecna Parent strategie podporující queues
class Strategy:
    def __init__(self, name: str, symbol: str, next: callable, init: callable, account: Account, mode: str = Mode.PAPER, stratvars: AttributeDict = None, open_rush: int = 30, close_rush: int = 30, pe: Event = None, se: Event = None, runner_id: UUID = None, ilog_save: bool = False) -> None:
        #variable to store methods overriden by strategytypes (ie pre plugins)
        self.overrides = None
        self.symbol = symbol
        self.next = next
        self.init = init
        self.mode = mode
        self.stratvars = stratvars
        self.name = name
        self.time = None
        self.rectype: RecordType = None
        self.nextnew = 1
        self.btdata: list = []
        self.interface: GeneralInterface = None
        self.state: StrategyState = None
        self.bt: Backtester = None
        self.debug = False
        self.debug_target_iter = 0
        self.debug_iter_cnt = 0
        #skip morning or closing rush
        self.open_rush = open_rush
        self.close_rush = close_rush
        self._streams = []
        self.account = account
        self.key = get_key(mode=self.mode, account=self.account)
        self.rtqueue = None
        self.runner_id = runner_id
        self.ilog_save = ilog_save


        #TODO predelat na dynamické queues
        self.q1 = queue.Queue()
        self.q2 = queue.Queue()
        self.q3 = queue.Queue()

        self.set_mode(mode=mode)

        #pause event and end event
        self.pe = pe
        self.se = se

    #prdelat queue na dynamic - podle toho jak bud uchtit pracovat s multiresolutions
    #zatim jen jedna q1
    #TODO zaroven strategie musi vedet o rectypu, protoze je zpracovava
    def add_data(self,
            symbol: str,
            rectype: RecordType = RecordType.BAR,
            timeframe: int = 5,
            minsize: int = 100,
            update_ltp: bool = False,
            align: StartBarAlign = StartBarAlign.ROUND,
            mintick: int = 0,
            exthours: bool = False):
        
        ##TODO vytvorit self.datas_here containing dict - queue - SYMBOL - RecType - 
        ##zatim natvrdo
        ##stejne tak podporit i ruzne resolutions, zatim take natvrdo prvni
        self.rectype = rectype
        self.state.rectype = rectype
        self.state.timeframe = timeframe
        stream = TradeAggregator2Queue(symbol=symbol,queue=self.q1,rectype=rectype,timeframe=timeframe,update_ltp=update_ltp,align=align,mintick = mintick, exthours=exthours, minsize=minsize)
        self._streams.append(stream)
        self.dataloader.add_stream(stream)

    """Allow client to set LIVE or BACKTEST mode"""
    def set_mode(self, mode: Mode, start: datetime = None, end: datetime = None, cash = None, debug: bool = False):
        #ic(f"mode {mode} selected")

        if mode == Mode.BT and (not start or not end):
            print("start/end required")
            return -1
        
        self.debug = debug
        self.key = get_key(mode=mode, account=self.account)
        
        if mode == Mode.LIVE or mode == Mode.PAPER:
            #data loader thread
            self.dataloader = Trade_WS_Streamer(name="WS-LDR-"+self.name)
            self.interface = LiveInterface(symbol=self.symbol, key=self.key)
            # order notif thread
            self.order_notifs = LiveOrderUpdatesStreamer(key=self.key, name="WS-STRMR-" + self.name)
            #propojujeme notifice s interfacem (pro callback)
            self.order_notifs.connect_callback(self)
            self.state = StrategyState(name=self.name, symbol = self.symbol, stratvars = self.stratvars, interface=self.interface, rectype=self.rectype, runner_id=self.runner_id, ilog_save=self.ilog_save)

        elif mode == Mode.BT:
            self.dataloader = Trade_Offline_Streamer(start, end, btdata=self.btdata)
            self.bt = Backtester(symbol = self.symbol, order_fill_callback= self.order_updates, btdata=self.btdata, cash=cash, bp_from=start, bp_to=end)
            self.interface = BacktestInterface(symbol=self.symbol, bt=self.bt)
            self.state = StrategyState(name=self.name, symbol = self.symbol, stratvars = self.stratvars, interface=self.interface, rectype=self.rectype, runner_id=self.runner_id, bt=self.bt, ilog_save=self.ilog_save)
            self.order_notifs = None
            ##streamer bude plnit trady do listu trades - nad kterym bude pracovat paper trade
            #zatim takto - pak pripadne do fajlu nebo jinak OPTIMALIZOVAT
            self.dataloader.add_stream(TradeAggregator2List(symbol=self.symbol,btdata=self.btdata,rectype=RecordType.TRADE))
        else:
            print("unknow mode")
            return -1
        
        self.mode = mode
        self.state.mode = self.mode

    """SAVE record to respective STATE variables (bar or trades)
    ukládáme i index pro případné indikátory - pro zobrazení v grafu
    -----  NO support for simultaneous rectypes in one queue """
    def save_item_history(self,item):
        if self.rectype == RecordType.BAR:
            #jako cas indikatorů pridavame cas baru, jejich hodnoty se naplni v nextu
            self.state.indicators['time'].append(item['time'])
            self.append_bar(self.state.bars,item)
        elif self.rectype == RecordType.TRADE:
            pass
            #implementovat az podle skutecnych pozadavku
            #self.state.indicators['time'].append(datetime.fromtimestamp(self.state.last_trade_time))
            #self.append_trade(self.state.trades,item)
        elif self.rectype == RecordType.CBAR:
            #novy vzdy pridame
            if self.nextnew:
                self.state.indicators['time'].append(item['time'])
                self.append_bar(self.state.bars,item)
                self.nextnew = 0
            #nasledujici updatneme, po potvrzeni, nasleduje novy bar
            else:
                if item['confirmed'] == 0:
                    self.state.indicators['time'][-1]=item['time']
                    self.replace_prev_bar(self.state.bars,item)
                #confirmed
                else:
                    self.state.indicators['time'][-1]=item['time']
                    self.replace_prev_bar(self.state.bars,item)
                    self.nextnew = 1

    """"refresh positions and avgp - for CBAR once per confirmed, for BARS each time"""
    def refresh_positions(self, item):
        if self.rectype == RecordType.BAR:
            self.state.avgp, self.state.positions = self.interface.pos()
        elif self.rectype == RecordType.CBAR and item['confirmed'] == 1:
            self.state.avgp, self.state.positions= self.interface.pos()

    """update state.last_trade_time a time of iteration"""
    def update_times(self, item):
        if self.rectype == RecordType.BAR or self.rectype == RecordType.CBAR:
            self.state.last_trade_time = item['updated']
        elif self.rectype == RecordType.TRADE:
            self.state.last_trade_time = item['t']
        if self.mode == Mode.BT:
            self.bt.time = self.state.last_trade_time + BT_DELAYS.trigger_to_strat
            self.state.time = self.state.last_trade_time + BT_DELAYS.trigger_to_strat
        elif self.mode == Mode.LIVE or self.mode == Mode.PAPER:
            self.state.time = datetime.now().timestamp()
        #ic('time updated')
    def strat_loop(self, item):

        ##TODO do samostatne funkce
        if self.debug:
            self.debug_iter_cnt += 1
            if (self.debug_iter_cnt >= self.debug_target_iter):
                try:
                    cnt = int(input("Press enter for next iteration or number to skip"))
                    self.debug_target_iter = self.debug_iter_cnt + cnt
                except ValueError:
                    self.debug_target_iter = self.debug_iter_cnt + 1

            


        self.update_times(item)
        ## BT - execute orders that should have been filled until this time
        ##do objektu backtest controller?

        #ic(self.state.time)

        if self.mode == Mode.BT:
            #self.state.ilog(e="----- BT exec START", msg=f"{self.bt.time=}")
            #pozor backtester muze volat order_updates na minuly cas - nastavi si bt.time
            self.bt.execute_orders_and_callbacks(self.state.time)
            #ic(self.bt.time)

        #ic(self.state.time)

        #volame jeste jednou update_times, kdyby si BT nastavil interfaces na jiny cas (v ramci callbacku notifikací)
        self.update_times(item)
        #ic(self.state.time)

        if self.mode == Mode.BT:
            pass
            #self.state.ilog(e="----- BT exec FINISH", msg=f"{self.bt.time=}")
            #ic(self.bt.time)
            #ic(len(self.btdata))
            #ic(self.bt.cash)

        self.save_item_history(item)
        #nevyhodit ten refresh do TypeLimit? asi ANO
        self.refresh_positions(item)
        #calling plugin (can be overriden to do some additional steps)
        self.before_iteration()
        ted = datetime.fromtimestamp(self.state.time).astimezone(zoneNY)
        if is_open_rush(ted, self.open_rush) or is_close_rush(ted, self.close_rush):
            #self.state.ilog(e="Rush hour - skipping")
            #identifikatory jsou ulozeny vektorove, tzn. kdyz nejdeme dovnitr iterace(tak nepotrebujeme prazdny cas pro tuto iteraci)
            #hodnoty time a identifikatoru musi byt stejne
            #TBD pripdane predelat  a dodelat pro CBARy az je budu pouzivat
            if self.rectype == RecordType.BAR:
               self.state.indicators['time'].pop() 
            elif self.rectype == RecordType.CBAR:
                print("RUSH skipping NOT IMPLEMENTED for CBARs yet")

        else:
            self.next(item, self.state)
            self.after_iteration(item)
            
    ##run strategy live
    def start(self):
        
        if not self.dataloader:
            print("Set mode first")

        print(40*"-",self.mode, "STRATEGY ***", self.name,"*** STARTING",40*"-")
        #data loader thread
        self.dataloader.start()

        if self.mode == Mode.LIVE or self.mode == Mode.PAPER:
            #live notification thread
            self.order_notifs.start()
        else:
            self.bt.backtest_start = datetime.now()

        self.strat_init()
        #print(self.init)
        self.init(self.state)
        
        #main strat loop
        print(self.name, "Waiting for DATA")
        while True:
            try:
                #block 5s, after that check signals
                item = self.q1.get(timeout=HEARTBEAT_TIMEOUT)
            except queue.Empty:
                #check signals
                if self.se.is_set():
                    print(current_thread().name, "Stopping signal")
                    break
                if self.pe.is_set():
                    print(current_thread().name, "Paused.")
                    continue
                else:
                    print(current_thread().name, "HEARTBEAT - no trades or signals")
                    continue
            #prijde posledni zaznam nebo stop event signal 
            if item == "last" or self.se.is_set():
                print(current_thread().name, "stopping")
                break
            elif self.pe.is_set():
                print(current_thread().name, "Paused.")
                continue
            #self.state.iter_log(event="INGEST",msg="New data ingested", item=item)
            print("New data ingested")
            #calling main loop
            self.strat_loop(item=item)

        tlog(f"FINISHED")
        print(40*"*",self.mode, "STRATEGY ", self.name,"STOPPING",40*"*")

        self.stop()

        if self.mode == Mode.BT:
            print("REQUEST COUNT:", self.interface.mincnt)

            self.bt.backtest_end = datetime.now()
            #print(40*"*",self.mode, "BACKTEST RESULTS",40*"*")
            #-> account, cash,trades,open_orders
            #self.bt.display_backtest_result(self.state)

    #this is(WILL BE) called when strategy is stopped 
    # LIVE - pause or stop signal received
    # BT - last item processed signal received
    def stop(self):

        #disconnect strategy from websocket trader updates
        if self.mode == Mode.LIVE or self.mode == Mode.PAPER:
            self.order_notifs.disconnect_callback(self)

        #necessary only for shared loaders (to keep it running for other stratefies)
        for i in self._streams:
            print(self.name, "Removing stream",i)
            self.dataloader.remove_stream(i)
        #pamatujeme si streamy, ktere ma strategie a tady je removneme

        #posilame break na RT queue na frontend
        if self.rtqueue is not None:
                self.rtqueue.put("break")

        #zavolame na loaderu remove streamer - mohou byt dalsi bezici strategie, ktery loader vyuzivaji
        #pripadne udelat shared loader a nebo dedicated loader
        #pokud je shared tak volat remove

        #refactor for multiprocessing
        # if self.mode == Mode.LIVE:
        #     self.order_notifs.stop()
        # self.dataloader.stop()

    #for order updates from LIVE or BACKTEST
    #updates are sent only for SYMBOL of strategy

    async def order_updates(self, data: TradeUpdate):
        if self.mode == Mode.LIVE or self.mode == Mode.PAPER:
            now = datetime.now().timestamp()
        else:
            now = self.bt.time

        self.state.ilog(e="NOTIF ARRIVED AT"+str(now))
        print("NOTIFICATION ARRIVED AT:", now)
        self.update_live_timenow()

        #pokud jde o FILL zapisujeme do self.trades a notifikujeme
        if data.event == TradeEvent.FILL:
            self.state.tradeList.append(data)
                
        ##TradeUpdate objekt better?
        order: Order = data.order
        if order.side == OrderSide.BUY:
            await self.orderUpdateBuy(data)
        if order.side == OrderSide.SELL:
            await self.orderUpdateSell(data)

    async def orderUpdateBuy(self, data):
        print(data)

    async def orderUpdateSell(self,data):   
        print(data)

    #pouze pro live a paper
    def update_live_timenow(self):
            if self.mode == Mode.LIVE or self.mode == Mode.PAPER:
                self.state.time = datetime.now().timestamp()

    ##method to override by child class. Allows to call specific code right before running next iteration.
    def before_iteration(self):
        self.update_live_timenow()

    ##kroky po iteraci
    def after_iteration(self, item):
        #sends real time updates to frontend if requested
        self.send_rt_updates(item)       
 

    # inicializace poplatna typu strategie (např. u LIMITu dotažení existující limitky)
    def strat_init(self):
        pass

    def send_rt_updates(self, item):
        ##if real time chart is requested
        ##posilame dict s objekty: bars, trades podle cbaru, a dale indicators naplnene time a pripadnymi identifikatory (EMA)
        if self.rtqueue is not None:
            rt_out = dict()
            
            if self.rectype == RecordType.BAR or self.rectype == RecordType.CBAR:
                rt_out["bars"] = item
            else:
                rt_out["trades"] = item
            #get only last values from indicators, if there are any indicators present
            if len(self.state.indicators) > 0:
                rt_out["indicators"] = dict()
                for key, value in self.state.indicators.items():
                        #odchyceny pripad, kdy indikatory jsou inicializovane, ale jeste v nich nejsou data, pak do WS nic neposilame
                        try:
                            rt_out["indicators"][key]= value[-1]
                        #zatim takto odchycene identifikatory, ktere nemaji list, ale dict - do budoucna predelat na samostatny typ "indicators_static"
                        except IndexError:
                            pass

            #same for static indicators
            if len(self.state.statinds) > 0:
                rt_out["statinds"] = dict()
                for key, value in self.state.statinds.items():
                    rt_out["statinds"][key] = value

            #vkladame average price and positions, pokud existuji
            #self.state.avgp , self.state.positions
            rt_out["positions"] = dict(time=self.state.time, positions=self.state.positions, avgp=self.state.avgp)

            #vkladame limitku a pendingbuys
            try:
                rt_out["pendingbuys"] = self.state.vars.pendingbuys 
                rt_out["limitka"] = dict(id=self.state.vars.limitka, price=self.state.vars.limitka_price)

            except Exception as e:
                print(str(e))
                pass

            #vkladame iteration log (do toho si muze instance vlozit cokoliv relavantniho pro danou iteraci) a po iteraci se smaze
            if len(self.state.iter_log_list) > 0:
                rt_out["iter_log"] = self.state.iter_log_list

            #print(rt_out)

            print("RTQUEUE INSERT")
            #send current values to Realtime display on frontend
            #all datetime values are converted to timestamp
            if self.rtqueue is not None:
                self.rtqueue.put(json.dumps(rt_out, default=json_serial))
                print("RTQUEUE", self.rtqueue)

            #cleaning iterlog lsit
            #TODO pridat cistku i mimo RT blok
        
        if self.ilog_save: insert_log_multiple(self.state.runner_id, self.state.iter_log_list)
        #smazeme logy
        self.state.iter_log_list = []

    @staticmethod
    def append_bar(history_reference, new_bar: dict):
        history_reference['open'].append(new_bar['open'])
        history_reference['high'].append(new_bar['high'])
        history_reference['low'].append(new_bar['low'])
        history_reference['close'].append(new_bar['close'])
        history_reference['hlcc4'].append(new_bar['hlcc4'])
        history_reference['volume'].append(new_bar['volume'])
        history_reference['time'].append(new_bar['time'])
        history_reference['trades'].append(new_bar['trades'])
        history_reference['resolution'].append(new_bar['resolution'])
        history_reference['vwap'].append(new_bar['vwap'])
        history_reference['confirmed'].append(new_bar['confirmed'])
        history_reference['index'].append(new_bar['index'])
        history_reference['updated'].append(new_bar['updated'])

    @staticmethod
    def append_trade(history_reference, new_trade: dict):
        history_reference['t'].append(new_trade['t'])
        history_reference['x'].append(new_trade['x'])
        history_reference['p'].append(new_trade['p'])
        history_reference['s'].append(new_trade['s'])
        history_reference['c'].append(new_trade['c'])
        history_reference['i'].append(new_trade['i'])
        history_reference['z'].append(new_trade['z'])

    @staticmethod
    def replace_prev_bar(history_reference, new_bar: dict):
        history_reference['open'][-1]=new_bar['open']
        history_reference['high'][-1]=new_bar['high']
        history_reference['low'][-1]=new_bar['low']
        history_reference['close'][-1]=new_bar['close']
        history_reference['hlcc4'][-1]=new_bar['hlcc4']
        history_reference['volume'][-1]=new_bar['volume']
        history_reference['time'][-1]=new_bar['time']
        history_reference['trades'][-1]=new_bar['trades']
        history_reference['resolution'][-1]=new_bar['resolution']
        history_reference['vwap'][-1]=new_bar['vwap']
        history_reference['confirmed'][-1]=new_bar['confirmed']
        history_reference['index'][-1]=new_bar['index']
        history_reference['updated'][-1]=new_bar['updated']
class StrategyState:
    """Strategy Stat object that is passed to callbacks
        note: 
          state.time
          state.interface.time
          většinou mají stejnou hodnotu, ale lišit se mužou např. v případě BT callbacku - kdy se v rámci okna končící state.time realizují objednávky, které
          triggerují callback, který následně vyvolá např. buy (ten se musí ale udít v čase fillu, tzn. callback si nastaví čas interfacu na filltime)
          po dokončení bt kroků před zahájením iterace "NEXT" se časy znovu updatnout na původni state.time
    """
    def __init__(self, name: str, symbol: str, stratvars: AttributeDict, bars: AttributeDict = {}, trades: AttributeDict = {}, interface: GeneralInterface = None, rectype: RecordType = RecordType.BAR, runner_id: UUID = None, bt: Backtester = None, ilog_save: bool = False):
        self.vars = stratvars
        self.interface = interface
        self.positions = 0
        self.avgp = 0
        self.blockbuy = 0
        self.name = name
        self.symbol = symbol
        self.rectype = rectype
        #LIVE - now()
        #BACKTEST - allows the interface to realize past events
        self.time = 0
        #time of last trade processed
        self.last_trade_time = 0
        self.timeframe = None
        self.runner_id = runner_id
        self.bt = bt
        self.ilog_save = ilog_save

        bars = {'high': [], 
                                'low': [],
                                'volume': [],
                                'close': [],
                                'hlcc4': [],
                                'open': [],
                                'time': [],
                                'trades':[],
                                'resolution':[],
                                'confirmed': [],
                                'vwap': [],
                                'updated': [],
                                'index': []}
        
        trades = {'t': [], 
                                'x': [],
                                'p': [],
                                's': [],
                                'c': [],
                                'i': [],
                                'z': []}
        
        self.bars = AttributeDict(bars)
        self.trades = AttributeDict(trades)
        self.indicators = AttributeDict(time=[])
        self.statinds = AttributeDict()
        #these methods can be overrided by StrategyType (to add or alter its functionality)
        self.buy = self.interface.buy
        self.buy_l = self.interface.buy_l
        self.sell = self.interface.sell
        self.sell_l = self.interface.sell_l
        self.cancel_pending_buys = None
        self.iter_log_list = []
        self.profit = 0
        self.tradeList = []
        self.mode = None
    
    def ilog(self, e: str = None, msg: str = None, **kwargs):
        if self.mode == Mode.LIVE or self.mode == Mode.PAPER:
            self.time = datetime.now().timestamp()

        #pri backtestingu logujeme BT casem (muze byt jiny nez self.time - napr. pri notifikacich a naslednych akcích)
        if self.mode == Mode.BT:
            time = self.bt.time
        else:
            time = self.time

        if e is None:
            if msg is None:
                row = dict(time=time, details=kwargs)
            else:
                row = dict(time=time, message=msg, details=kwargs)
        else:
            if msg is None:
                row = dict(time=time, event=e, details=kwargs)
            else:
                row = dict(time=time, event=e, message=msg, details=kwargs)
        self.iter_log_list.append(row)
        row["name"] = self.name
        print(row)
        #zatim obecny parametr -predelat per RUN?
        #if LOG_RUNNER_EVENTS: insert_log(self.runner_id, time=self.time, logdict=row)