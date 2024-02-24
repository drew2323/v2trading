from v2realbot.loader.aggregator import TradeAggregator, TradeAggregator2List, TradeAggregator2Queue
#from v2realbot.loader.cacher import get_cached_agg_data
from alpaca.trading.requests import GetCalendarRequest
from alpaca.data.live import StockDataStream
from v2realbot.config import ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY, DATA_DIR, OFFLINE_MODE, LIVE_DATA_FEED
from alpaca.data.enums import DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest, StockBarsRequest, StockTradesRequest
from threading import Thread, current_thread
from v2realbot.utils.utils import parse_alpaca_timestamp, ltp, zoneNY, send_to_telegram, fetch_calendar_data
from v2realbot.utils.tlog import tlog
from datetime import datetime, timedelta, date
from threading import Thread
import asyncio
from msgpack.ext import Timestamp
from msgpack import packb
from pandas import to_datetime
import gzip
import pickle
import os
from rich import print
import queue
from alpaca.trading.models import Calendar
from tqdm import tqdm
import time
from traceback import format_exc
from collections import defaultdict
import requests
"""
    Trade offline data streamer, based on Alpaca historical data.
"""
class Trade_Offline_Streamer(Thread):
    #pro BT se pripojujeme vzdy k primarnimu uctu - pouze tahame historicka data + calendar
    client =  StockHistoricalDataClient(ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY, raw_data=True)
    #clientTrading = TradingClient(ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY, raw_data=False)
    def __init__(self, time_from: datetime, time_to: datetime, btdata) -> None:
       # Call the Thread class's init function
       Thread.__init__(self)
       self.uniquesymbols = set()
       self.streams = []
       self.to_run = dict()
       self.time_from = time_from
       self.time_to = time_to
       self.btdata = btdata
       self.cache_used = defaultdict(list)
 
    def add_stream(self, obj: TradeAggregator):
        self.streams.append(obj)

    def remove_stream(self, obj):
        pass

    def run(self):
        try:
            self.main()
        except Exception as e:
            print("ERROR IN TRADE OFFLINE STREAMER"+str(e)+format_exc())
        # #create new asyncio loop in the thread
        # loop = asyncio.new_event_loop()
        # asyncio.set_event_loop(loop)
        # loop.create_task(self.main())
        # loop.run_forever()

    def stop(self):
        pass

    def fetch_stock_trades(self, symbol, start, end, max_retries=5, backoff_factor=1):
        """
        Attempts to fetch stock trades with exponential backoff. Raises an exception if all retries fail.

        :param symbol: The stock symbol to fetch trades for.
        :param start: The start time for the trade data.
        :param end: The end time for the trade data.
        :param max_retries: Maximum number of retries.
        :param backoff_factor: Factor to determine the next sleep time.
        :return: TradesResponse object.
        :raises: ConnectionError if all retries fail.
        """
        stockTradeRequest = StockTradesRequest(symbol_or_symbols=symbol, start=start, end=end)
        last_exception = None

        for attempt in range(max_retries):
            try:
                tradesResponse = self.client.get_stock_trades(stockTradeRequest)
                print("Remote Fetch DAY DATA Complete", start, end)
                return tradesResponse
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                last_exception = e
                time.sleep(backoff_factor * (2 ** attempt))

        print("All attempts to fetch data failed.")
        send_to_telegram(f"Failed to fetch stock trades after {max_retries} retries. Last exception: {str(last_exception)} and {format_exc()}")
        raise ConnectionError(f"Failed to fetch stock trades after {max_retries} retries. Last exception: {str(last_exception)} and {format_exc()}")

   # Override the run() function of Thread class
   #odebrano async
    def main(self):
        trade_queue = queue.Queue()
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

        #datetime.fromtimestamp(data['updated']).astimezone(zoneNY))
        #REFACTOR STARTS HERE
        #print(f"{self.time_from=} {self.time_to=}")
              
        if OFFLINE_MODE:
            #just one day - same like time_from
            den = str(self.time_to.date())
            bt_day = Calendar(date=den,open="9:30",close="16:00")
            cal_dates = [bt_day]
        else:
            start_date = self.time_from  # Assuming this is your start date
            end_date = self.time_to  # Assuming this is your end date
            cal_dates = fetch_calendar_data(start_date, end_date)

            #zatim podpora pouze main session
        
        #zatim podpora pouze 1 symbolu, predelat na froloop vsech symbolu ze symbpole
        #minimalni jednotka pro CACHE je 1 den - a to jen marketopen to marketclose (extended hours not supported yet)
        for day in cal_dates:
            print("Processing DAY", day.date)
            #print(day.date)
            print(day.open)
            print(day.close)
            #make it offset aware
            day.open = zoneNY.localize(day.open)
            #day.open.replace(tzinfo=zoneNY)
            #add 20 minutes of premarket
            #day.open = day.open - timedelta(minutes=20)
            day.close = zoneNY.localize(day.close)
            #day.close = day.close.replace(tzinfo=zoneNY)
            #print(day.open)
            #print(day.close)  
            #print("dayopentimestamp", day.open.timestamp())      
            #print("dayclosetimestamp", day.close.timestamp())     
            ##pokud datum do je mensi day.open, tak tento den neresime
            if self.time_to < day.open:
                print("time_to je pred zacatkem marketu. Vynechavame tento den.")
                continue

            if datetime.now().astimezone(zoneNY) < day.open:
                print("Tento den je v budoucnu. Vynechavame tento den.")
                continue                

            
            #check if we have  data in aggregator cache - for all streams
            #zatim jednoduse
            # predpokladame ze [0] jsou btdata a [1] hlavni add_data
            # - pokud jsou oba, jedeme z cache ,pokud jeden nebo zadny - jedeme trady
            # - cache pokryva cely den

            #musim zajistit, ze BT data tam jdou drive nez cache
            # to_rem = []
            # for stream in self.to_run[symbpole[0]]:
            #     cache = stream.get_cache(day.open, day.close)
            #     if cache is not None:
            #         stream.send_cache_to_output(cache)
            #         to_rem.append(stream)

            #cache resime jen kdyz backtestujeme cely den a mame sip datapoint (iex necachujeme)
            #pokud ne tak ani necteme, ani nezapisujeme do cache

            if (self.time_to >= day.close and self.time_from <= day.open) and LIVE_DATA_FEED == DataFeed.SIP:
                #tento odstavec obchazime pokud je nastaveno "dont_use_cache"
                stream_btdata = self.to_run[symbpole[0]][0]
                cache_btdata, file_btdata = stream_btdata.get_cache(day.open, day.close)
                stream_main = self.to_run[symbpole[0]][1]
                cache_main, file_main = stream_main.get_cache(day.open, day.close)
                if cache_btdata is not None and cache_main is not None:
                    stream_btdata.send_cache_to_output(cache_btdata)
                    stream_main.send_cache_to_output(cache_main)
                    #ukladame nazvy souboru pro pozdejsi ulozeni ke strategii
                    self.cache_used[str(day.date)].append(file_btdata)
                    self.cache_used[str(day.date)].append(file_main)
                    continue

                #TBD pokud se jede na cache a testovaci obdobi je mensi nez den
                #    - bud disablujeme cashovani
                #    - nebo nechavame dobehnout cely den

                #pokud cache neexistuje, pak ji zapiname
                if day.open < datetime.now().astimezone(zoneNY) < day.close:
                    print("not saving the aggregating cache, market still open today")
                else:
                    if cache_btdata is None:
                        stream_btdata.enable_cache_output(day.open, day.close)
                    if cache_main is None:
                        stream_main.enable_cache_output(day.open, day.close)

            #trade daily file
            daily_file = str(symbpole[0]) + '-' + str(int(day.open.timestamp())) + '-' + str(int(day.close.timestamp())) + '.cache.gz'
            print(daily_file)
            file_path = DATA_DIR + "/tradecache/"+daily_file
        
            if os.path.exists(file_path):
                ##denní file existuje
                #loadujeme ze souboru
                #pokud je start_time < trade < end_time 
                    #odesíláme do queue
                    #jinak pass
                with gzip.open (file_path, 'rb') as fp:
                    tradesResponse = pickle.load(fp)
                    print("Loading from Trade CACHE", file_path)
            #daily file doesnt exist
            else:

                #implement retry mechanism
                symbol = symbpole[0]  # Assuming symbpole[0] is your target symbol
                day_open = day.open  # Assuming day.open is the start time
                day_close = day.close  # Assuming day.close is the end time

                tradesResponse = self.fetch_stock_trades(symbol, day_open, day_close)

                # # TODO refactor pro zpracovani vice symbolu najednou(multithreads), nyni predpokladame pouze 1 
                # stockTradeRequest = StockTradesRequest(symbol_or_symbols=symbpole[0], start=day.open,end=day.close)
                # tradesResponse = self.client.get_stock_trades(stockTradeRequest)
                print("Remote Fetch DAY DATA Complete", day.open, day.close)

                #pokud jde o dnešní den a nebyl konec trhu tak cache neukládáme, pripadne pri iex datapointu necachujeme
                if (day.open < datetime.now().astimezone(zoneNY) < day.close) or LIVE_DATA_FEED == DataFeed.IEX:
                    print("not saving trade cache, market still open today or IEX datapoint")
                    #ic(datetime.now().astimezone(zoneNY))
                    #ic(day.open, day.close)
                else:
                    with gzip.open(file_path, 'wb') as fp:
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
                
                
                for t in tqdm(tradesResponse[symbol], desc="Loading Trades"):
                    
                    #protoze je zde cely den, poustime dal, jen ty relevantni
                    #pokud je    start_time < trade < end_time
                    #datetime.fromtimestamp(parse_alpaca_timestamp(t['t']))
                    ##ic(t['t'])

                    #poustime i 20 minut premarketu pro presnejsi populaci slopu v prvnich minutech
                    # - timedelta(minutes=20)
                    #homogenizace timestampu s online streamem
                    #tmp = to_datetime(t['t'], utc=True).timestamp()
                    

                    #obcas se v response objevoval None radek
                    if t is None:
                        continue

                    datum = to_datetime(t['t'], utc=True)

                    if self.time_from < datum < self.time_to:
                        #poustime dal, jinak ne
                        if wait_for_q:
                            #cekame na Q nebo na O (nekterym dnum chybelo Q)
                            if ('Q' not in t['c']) and ('O' not in t['c']): continue
                            else:
                                #ic("Q found poustime dal")
                                wait_for_q = False
                        
                        #homogenizace timestampu s online streamem
                        t['t'] = Timestamp.from_unix(datum.timestamp())
                        #print(f"{t['t']}")
                        #t['t'] = Timestamp.from_unix(to_datetime(t['t']).timestamp())
                        #print(to_datetime(t['t']).timestamp())
                        
                        #print("PROGRESS ",cnt,"/",celkem)
                        #print(t)
                        #na rozdil od wwebsocketu zde nemame v zaznamu symbol ['S']
                        #vsem streamum na tomto symbolu posilame data - tbd mozna udelat i per stream vlakno
                        for s in self.to_run[symbol]:
                            #print("zaznam",t)
                            #print("Ingest", s, "zaznam", t)
                            #await s.ingest_trade(packb(t))
                            trade_queue.put((s,t))

                            ##asyncio.run(s.ingest_trade(packb(t)))
                        cnt += 1
                    #protoze jsou serazene, tak prvni ktery je vetsi muze prerusit
                    elif datum > self.time_to:
                        #print(f"{datum=}")
                        #print(to_datetime(t['t']))
                        #print(f"{self.time_to=}")
                        #print("prerusujeme")
                        break
        #vsem streamum posleme last TODO: (tuto celou cast prepsat a zjednodusit)
        #po loadovani vsech dnu
        print("naloadovane vse posilame last")
        for s in self.to_run[symbpole[0]]:
            #zde bylo await
            trade_queue.put((s,"last"))
            ##asyncio.run(s.ingest_trade(packb("last")))
            print("poslano last")

        async def process_trade_queue(trade_queue):
            while not trade_queue.empty():
                #print("send trade")
                s, trade = trade_queue.get()
                await s.ingest_trade(packb(trade))

        #spusteni asyncio run - tentokrat jednou, ktera spusti proces jez to z queue odesle
        #nevyhoda reseni - kdyz je to pres vice dnu, tak se naloaduji vsechny dny do queue
        #ale to mi u Classic zatim nevadi - poustim per days
        #uvidim jak to ovlivn rychlost
        asyncio.run(process_trade_queue(trade_queue))
        print("skoncilo zpracovani ASYNCIO RUN TRADE QUEUE - zpracovany vsechny trady v agreagtorech")
        print(10*"*","Trade OFFLINE streamer STOPPED", current_thread().name,10*"*")


