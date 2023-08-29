from v2realbot.loader.aggregator import TradeAggregator, TradeAggregator2List, TradeAggregator2Queue
from alpaca.trading.requests import GetCalendarRequest
from alpaca.trading.client import TradingClient
from alpaca.data.live import StockDataStream
from v2realbot.config import ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY, DATA_DIR
from alpaca.data.enums import DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest, StockBarsRequest, StockTradesRequest
from threading import Thread, current_thread
from v2realbot.utils.utils import parse_alpaca_timestamp, ltp, zoneNY, print
from v2realbot.utils.tlog import tlog
from datetime import datetime, timedelta
from threading import Thread
import asyncio
from msgpack.ext import Timestamp
from msgpack import packb
from pandas import to_datetime
import pickle
import os

"""
    Trade offline data streamer, based on Alpaca historical data.
"""
class Trade_Offline_Streamer(Thread):
    #pro BT se pripojujeme vzdy k primarnimu uctu - pouze tahame historicka data + calendar
    client =  StockHistoricalDataClient(ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY, raw_data=True)
    clientTrading = TradingClient(ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY, raw_data=False)
    def __init__(self, time_from: datetime, time_to: datetime, btdata) -> None:
       # Call the Thread class's init function
       Thread.__init__(self)
       self.uniquesymbols = set()
       self.streams = []
       self.to_run = dict()
       self.time_from = time_from
       self.time_to = time_to
       self.btdata = btdata
 
    def add_stream(self, obj: TradeAggregator):
        self.streams.append(obj)

    def remove_stream(self, obj):
        pass

    def run(self):
        self.main()
        # #create new asyncio loop in the thread
        # loop = asyncio.new_event_loop()
        # asyncio.set_event_loop(loop)
        # loop.create_task(self.main())
        # loop.run_forever()

    def stop(self):
        pass

   # Override the run() function of Thread class
   #odebrano async
    def main(self):
        print(10*"*","Trade OFFLINE streamer STARTED", current_thread().name,10*"*")
        
        if not self.streams:
            print("call add streams to queue first")
            return 0
        
        #iterujeme nad streamy
        for i in self.streams:
            self.uniquesymbols.add(i.symbol)

        #ic(self.uniquesymbols)
        ##z unikatnich symbolu naplnime keys pro dictionary
        # for i in self.uniquesymbols:
        #     self.to_run

        #vytvorime prazdne dict oklicovane unik.symboly a obsahujici prazdne pole
        self.to_run = {key: [] for key in self.uniquesymbols}
        #stejne tak pro glob.tridu last price
        ltp.price = {key: 0 for key in self.uniquesymbols}
        #pro kazdy symbol do toho pole ulozime instance na spusteni
        print(self.to_run)
        for i in self.streams:
            self.to_run[i.symbol].append(i)
        
        #ic(self.to_run)
        #prepare data
        symbpole = []
        for key in self.uniquesymbols:
            symbpole.append(key)
        #print(symbpole))
        #ic(self.time_from.astimezone(tz=zoneNY))
        #ic(self.time_to.astimezone(tz=zoneNY))

        ##PREPSAT jednoduse tak, aby podporovalo jen jeden symbol
        #agregator2list bude mit vstup list

        #REFACTOR STARTS HERE
        calendar_request = GetCalendarRequest(start=self.time_from,end=self.time_to)
        cal_dates = self.clientTrading.get_calendar(calendar_request)
        #ic(cal_dates)
        #zatim podpora pouze main session

        #zatim podpora pouze 1 symbolu, predelat na froloop vsech symbolu ze symbpole
        #minimalni jednotka pro CACHE je 1 den - a to jen marketopen to marketclose (extended hours not supported yet)
        for day in cal_dates:
            print("Processing DAY", day.date)
            print(day.date)
            print(day.open)
            print(day.close)
            #make it offset aware
            day.open = day.open.replace(tzinfo=zoneNY)
            #add 20 minutes of premarket
            #day.open = day.open - timedelta(minutes=20)
            day.close = day.close.replace(tzinfo=zoneNY)
                                     
            ##pokud datum do je mensi day.open, tak tento den neresime
            if self.time_to < day.open:
                print("time_to je pred zacatkem marketu. Vynechavame tento den.")
                continue

            daily_file = str(symbpole[0]) + '-' + str(int(day.open.timestamp())) + '-' + str(int(day.close.timestamp())) + '.cache'
            print(daily_file)
            file_path = DATA_DIR + "/"+daily_file
        
            if os.path.exists(file_path):
                ##denní file existuje
                #loadujeme ze souboru
                #pokud je start_time < trade < end_time 
                    #odesíláme do queue
                    #jinak pass
                with open (file_path, 'rb') as fp:
                    tradesResponse = pickle.load(fp)
                    print("Loading DATA from CACHE", file_path)
            #daily file doesnt exist
            else:
                # TODO refactor pro zpracovani vice symbolu najednou(multithreads), nyni predpokladame pouze 1 
                stockTradeRequest = StockTradesRequest(symbol_or_symbols=symbpole[0], start=day.open,end=day.close)
                tradesResponse = self.client.get_stock_trades(stockTradeRequest)
                print("Remote Fetch DAY DATA Complete", day.open, day.close)

                #pokud jde o dnešní den a nebyl konec trhu tak cache neukládáme
                if day.open < datetime.now().astimezone(zoneNY) < day.close:
                    print("not saving the cache, market still open today")
                    #ic(datetime.now().astimezone(zoneNY))
                    #ic(day.open, day.close)
                else:
                    with open(file_path, 'wb') as fp:
                        pickle.dump(tradesResponse, fp)

            #zde už máme daily data
            #pokud je    start_time < trade < end_time
            #odesíláme do queue
            #jinak ne

            #TODO pokud data zahrnuji open (tzn. bud cely den(jednotest nebo v ramci vice dni) a nebo jednotest se zacatkem v 9:30 nebo driv.

            #- pockame na trade Q a od nej budeme pocitat
            #    abychom meli zarovnano s tradingview
            #- zaroven pak cekame na M(market close) a od nej uz take nic dál nepoustime (NOT IMPLEMENTED YET)

            #protze mi chodi data jen v main sessione, pak jediné, kdy nečekáme na Q, je když time_from je větší než day.open
            # (např. požadovaná start až od 10:00)

            #docasne disablujeme wait for queue, aby nam mohl jit i premarket
            if self.time_from > day.open: # or 1==1:
                wait_for_q = False
            else:
                wait_for_q = True
            print(f"{wait_for_q=}")

        # v tradesResponse je dict = Trades identifikovane symbolem
            for symbol in tradesResponse:
                #print(tradesResponse[symbol])
                celkem = len(tradesResponse[symbol])
                
                #ic(symbol, celkem)
                print("POCET: ", celkem)
                cnt = 1
                
                
                for t in tradesResponse[symbol]:
                    
                    #protoze je zde cely den, poustime dal, jen ty relevantni
                    #pokud je    start_time < trade < end_time
                    #datetime.fromtimestamp(parse_alpaca_timestamp(t['t']))
                    ##ic(t['t'])

                    #poustime i 20 minut premarketu pro presnejsi populaci slopu v prvnich minutech
                    # - timedelta(minutes=20)
                    if self.time_from < to_datetime(t['t']) < self.time_to:
                        #poustime dal, jinak ne
                        if wait_for_q:
                            #cekame na Q nebo na O (nekterym dnum chybelo Q)
                            if ('Q' not in t['c']) and ('O' not in t['c']): continue
                            else:
                                #ic("Q found poustime dal")
                                wait_for_q = False
                        
                        #homogenizace timestampu s online streamem
                        t['t'] = Timestamp.from_unix(to_datetime(t['t']).timestamp())
                        
                        print("PROGRESS ",cnt,"/",celkem)
                        #print(t)
                        #na rozdil od wwebsocketu zde nemame v zaznamu symbol ['S']
                        #vsem streamum na tomto symbolu posilame data - tbd mozna udelat i per stream vlakno
                        for s in self.to_run[symbol]:
                            #print("zaznam",t)
                            #print("Ingest", s, "zaznam", t)
                            #await s.ingest_trade(packb(t))
                            asyncio.run(s.ingest_trade(packb(t)))
                        cnt += 1
                    #protoze jsou serazene, tak prvni ktery je vetsi muze prerusit
                    elif to_datetime(t['t']) > self.time_to:
                        print("prerusujeme")
                        break
        #vsem streamum posleme last TODO: (tuto celou cast prepsat a zjednodusit)
        #po loadovani vsech dnu
        print("naloadovane vse posilame last")
        for s in self.to_run[symbpole[0]]:
            #zde bylo await
            asyncio.run(s.ingest_trade(packb("last")))
            print("poslano last")

        #loop = asyncio.get_running_loop()
        print("stoping loop")
        #loop.stop()
        print(10*"*","Trade OFFLINE streamer STOPPED", current_thread().name,10*"*")


