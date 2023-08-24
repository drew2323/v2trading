from threading import Thread, current_thread
import threading
from alpaca.data.live import StockDataStream, CryptoDataStream
from v2realbot.config import ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY, ACCOUNT1_PAPER_MAX_BATCH_SIZE
import queue
from alpaca.data.enums import DataFeed
from typing_extensions import Any
import time
from v2realbot.loader.aggregator import TradeAggregator2Queue
from v2realbot.enums.enums import RecordType, StartBarAlign, Mode, Order


# class ws_agg() :
#     def __init__(self, client, symbol) -> None:
#        # Call the Thread class's init function
#        Thread.__init__(self)
#        self.client = client
#        self.symbol = symbol



#object composition

"""""
vlakno je zde pro asynchronni zapnuti klienta, 
vlakno je vzdy pouze jedno, nicmene instancovani teto tridy je kvuli stejnemu chovani 
s ostatnimi streamery (v budoucnu mozna predelat na dedicated streamer a shared streamer)
"""""
class WS_Stream(Thread):
    client = CryptoDataStream(ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY, raw_data=True, websocket_params={})
    _streams = []
    lock = threading.Lock()

    def __init__(self, name) -> None:
       # Call the Thread class's init function
       Thread.__init__(self, name=name)
       #promenna bude obsahovat seznam streamů
       name = name

    def symbol_exists(self, symbol):
        for i in WS_Stream._streams:
           if i.symbol == symbol:
               return True
        return False

    def add_stream(self, obj):
        WS_Stream._streams.append(obj)
        if WS_Stream.client._running is False:
            print("websocket zatim nebezi, pridavame do pole")
            #do promenne tridy se zapise agregator
        else:
            print("websokcet bezi - pouze subscribujeme")
            WS_Stream.client.subscribe_trades(self.handler, obj.symbol)
            print("muze se vratit uz subscribnuto, coz je ok")

    def remove_stream(self, obj):
        #delete added stream
        try:
            WS_Stream._streams.remove(obj)
        except ValueError:
            print("value not found in _streams")
            return
        #if it is the last item at all, stop the client from running
        if len( WS_Stream._streams) == 0:
            print("removed last item from WS, stopping the client")
            WS_Stream.client.stop()
            return
        
        if not self.symbol_exists(obj.symbol):
            WS_Stream.client.unsubscribe_trades(obj.symbol)
            print("symbol no longer used, unsubscribed from ", obj.symbol)
        
    @classmethod
    async def handler(cls, data):
        print("handler ve threadu:",current_thread().name)
        # podíváme kolik streamů je instancovaných pro tento symbol - v dict[symbol] a spusteni
        # pro každý stream zavoláme

        print(data)
        print("*"*40)

    def run(self):
        print(self.name, "AKtualni vlakno")
        if(len(self._streams)==0):
            print(self.name, "no streams. no run")
            return
        #print(self._streams)
        unique = set()
        ## for each symbol we subscribe
        for i in self._streams:
            #print(self.name, i.symbol)
            #instanciace tradeAggregatoru a uložení do dict[symbol]
            #zde
            unique.add(i.symbol)
        #print(unique)
        #subscribe for unique symbols

        #
        ##TODO *PROBLEM* co kdyz chci subscribe stejneho symbolu co uz konzumuje jina strategie. PROBLEM koncepční
        ##TODO pri skonceni jedne strategie, udelat teardown kroky jako unsubscribe pripadne stop
        for i in unique: 
            WS_Stream.client.subscribe_trades(self.handler, i)
            print(self.name, "subscribed to",i)
        #timto se spusti jenom poprve v 1 vlaknu
        #ostatni pouze vyuzivaji
        if WS_Stream.client._running is False:
            print(self.name, "it is not running, starting by calling RUN")
            WS_Stream.client.run()
        #tímto se spustí pouze 1.vlakno, nicmene subscribe i pripadny unsubscribe zafunguji
        else:
            print(self.name, "it is running, not calling RUN")


# class SymbolStream():
#     def __init__(self, symbol) -> None:
#         self.symbol = symbol
#         s
# class StreamRequest:
#     symbol: str
#     resolution: int

#clientDataStream = CryptoDataStream(API_KEY, SECRET_KEY, raw_data=True, websocket_params={})

# novy ws stream - vždy jednom vláknu
obj= WS_Stream(name="jednicka")
q1 = queue.Queue()
stream1 = TradeAggregator2Queue(symbol="BTC/USD",queue=q1,rectype=RecordType.BAR,timeframe=1,update_ltp=False,align=StartBarAlign.ROUND,mintick = 0)
obj.add_stream(stream1)
print("1", WS_Stream._streams)
# novy ws stream - vždy jednom vláknu
obj2= WS_Stream("dvojka")
stream2 = TradeAggregator2Queue(symbol="ETH/USD",queue=q1,rectype=RecordType.BAR,timeframe=1,update_ltp=False,align=StartBarAlign.ROUND,mintick = 0)
obj2.add_stream(stream2)
print("2", WS_Stream._streams)
obj.start()
print("po startu prvniho")
print(WS_Stream._streams)
time.sleep(1)
obj2.start()
print("po startu druheho")
time.sleep(2)
print("pridavame treti")
obj3 = WS_Stream(name="trojka")
stream3 = TradeAggregator2Queue(symbol="BTC/USD",queue=q1,rectype=RecordType.BAR,timeframe=1,update_ltp=False,align=StartBarAlign.ROUND,mintick = 0)
obj3.add_stream(stream3)
obj3.start()
print(WS_Stream._streams)
print("po zapnuti trojky")
time.sleep(5)
print("cekame na skonceni")
print("celkem enumerate", threading.enumerate())
time.sleep(2)
print("rusim jednicku")
obj.remove_stream(stream1)
print("po ruseni")
time.sleep(2)
print("rusim dvojku")
obj2.remove_stream(stream2)
print("po ruseni")
time.sleep(2)
print("rusim trojku")
obj3.remove_stream(stream3)
obj2.join()
obj.join()

