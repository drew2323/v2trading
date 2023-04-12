from threading import Thread, current_thread
from alpaca.data.live import StockDataStream, CryptoDataStream
from v2realbot.config import API_KEY, SECRET_KEY, MAX_BATCH_SIZE, PAPER
import queue
from alpaca.data.enums import DataFeed
from typing_extensions import Any
import time
from v2realbot.loader.aggregator import TradeAggregator

# class ws_agg() :
#     def __init__(self, client, symbol) -> None:
#        # Call the Thread class's init function
#        Thread.__init__(self)
#        self.client = client
#        self.symbol = symbol



#object composition
ws_client = CryptoDataStream(API_KEY, SECRET_KEY, raw_data=True, websocket_params={})
_streams = []
    
def add_stream(self, **data):
    #object composition - pomocí append
    self._streams.append(data)

    async def handler(self, data):
        print("handler ve threadu:",current_thread().name)
        # podíváme kolik streamů je instancovaných pro tento symbol - v dict[symbol] a spusteni
        # pro každý stream zavoláme

        print(data)
        print("*"*40)

    def run(self) :
        print(current_thread().name)
        print(self._streams)
        unique = set()
        ## for each symbol we subscribe
        for i in self._streams:
            print(i['symbol'])
            #instanciace tradeAggregatoru a uložení do dict[symbol]
            #zde
            unique.add(i['symbol'])
        print(unique)
        #subscribe for unique symbols

        #
        ##TODO *PROBLEM* co kdyz chci subscribe stejneho symbolu co uz konzumuje jina strategie. PROBLEM koncepční
        ##TODO pri skonceni jedne strategie, udelat teardown kroky jako unsubscribe pripadne stop
        for i in unique: 
            WS_Stream.client.subscribe_trades(self.handler, i)
            print("subscribed to",i)
        #timto se spusti jenom poprve v 1 vlaknu
        #ostatni pouze vyuzivaji
        if WS_Stream.client._running is False:
            print("it is not running, starting by calling RUN")
            WS_Stream.client.run()
        #tímto se spustí pouze 1.vlakno, nicmene subscribe i pripadny unsubscribe zafunguji
        else:
            print("it is running, not calling RUN")


# class SymbolStream():
#     def __init__(self, symbol) -> None:
#         self.symbol = symbol
#         s
# class StreamRequest:
#     symbol: str
#     resolution: int

#clientDataStream = CryptoDataStream(API_KEY, SECRET_KEY, raw_data=True, websocket_params={})

# novy ws stream - vždy jednom vláknu
obj= WS_Stream("jednicka")
obj.add_stream(symbol="BTC/USD",resolution=15)
# novy ws stream - vždy jednom vláknu
obj2= WS_Stream("dvojka")
obj2.add_stream(symbol="ETH/USD",resolution=5)
obj.start()
time.sleep(1)
obj2.start()
# clientDataStream.run()
# clientDataStream2.run()
obj2.join()
obj.join()

print("po startu")
