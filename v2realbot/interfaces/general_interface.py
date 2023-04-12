from alpaca.trading.enums import OrderSide

class GeneralInterface:
    """initial checks."""
    def start_checks(self):
        pass
    
    """buy market"""
    def buy(self, size = 1, repeat: bool = False):
        pass

    """buy limit"""
    def buy_l(self, price: float, size: int = 1, repeat: bool = False, force: int = 0):
        pass

    """sell market"""
    async def sell(self, size = 1, repeat: bool = False):
        pass

    """sell limit"""
    async def sell_l(self, price: float, size = 1, repeat: bool = False):
        pass

    """order replace"""
    async def repl(self, price: float, orderid: str, size: int = 1, repeatl: bool = False):
        pass

    """order update callback"""
    async def orderUpdate(self, data):
        pass

    """get open positions"""
    def pos(self) -> tuple[int, int]:
        pass

    """get open orders"""
    def get_open_orders(self, side: OrderSide, symbol: str):
        pass

    """get most recent price"""
    def get_last_price(symbol: str):
        pass