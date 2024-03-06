from alpaca.trading.enums import OrderSide, OrderType
from threading import Lock
from v2realbot.interfaces.general_interface import GeneralInterface
from v2realbot.backtesting.backtester import Backtester
from datetime import datetime
from v2realbot.utils.utils import zoneNY
import v2realbot.utils.config_handler as cfh

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
        self.count_api_requests = cfh.config_handler.get_val('COUNT_API_REQUESTS')
        self.mincnt = list([dict(minute=0,count=0)])
        #TODO time v API nejspis muzeme dat pryc a BT bude si to brat primo ze self.time (nezapomenout na + BT_DELAYS)
        # self.time = self.bt.time

    #pocita pocet api requestu za minutu
    def count(self):
        if self.count_api_requests: 
            #get minute od the day
            now = datetime.fromtimestamp(self.bt.time).astimezone(zoneNY)
            dayminute = now.hour*60 + now.minute
            if self.mincnt[-1]["minute"] == dayminute:
                self.mincnt[-1]["count"] += 1
            else:
                self.mincnt.append(dict(minute=dayminute, count=1))

    """initial checks."""
    def start_checks(self):
        print("start_checks")
        
    """buy market"""
    def buy(self, size = 1, repeat: bool = False):
        self.count()
        #add REST API latency
        return self.bt.submit_order(time=self.bt.time + cfh.config_handler.get_val('BT_DELAYS','strat_to_sub'),symbol=self.symbol,side=OrderSide.BUY,size=size,order_type = OrderType.MARKET) 
    
    """buy limit"""
    def buy_l(self, price: float, size: int = 1, repeat: bool = False, force: int = 0):
        self.count()
        return self.bt.submit_order(time=self.bt.time + cfh.config_handler.get_val('BT_DELAYS','strat_to_sub'),symbol=self.symbol,side=OrderSide.BUY,size=size,price=price,order_type = OrderType.LIMIT) 
    
    """sell market"""
    def sell(self, size = 1, repeat: bool = False):
        self.count()
        return self.bt.submit_order(time=self.bt.time + cfh.config_handler.get_val('BT_DELAYS','strat_to_sub'),symbol=self.symbol,side=OrderSide.SELL,size=size,order_type = OrderType.MARKET) 

    """sell limit"""
    async def sell_l(self, price: float, size = 1, repeat: bool = False):
        self.count()
        return self.bt.submit_order(time=self.bt.time + cfh.config_handler.get_val('BT_DELAYS','strat_to_sub'),symbol=self.symbol,side=OrderSide.SELL,size=size,price=price,order_type = OrderType.LIMIT)        

    """replace order"""
    async def repl(self, orderid: str, price: float = None, size: int = None, repeat: bool = False):
        self.count()
        return self.bt.replace_order(time=self.bt.time + cfh.config_handler.get_val('BT_DELAYS','strat_to_sub'),id=orderid,size=size,price=price)
    
    """cancel order"""
    #TBD exec predtim?
    def cancel(self, orderid: str):
        self.count()
        return self.bt.cancel_order(time=self.bt.time + cfh.config_handler.get_val('BT_DELAYS','strat_to_sub'), id=orderid)

    """get positions ->(size,avgp)"""
    #TBD exec predtim?
    def pos(self):
        self.count()
        return self.bt.get_open_position(symbol=self.symbol)

    """get open orders ->list(Order)"""      
    def get_open_orders(self, side: OrderSide, symbol: str):
        self.count()
        return self.bt.get_open_orders(side=side, symbol=symbol)
    
    def get_last_price(self, symbol: str):
        self.count()
        return self.bt.get_last_price(time=self.bt.time)


    
    