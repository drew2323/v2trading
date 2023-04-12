from alpaca.trading.enums import OrderSide, OrderType
from threading import Lock
from v2realbot.interfaces.general_interface import GeneralInterface
from v2realbot.backtesting.backtester import Backtester
from v2realbot.config import BT_DELAYS

""""
backtester methods can be called
- within the Strategy
- from the OrderUpdate notification callback

both should be backtestable

if method are called for the past self.time must be set accordingly
"""
class BacktestInterface(GeneralInterface):
    def __init__(self, symbol, bt: Backtester) -> None:
        self.symbol = symbol
        self.bt = bt
        #TODO time v API nejspis muzeme dat pryc a BT bude si to brat primo ze self.time (nezapomenout na + BT_DELAYS)
        # self.time = self.bt.time

    """initial checks."""
    def start_checks(self):
        print("start_checks")
        
    """buy market"""
    def buy(self, size = 1, repeat: bool = False):
        #add REST API latency
        return self.bt.submit_order(time=self.bt.time + BT_DELAYS.strat_to_sub,symbol=self.symbol,side=OrderSide.BUY,size=size,order_type = OrderType.MARKET) 
    
    """buy limit"""
    def buy_l(self, price: float, size: int = 1, repeat: bool = False, force: int = 0):
        return self.bt.submit_order(time=self.bt.time + BT_DELAYS.strat_to_sub,symbol=self.symbol,side=OrderSide.BUY,size=size,price=price,order_type = OrderType.LIMIT) 
    
    """sell market"""
    def sell(self, size = 1, repeat: bool = False):
        return self.bt.submit_order(time=self.bt.time + BT_DELAYS.strat_to_sub,symbol=self.symbol,side=OrderSide.SELL,size=size,order_type = OrderType.MARKET) 

    """sell limit"""
    async def sell_l(self, price: float, size = 1, repeat: bool = False):
        return self.bt.submit_order(time=self.bt.time + BT_DELAYS.strat_to_sub,symbol=self.symbol,side=OrderSide.SELL,size=size,price=price,order_type = OrderType.LIMIT)        

    """replace order"""
    async def repl(self, orderid: str, price: float = None, size: int = None, repeat: bool = False):
        return self.bt.replace_order(time=self.bt.time + BT_DELAYS.strat_to_sub,id=orderid,size=size,price=price)
    
    """cancel order"""
    #TBD exec predtim?
    def cancel(self, orderid: str):
        return self.bt.cancel_order(time=self.bt.time + BT_DELAYS.strat_to_sub, id=orderid)

    """get positions ->(size,avgp)"""
    #TBD exec predtim?
    def pos(self):
        return self.bt.get_open_position(symbol=self.symbol)

    """get open orders ->list(Order)"""      
    def get_open_orders(self, side: OrderSide, symbol: str):
        return self.bt.get_open_orders(side=side, symbol=symbol)
    
    def get_last_price(self, symbol: str):
        return self.bt.get_last_price(time=self.bt.time)


    
    