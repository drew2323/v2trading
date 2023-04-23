from strategy.base import Strategy
from utils.utils import zoneNY
from datetime import datetime, timedelta
from utils.utils import parse_alpaca_timestamp, ltp, AttributeDict,trunc
from v2realbot.enums.enums import RecordType, StartBarAlign, Mode, Order, Account
from alpaca.trading.models import TradeUpdate
from alpaca.trading.enums import TradeEvent
from rich import print



class StrategyOrderLimitWatched(Strategy):
    def __init__(self, name: str, symbol: str, next: callable, init: callable, account: Account, mode: Mode = Mode.PAPER, stratvars: AttributeDict = None, open_rush: int = 30, close_rush: int = 30) -> None:
        super().__init__(name, symbol, next, init, account, mode, stratvars, open_rush, close_rush)

    async def orderUpdateBuy(self, data: TradeUpdate):
        if data.event == TradeEvent.FILL:
            #ic("orderbuyfill callback")
            print(data)
            o: Order = data.order
            #dostavame zde i celkové akutální množství - ukládáme
            self.state.positions = data.position_qty
            self.state.avgp = float(data.price)
            self.state.vars.watched = self.state.avgp
            self.state.vars.wait = False

    async def orderUpdateSell(self, data: TradeUpdate):
        if data.event == TradeEvent.FILL:
            print(data)
            self.state.positions = data.position_qty
            self.state.vars.watched = None
            self.state.vars.wait = False
            #ic("SELL notifikace callback - prodano - muzeme znovu nakupovat")
    
    #this parent method is called by strategy just once before waiting for first data
    def strat_init(self):
        #ic("strat INI function")
        #lets connect method overrides
        self.state.buy = self.buy
        self.state.buy_l = self.buy_l

    #overidden methods
    def buy(self, size = None, repeat: bool = False):
        print("overriden method to size&check maximum ")
        # if int(self.state.positions) >= self.state.vars.maxpozic:
        #     print("max mnostvi naplneno")
        #     return 0
        if size is None:
            sizer = self.state.vars.chunk
        else:
            sizer = size
        self.state.blockbuy = 1
        self.state.vars.lastbuyindex = self.state.bars['index'][-1]
        #ic(self.state.blockbuy)
        #ic(self.state.vars.lastbuyindex)
        return self.state.interface.buy(size=sizer)
    
    #pro experiment - nemame zde max mnozstvi
    def buy_l(self, price: float = None, size = None, repeat: bool = False):
        print("overriden buy limitka")
        if size is None: size=self.state.vars.chunk
        if price is None: price=trunc(self.state.interface.get_last_price(self.symbol)-0.01,2)
        #ic(price)
        self.state.blockbuy = 1
        self.state.vars.lastbuyindex = self.state.bars['index'][-1]
        #ic(self.state.blockbuy)
        #ic(self.state.vars.lastbuyindex)
        return self.state.interface.buy_l(price=price, size=size)