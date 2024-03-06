"""
    Classes for streamers (websocket and offline)
    currently only streams are Trades
"""
from v2realbot.loader.aggregator import TradeAggregator2Queue
from alpaca.data.live import StockDataStream
from v2realbot.config import LIVE_DATA_API_KEY, LIVE_DATA_SECRET_KEY
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest, StockBarsRequest, StockTradesRequest
from threading import Thread, current_thread
from v2realbot.utils.utils import parse_alpaca_timestamp, ltp
from datetime import datetime, timedelta
from threading import Thread, Lock
from msgpack import packb
import v2realbot.utils.config_handler as cfh

"""
    Shared streamer (can be shared amongst concurrently running strategies)
    Connects to alpaca websocket client and subscribe for trades on symbols requested
    by strategies
"""
class Trade_WS_Streamer(Thread):
    live_data_feed = cfh.config_handler.get_val('LIVE_DATA_FEED')
    ##tento ws streamer je pouze jeden pro vsechny, tzn. vyuziváme natvrdo placena data primarniho uctu (nezalezi jestli paper nebo live)
    msg = f"Realtime Websocket connection will use FEED: {live_data_feed} and credential of ACCOUNT1"
    print(msg)
    #cfh.config_handler.print_current_config()
    client = StockDataStream(LIVE_DATA_API_KEY, LIVE_DATA_SECRET_KEY, raw_data=True, websocket_params={}, feed=live_data_feed)
    #uniquesymbols = set()
    _streams = []
    #to_run = dict()
    #lock = Lock()

    def __init__(self, name: str) -> None:
       # Call the Thread class's init function
       Thread.__init__(self, name=name)

    def symbol_exists(self, symbol):
        for i in Trade_WS_Streamer._streams:
           if i.symbol == symbol:
               return True
        return False

    def add_stream(self, obj: TradeAggregator2Queue):
        print(Trade_WS_Streamer.msg)
        print("stav pred pridavanim", Trade_WS_Streamer._streams)
        Trade_WS_Streamer._streams.append(obj)
        if Trade_WS_Streamer.client._running is False:
            print("websocket zatim nebezi, pouze pridavame do pole")

            #zde delame refresh clienta (pokud se zmenilo live_data_feed)

            # live_data_feed = cfh.config_handler.get_val('LIVE_DATA_FEED')
            # #po otestování přepnout jen pokud se live_data_feed změnil
            # #if live_data_feed != Trade_WS_Streamer.live_data_feed:
            # #    Trade_WS_Streamer.live_data_feed = live_data_feed
            # msg = f"REFRESH OF CLIENT! Realtime Websocket connection will use FEED: {live_data_feed} and credential of ACCOUNT1"
            # print(msg)
            # #cfh.config_handler.print_current_config()
            # Trade_WS_Streamer.client = StockDataStream(LIVE_DATA_API_KEY, LIVE_DATA_SECRET_KEY, raw_data=True, websocket_params={}, feed=live_data_feed)

        else:
            print("websocket client bezi")
            if self.symbol_exists(obj.symbol):
                print("Symbol",obj.symbol,"již je subscribnuty")
                return
            Trade_WS_Streamer.client.subscribe_trades(self.datahandler, obj.symbol)

    def remove_stream(self, obj: TradeAggregator2Queue):
        #delete added stream
        try:
            Trade_WS_Streamer._streams.remove(obj)
        except ValueError:
            print("value not found in _streams")
            return
        #if it is the last item at all, stop the client from running
        if len(Trade_WS_Streamer._streams) == 0:
            print("removed last item from WS, stopping the client")
            #Trade_WS_Streamer.client.stop_ws()
            #Trade_WS_Streamer.client.stop()
            #zkusíme explicitně zavolat kroky pro disconnect od ws
            if Trade_WS_Streamer.client._stop_stream_queue.empty():
                Trade_WS_Streamer.client._stop_stream_queue.put_nowait({"should_stop": True})
            Trade_WS_Streamer.client._should_run = False
            return
        
        if not self.symbol_exists(obj.symbol):
            Trade_WS_Streamer.client.unsubscribe_trades(obj.symbol)
            print("symbol no longer used, unsubscribed from ", obj.symbol)
 

    # dispatch for all streams
    @classmethod 
    async def datahandler(cls, data):

        #REFACTOR nemuze byt takto? vyzkouset, pripadne se zbavit to_run dict
        #overit i kvuli performance
        for i in cls._streams:
            if i.symbol == data['S']:
                await i.ingest_trade(packb(data))

        #pro každý symbol volat příslušné agregátory pro symbol
        # for i in self.to_run[data['S']]:
        #     #print("ingest pro", data['S'], "volano", i)
        #     await i.ingest_trade(packb(data))
        # #print("*"*40)

        #zatim vracime do jedne queue - dodelat dynamicky

   # Override the run() function of Thread class
    def run(self):
        if len(Trade_WS_Streamer._streams)==0:
            print("call add streams to queue")
        print("*"*10, "WS Streamer - run", current_thread().name,"*"*10)
        
        #iterujeme nad streamy
        unique = set()
        for i in self._streams:
            print("symbol ve streams", i.symbol)
            unique.add(i.symbol)

        ##z unikatnich symbolu naplnime keys pro dictionary
        #print(self.uniquesymbols)
        # for i in self.uniquesymbols:
        #     self.to_run

        #TODO nejspis s lockem? kdyz menime pri bezici strategii

        #vytvorime prazdne dict oklicovane unik.symboly a obsahujici prazdne pole
        #with self.lock:
            ##self.to_run = {key: [] for key in self.uniquesymbols}
            #stejne tak pro glob.tridu last price 
            #TODO predelat pro concurrency
            #ltp.price = {key: 0 for key in self.uniquesymbols}
            #pro kazdy symbol do toho pole ulozime instance na spusteni
        #     print(self.to_run)
        #     for i in self._streams:
        #         self.to_run[i.symbol].append(i)
        
        # print ("promenna to_run:",self.to_run)

        # sub for unique symbols
        for i in unique: 
            Trade_WS_Streamer.client.subscribe_trades(Trade_WS_Streamer.datahandler, i)
            print("subscribed to",i)

        #timto se spusti jenom poprve v 1 vlaknu
        #ostatni pouze vyuzivaji
        if Trade_WS_Streamer.client._running is False:
            print(self.name, "it is not running, starting by calling RUN")
            print("*"*10, "WS Streamer STARTED", "*"*10)
            Trade_WS_Streamer.client.run()
            print("*"*10, "WS Streamer STOPPED", "*"*10)
        #tímto se spustí pouze 1.vlakno, nicmene subscribe i pripadny unsubscribe zafunguji
        else:
            print("Websocket client is running, not calling RUN this time")


