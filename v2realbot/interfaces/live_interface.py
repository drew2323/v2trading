from v2realbot.enums.enums import RecordType, StartBarAlign
from datetime import datetime, timedelta
from v2realbot.utils.utils import ltp
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, TakeProfitRequest, LimitOrderRequest, ReplaceOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass, OrderStatus, QueryOrderStatus
from alpaca.trading.models import Order, Position
from alpaca.common.exceptions import APIError
from v2realbot.config import Keys
from v2realbot.interfaces.general_interface import GeneralInterface
"""""
Live interface with Alpaca for LIVE and PAPER trading.
"""""
class LiveInterface(GeneralInterface):
    def __init__(self, symbol: str, key: Keys) -> None:
        self.symbol = symbol
        self.key :Keys = key
        self.trading_client = TradingClient(api_key=key.API_KEY, secret_key=key.SECRET_KEY, paper=key.PAPER)
 
    def start_checks(self):
        pass

    """buy market"""
    def buy(self, size = 1, repeat: bool = False):

        order_request = MarketOrderRequest(
                                    symbol=self.symbol,
                                    qty=size,
                                    side=OrderSide.BUY,
                                    time_in_force=TimeInForce.GTC,
                                    order_class=OrderClass.SIMPLE,
                                    take_profit = None
                                    )
        try:
            # Market order submit
            market_order = self.trading_client.submit_order(
                            order_data=order_request
                        )
            
            return market_order.id
        except Exception as e:
            print("Nepodarilo se odeslat buy", str(e))
            return -1

    """buy limit"""
    def buy_l(self, price: float, size: int = 1, repeat: bool = False, force: int = 0):
        
        limit_request = LimitOrderRequest(
                                    symbol=self.symbol,
                                    qty=size,
                                    side=OrderSide.BUY,
                                    time_in_force=TimeInForce.GTC,
                                    order_class=OrderClass.SIMPLE,
                                    take_profit = None,
                                    limit_price = price
                                    )
        try:
            # Market order submit
            limit_order = self.trading_client.submit_order(
                            order_data=limit_request
                        )
            
            print("LIIF: odeslana litmka s cenou", price, "- akt. cena", ltp.price[self.symbol])

            return limit_order.id
        except Exception as e:
            print("Nepodarilo se odeslat limitku", str(e))
            return -1

    """sell market"""
    def sell(self, size = 1, repeat: bool = False):

        order_request = MarketOrderRequest(
                                    symbol=self.symbol,
                                    qty=size,
                                    side=OrderSide.SELL,
                                    time_in_force=TimeInForce.GTC,
                                    order_class=OrderClass.SIMPLE,
                                    take_profit = None
                                    )
        try:
            # Market order submit
            market_order = self.trading_client.submit_order(
                            order_data=order_request
                        )
            
            return market_order.id
        except Exception as e:
            print("Nepodarilo se odeslat sell", str(e))
            return -1

    """sell limit"""
    async def sell_l(self, price: float, size = 1, repeat: bool = False):
        self.size = size
        self.repeat = repeat

        limit_order = LimitOrderRequest(
                                    symbol=self.symbol,
                                    qty=self.size,
                                    side=OrderSide.SELL,
                                    time_in_force=TimeInForce.GTC,
                                    order_class=OrderClass.SIMPLE,
                                    limit_price = price)
        try:
            # Market order submit
            limit_order = self.trading_client.submit_order(
                            order_data=limit_order
                        )

            #pripadne ulozeni do self.lastOrder
            return limit_order.id
        
        except Exception as e:
            print("Nepodarilo se odeslat sell_l", str(e))
            #raise Exception(e)
            return -1
        
    """order replace"""
    async def repl(self, orderid: str, price: float = None, size: int = None, repeatl: bool = False):
        
        if not price and not size:
            print("price or size has to be filled")
            return -1
        
        replace_request = ReplaceOrderRequest(qty=size, limit_price=price)
        
        try:
            print("request na replace",replace_request)
            print("cislo objednavky",orderid)
            replaced_order = self.trading_client.replace_order_by_id(orderid, replace_request)
            print("replaced ok",replaced_order.id)
            return replaced_order.id
        except APIError as e:
            #stejne parametry - stava se pri rychle obratce, nevadi, vracime stejne orderid, chytne se dal
            if e.code == 42210000: return orderid
            else:
                ##mozna tady proste vracet vzdy ok
                print("Neslo nahradit profitku. Problem",str(e))
                return -1
                #raise Exception(e)

    """order cancel"""
    def cancel(self, orderid: str):
        try:
            a  = self.trading_client.cancel_order_by_id(orderid)
            print("rusime order",orderid)
            return a
        except APIError as e:
            #order doesnt exist
            if e.code == 40410000: return 0
            else:
                print("nepovedlo se zrusit objednavku", str(e))
                #raise Exception(e)
                return -1
            
    """get positions ->(size,avgp)"""
    def pos(self):
        try:
            a : Position = self.trading_client.get_open_position(self.symbol)
            self.avgp, self.poz = float(a.avg_entry_price), int(a.qty) 
            return a.avg_entry_price, a.qty
        except APIError as e:
            #no position
            if e.code == 40410000: return 0,0
            else:
                #raise Exception(e)
                return -1
            
    """get open orders ->list(Order)"""         
    def get_open_orders(self, symbol: str, side: OrderSide = OrderSide.SELL): # -> list(Order):
        getRequest = GetOrdersRequest(status=QueryOrderStatus.OPEN, side=side, symbols=[symbol])
        try:
            # Market order submit
            orderlist = self.trading_client.get_orders(getRequest)
            #list of Orders (orderlist[0].id)
            return orderlist
        except Exception as e:
            print("Chyba pri dotazeni objednávek.", str(e))
            #raise Exception (e)
            return -1
    
    def get_last_price(self, symbol: str):
        return ltp.price[symbol]


    
    