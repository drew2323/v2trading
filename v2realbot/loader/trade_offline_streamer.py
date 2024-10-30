
# TADY JSEM SKONCIL
##moved loader and vectorized aggregator out to ttools, so ite can be shaerd
#continue with the steps and include ttools, make sure that DIRS are aligned
#file moved to todel dir

from v2realbot.loader.aggregator import TradeAggregator
from ttools.loaders import fetch_daily_stock_trades
from alpaca.data.enums import DataFeed
from threading import Thread, current_thread
from v2realbot.utils.utils import fetch_calendar_data, ltp, zoneNY
from datetime import datetime
from threading import Thread
import asyncio
from msgpack.ext import Timestamp
from msgpack import packb
import numpy as np
from rich import print
import queue
from alpaca.trading.models import Calendar
from tqdm import tqdm
from traceback import format_exc
from collections import defaultdict
import v2realbot.utils.config_handler as cfh
"""
    Trade offline data streamer, based on Alpaca historical data.
"""
class Trade_Offline_Streamer(Thread):
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
       self.main_session_only = True
 
    def add_stream(self, obj: TradeAggregator):

        #WORKAROUND - exthours on each add_data creates main_session_only attribute
        #if any of stream has ext_hours True, it populates global params
        # and apply to all streams
        if obj.exthours != (not self.main_session_only):
            self.main_session_only = not obj.exthours

        #when new stream is added with exthours update it on all existing streams - TODO add as instance parameter
        for stream in self.streams:
            stream.exthours = obj.exthours

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

   # Override the run() function of Thread class
   #odebrano async
    def main(self):
        trade_queue = queue.Queue()
        print(10*"*","Trade OFFLINE streamer STARTED", current_thread().name,10*"*")
        
        if not self.streams:
            print("call add streams to queue first")
            return 0
        
        cfh.config_handler.print_current_config()

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


        #na GUI no_cache
        #na uroven strategie typ behu - bud day by day(N runners) nebo continuous

        #REFACTOR STARTS HERE
        #print(f"{self.time_from=} {self.time_to=}")
 
        if cfh.config_handler.get_val('OFFLINE_MODE'):
            #just one day - same like time_from
            den = str(self.time_to.date())
            bt_day = Calendar(date=den,open="9:30",close="16:00")
            cal_dates = [bt_day]
        else:
            start_date = self.time_from  # Assuming this is your start date
            end_date = self.time_to  # Assuming this is your end date
            cal_dates = fetch_calendar_data(start_date, end_date)

        #zatim podpora pouze main session
        
        live_data_feed = cfh.config_handler.get_val('LIVE_DATA_FEED')

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
            if self.time_to < day.open: #issue #260 adapt to extended horus when needed
                print("time_to je pred zacatkem marketu. Vynechavame tento den.")
                continue

            if datetime.now().astimezone(zoneNY) < day.open:
                print("Tento den je v budoucnu. Vynechavame tento den.")
                continue                

            #main_session_only = False #TODO issue #260 currently strat wide
            force_remote = False #bring to frontend issue #258
            exthours = not self.main_session_only

            #RESOLVE daily times
            day_date = day.open.date()
            min_day_time = zoneNY.localize(datetime.combine(day_date, datetime.min.time()))
            max_day_time = zoneNY.localize(datetime.combine(day_date, datetime.max.time()))          

            #cut first day to time_from and last day to time_to
            start = max(self.time_from, min_day_time)
            end = min(self.time_to, max_day_time)

            #AGG daily CACHE HERE (from-to period enters cache)
            #we cache daily cache files, including partial days - identified by exact time from - to
            #we assume single add_data here
            symbol = symbpole[0]  # Assuming symbpole[0] is your target symbol
            #AGG CACHE zatim neupravujeme, zde je zatim zapiklovany MAIN SESSION a dany objekt
            #TODO v budoucnu predelat, na daily, parquet a reuse i pro vbt, jako tradecache
            if live_data_feed == DataFeed.SIP :
                #tento odstavec obchazime pokud je nastaveno "dont_use_cache"
                stream_btdata = self.to_run[symbol][0]
                cache_btdata = None
                cache_main = None
                if force_remote is False:
                    cache_btdata, file_btdata = stream_btdata.get_cache(start, end, exthours)
                    stream_main = self.to_run[symbol][1]
                    cache_main, file_main = stream_main.get_cache(start, end, exthours)
                    if cache_btdata is not None and cache_main is not None:
                        stream_btdata.send_cache_to_output(cache_btdata)
                        stream_main.send_cache_to_output(cache_main)
                        #ukladame nazvy souboru pro pozdejsi ulozeni ke strategii
                        self.cache_used[str(day.date)].append(str(file_btdata))
                        self.cache_used[str(day.date)].append(str(file_main))
                        continue

                #IF CACHE NOT FOUND, THEN ENABLE CACHING (except for todays records)
                if min_day_time< datetime.now().astimezone(zoneNY) < max_day_time:
                    print("not saving the aggregating cache, market still open today")
                else:
                    if cache_btdata is None:
                        stream_btdata.enable_cache_output(start, end, exthours) #AGG CACHE on main data now only
                    if cache_main is None:
                        stream_main.enable_cache_output(start, end, exthours)

            df = fetch_daily_stock_trades(symbol=symbol,
                                          start=start,
                                          end=end,
                                          main_session_only=self.main_session_only, #currently only main session supported
                                          no_return=False,
                                          force_remote=force_remote, # issue #258 
                                          rename_labels=False,
                                          keep_symbols=False,
                                          data_feed=live_data_feed)

            #- pockame na trade Q a od nej budeme pocitat
            #    abychom meli zarovnano s tradingview
            #- zaroven pak cekame na M(market close) a od nej uz take nic dál nepoustime (NOT IMPLEMENTED YET)

            #protze mi chodi data jen v main sessione, pak jediné, kdy nečekáme na Q, je když time_from je větší než day.open
            # (např. požadovaná start až od 10:00)

            #docasne disablujeme wait for queue, aby nam mohl jit i premarket
            if self.time_from > day.open or self.main_session_only is False: # or 1==1:
                wait_for_q = False
            else:
                wait_for_q = True
            print(f"{wait_for_q=}")
        
            if wait_for_q:
                # Identify the first market open row containing "Q" or "O" in the "c" list
                market_open_index = df[df['c'].apply(lambda x: 'Q' in x or 'O' in x)].index.min()

                if market_open_index is not None:
                    # Remove all rows before market open
                    df = df.loc[market_open_index:].copy()

            df.reset_index(inplace=True)

            #from numpy to list
            df["c"] = df["c"].apply(lambda x: x.tolist() if isinstance(x, np.ndarray) else x)

            #TODO ZRYCHLIT
            # Put each row into the queue in the format (symbol, row) with "t" as Unix timestamp
            for row in tqdm(df.itertuples(index=False, name='Row'), desc="Loading rows"):
                row_dict = row._asdict()
                # Convert the index 't' to a Unix timestamp using Pandas' timestamp() method
                #row_dict['t'] = row.Index.timestamp()
                #same as in live input
                #row_dict['t'] = Timestamp.from_unix(row.Index.timestamp())
                row_dict["t"] = Timestamp.from_unix(row_dict["t"].timestamp())
                #Optimized this
                #send the data, to all streams of this symbol
                for s in self.to_run[symbol]:
                    trade_queue.put((s, row_dict))

        print("naloadovane vse posilame last")
        for s in self.to_run[symbol]:
            #zde bylo await
            trade_queue.put((s,"last"))
            ##asyncio.run(s.ingest_trade(packb("last")))
            print("poslano last")

        async def process_trade_queue(trade_queue):
            while not trade_queue.empty():
                #print("send trade")
                s, trade = trade_queue.get()
                await s.ingest_trade(packb(trade))

        #TADY pouzit vectorize loader
        #nejspis do issue, na parametr pouzit bud standardni(pomaly a nebo vektorovy)

        #spusteni asyncio run - tentokrat jednou, ktera spusti proces jez to z queue odesle
        #nevyhoda reseni - kdyz je to pres vice dnu, tak se naloaduji vsechny dny do queue
        #ale to mi u Classic zatim nevadi - poustim per days
        #uvidim jak to ovlivn rychlost
        asyncio.run(process_trade_queue(trade_queue))
        print("skoncilo zpracovani ASYNCIO RUN TRADE QUEUE - zpracovany vsechny trady v agreagtorech")
        print(10*"*","Trade OFFLINE streamer STOPPED", current_thread().name,10*"*")


