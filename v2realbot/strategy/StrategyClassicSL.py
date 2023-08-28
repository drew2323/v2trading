from v2realbot.strategy.base import Strategy
from v2realbot.utils.utils import parse_alpaca_timestamp, ltp, AttributeDict,trunc,price2dec, zoneNY, print, json_serial, safe_get, get_tick
from v2realbot.utils.tlog import tlog, tlog_exception
from v2realbot.enums.enums import Mode, Order, Account, RecordType
#from alpaca.trading.models import TradeUpdate
from  v2realbot.common.model import TradeUpdate
from alpaca.trading.enums import TradeEvent, OrderStatus
from v2realbot.indicators.indicators import ema
import json
from datetime import datetime
#from rich import print
from random import randrange
from alpaca.common.exceptions import APIError
import copy
from threading import Event
from uuid import UUID


class StrategyClassicSL(Strategy):
    """
    Base override file for Classic Stop-Loss startegy
    """
    def __init__(self, name: str, symbol: str, next: callable, init: callable, account: Account, mode: Mode = Mode.PAPER, stratvars: AttributeDict = None, open_rush: int = 30, close_rush: int = 30, pe: Event = None, se: Event = None, runner_id: UUID = None, ilog_save: bool = False) -> None:
        super().__init__(name, symbol, next, init, account, mode, stratvars, open_rush, close_rush, pe, se, runner_id, ilog_save)

    #todo dodelat profit, podle toho jestli jde o short nebo buy

    async def orderUpdateBuy(self, data: TradeUpdate):
        o: Order = data.order
        ##nejak to vymyslet, aby se dal poslat cely Trade a serializoval se
        self.state.ilog(e="Příchozí BUY notif", msg=o.status, trade=json.loads(json.dumps(data, default=json_serial)))


        if data.event == TradeEvent.FILL or data.event == TradeEvent.PARTIAL_FILL:

            #jde o uzavření short pozice - počítáme PROFIT
            if int(self.state.positions) < 0:
                #PROFIT pocitame z TradeUpdate.price a TradeUpdate.qty - aktualne provedene mnozstvi a cena
                #naklady vypocteme z prumerne ceny, kterou mame v pozicich
                bought_amount = data.qty * data.price
                #podle prumerne ceny, kolik stalo toto mnozstvi
                avg_costs = float(self.state.avgp) * float(data.qty)
                if avg_costs == 0:
                    self.state.ilog(e="ERR: Nemame naklady na PROFIT, AVGP je nula. Zaznamenano jako 0", msg="naklady=utrzena cena. TBD opravit.")
                    avg_costs = bought_amount
                
                trade_profit = round((avg_costs-bought_amount),2)
                self.state.profit += trade_profit
                self.state.ilog(e=f"BUY notif - SHORT PROFIT:{round(float(trade_profit),3)} celkem:{round(float(self.state.profit),3)}", msg=str(data.event), bought_amount=bought_amount, avg_costs=avg_costs, trade_qty=data.qty, trade_price=data.price, orderid=str(data.order.id))
            
                #zapsat profit do prescr.trades
                for trade in self.state.vars.prescribedTrades:
                    if trade.id == self.state.vars.pending:
                        trade.last_update = datetime.fromtimestamp(self.state.time).astimezone(zoneNY)
                        trade.profit += trade_profit
                        trade.profit_sum = self.state.profit

                #zapsat update profitu do tradeList
                for tradeData in self.state.tradeList:
                    if tradeData.execution_id == data.execution_id:
                        #pridat jako attribut, aby proslo i na LIVE a PAPPER, kde se bere TradeUpdate z Alpaca
                        setattr(tradeData, "profit", trade_profit)
                        setattr(tradeData, "profit_sum", self.state.profit)
                        self.state.ilog(f"updatnut tradeList o profi {str(tradeData)}")
            
            else:
                self.state.ilog(e="BUY: Jde o LONG nakuú nepocitame profit zatim")

            #ic("vstupujeme do orderupdatebuy")
            print(data)
            #dostavame zde i celkové akutální množství - ukládáme
            self.state.positions = data.position_qty
            self.state.avgp, self.state.positions = self.state.interface.pos()

        if o.status == OrderStatus.FILLED or o.status == OrderStatus.CANCELED:
            #davame pryc pending
            self.state.vars.pending = None

    async def orderUpdateSell(self, data: TradeUpdate): 

        self.state.ilog(e="Příchozí SELL notif", msg=data.order.status, trade=json.loads(json.dumps(data, default=json_serial)))
        #naklady vypocteme z prumerne ceny, kterou mame v pozicich
        if data.event == TradeEvent.FILL or data.event == TradeEvent.PARTIAL_FILL:            
            #jde o uzavření long pozice - počítáme PROFIT
            if int(self.state.positions) > 0:
                #PROFIT pocitame z TradeUpdate.price a TradeUpdate.qty - aktualne provedene mnozstvi a cena
                #naklady vypocteme z prumerne ceny, kterou mame v pozicich
                sold_amount = data.qty * data.price
                #podle prumerne ceny, kolik stalo toto mnozstvi
                avg_costs = float(self.state.avgp) * float(data.qty)
                if avg_costs == 0:
                    self.state.ilog(e="ERR: Nemame naklady na PROFIT, AVGP je nula. Zaznamenano jako 0", msg="naklady=utrzena cena. TBD opravit.")
                    avg_costs = sold_amount
                
                trade_profit = round((sold_amount - avg_costs),2)
                self.state.profit += trade_profit
                self.state.ilog(e=f"SELL notif - PROFIT:{round(float(trade_profit),3)} celkem:{round(float(self.state.profit),3)}", msg=str(data.event), sold_amount=sold_amount, avg_costs=avg_costs, trade_qty=data.qty, trade_price=data.price, orderid=str(data.order.id))

                #zapsat profit do prescr.trades
                for trade in self.state.vars.prescribedTrades:
                    if trade.id == self.state.vars.pending:
                        trade.last_update = datetime.fromtimestamp(self.state.time).astimezone(zoneNY)
                        trade.profit += trade_profit
                        trade.profit_sum = self.state.profit

                #zapsat update profitu do tradeList
                for tradeData in self.state.tradeList:
                    if tradeData.execution_id == data.execution_id:
                        #pridat jako attribut, aby proslo i na LIVE a PAPPER, kde se bere TradeUpdate z Alpaca
                        setattr(tradeData, "profit", trade_profit)
                        setattr(tradeData, "profit_sum", self.state.profit)
                        self.state.ilog(f"updatnut tradeList o profi {str(tradeData)}")

            else:
                self.state.ilog(e="SELL: Jde o SHORT nepocitame profit zatim")

            #update pozic, v trade update je i pocet zbylych pozic
            old_avgp = self.state.avgp
            old_pos = self.state.positions
            self.state.positions = int(data.position_qty)
            if int(data.position_qty) == 0:
                self.state.avgp = 0

            self.state.ilog(e="SELL notifikace "+str(data.order.status), msg="update pozic", old_avgp=old_avgp, old_pos=old_pos, avgp=self.state.avgp, pos=self.state.positions, orderid=str(data.order.id))
            #self.state.avgp, self.state.positions = self.interface.pos()

        if data.event == TradeEvent.FILL or data.event == TradeEvent.CANCELED:
            print("Příchozí SELL notifikace - complete FILL nebo CANCEL", data.event)
            self.state.vars.pending = None
            a,p = self.interface.pos()
            #pri chybe api nechavame puvodni hodnoty
            if a != -1:
                self.state.avgp, self.state.positions = a,p
            #ic(self.state.avgp, self.state.positions)

    #this parent method is called by strategy just once before waiting for first data
    def strat_init(self):
        #ic("strat INI function")
        #lets connect method overrides
        self.state.buy = self.buy
        self.state.sell = self.sell

    #overidden methods
    # pouziva se pri vstupu long nebo exitu short
    # osetrit uzavreni s vice nez mam
    def buy(self, size = None, repeat: bool = False):
        print("overriden buy method")
        if size is None:
            sizer = self.state.vars.chunk
        else:
            sizer = size
        #jde o uzavreni short pozice
        if int(self.state.positions) < 0 and (int(self.state.positions) + sizer) > 0:
            self.state.ilog(e="buy nelze nakoupit vic nez shortuji", positions=self.state.positions, size=size)
            print("buy nelze nakoupit vic nez shortuji") 
            return -2

        if int(self.state.positions) >= self.state.vars.maxpozic:
            self.state.ilog(e="buy Maxim mnozstvi naplneno", positions=self.state.positions)
            print("max mnostvi naplneno")
            return 0

        self.state.blockbuy = 1
        self.state.vars.lastbuyindex = self.state.bars['index'][-1]
        self.state.ilog(e="send MARKET buy to if", msg="S:"+str(size), ltp=self.state.interface.get_last_price(self.state.symbol))
        return self.state.interface.buy(size=sizer)

    #overidden methods
    # pouziva se pri vstupu short nebo exitu long
    def sell(self, size = None, repeat: bool = False):
        print("overriden sell method")
        if size is None:
            size = abs(int(self.state.positions))

        #jde o uzavreni long pozice
        if int(self.state.positions) > 0 and (int(self.state.positions) - size) < 0:
            self.state.ilog(e="nelze prodat vic nez longuji", positions=self.state.positions, size=size)
            print("nelze prodat vic nez longuji") 
            return -2

        #pokud shortuji a mam max pozic
        if int(self.state.positions) < 0 and abs(int(self.state.positions)) >= self.state.vars.maxpozic:
            self.state.ilog(e="short - Maxim mnozstvi naplneno", positions=self.state.positions, size=size)
            print("max mnostvi naplneno")
            return 0

        #self.state.blocksell = 1
        #self.state.vars.lastbuyindex = self.state.bars['index'][-1]
        self.state.ilog(e="send MARKET SELL to if", msg="S:"+str(size), ltp=self.state.interface.get_last_price(self.state.symbol))
        return self.state.interface.sell(size=size)

    async def get_limitka_price(self):
        def_profit = safe_get(self.state.vars, "def_profit") 
        if def_profit == None: def_profit = self.state.vars.profit
        cena = float(self.state.avgp)
        if await self.is_defensive_mode():
            return price2dec(cena+get_tick(cena,float(def_profit)))
        else:
            return price2dec(cena+get_tick(cena,float(self.state.vars.profit)))