from threading import Thread
from alpaca.trading.stream import TradingStream
from v2realbot.config import Keys
from v2realbot.common.model import Account

#jelikoz Alpaca podporuje pripojeni libovolneho poctu websocket instanci na order updates
#vytvorime pro kazdou bezici instanci vlastni webservisu (jinak bychom museli delat instanci pro kombinaci ACCOUNT1 - LIVE, ACCOUNT1 - PAPER, ACCOUNT2 - PAPER ..)
#bude jednodussi mit jednu instanci pokazde
"""""
Connects to Alpaca websocket, listens to trade updates
of given account. All notifications of given SYMBOL
routes to strategy callback.

As Alpaca supports connecting of any number of trade updates clients
new instance of this websocket thread is created for each strategy instance.
"""""
class LiveOrderUpdatesStreamer(Thread):
    def __init__(self, key: Keys, name: str, account: Account) -> None:
        self.key = key
        self.account = account
        self.strategy = None
        self.client = TradingStream(api_key=key.API_KEY, secret_key=key.SECRET_KEY, paper=key.PAPER)
        Thread.__init__(self, name=name)
    
    #notif dispatcher - pouze 1 strategie
    async def distributor(self,data):     
        if self.strategy.symbol == data.order.symbol: await self.strategy.order_updates(data, self.account)

   # connects callback to interface object - responses for given symbol are routed to interface callback
    def connect_callback(self, st):
        self.strategy = st

    def disconnect_callback(self, st):
        print("*"*10, "WS Order Update Streamer stopping for", self.strategy.name, "*"*10)
        self.strategy = None
        self.client.stop()

    def run(self):
        ## spusti webservice
        if self.strategy is None:
            print("connect strategy first")
            return
        self.client.subscribe_trade_updates(self.distributor)
        print("*"*10, "WS Order Update Streamer started for", self.strategy.name, "*"*10)
        self.client.run()
        
