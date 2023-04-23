from strategy.base import Strategy
from utils.utils import zoneNY
from datetime import datetime, timedelta
from utils.utils import parse_alpaca_timestamp, ltp, AttributeDict,trunc
from utils.tlog import tlog, tlog_exception
from v2realbot.enums.enums import RecordType, StartBarAlign, Mode, Order, Account
from alpaca.data.enums import DataFeed
from alpaca.trading.models import TradeUpdate
from alpaca.trading.enums import TradeEvent
import queue
from indicators import ema
from rich import print
from loader.aggregator import TradeAggregator2Queue, TradeAggregator2List
from loader.order_updates_streamer import LiveOrderUpdatesStreamer
from loader.trade_offline_streamer import Trade_Offline_Streamer
from loader.trade_ws_streamer import Trade_WS_Streamer
from random import randrange
from queue import Queue
from alpaca.trading.stream import TradingStream
from interfaces.general_interface import GeneralInterface
from interfaces.backtest_interface import BacktestInterface
from interfaces.live_interface import LiveInterface
from alpaca.trading.enums import OrderSide, QueryOrderStatus
from alpaca.common.exceptions import APIError
from backtesting.backtester import Backtester


class StrategyOrderLimit(Strategy):
    def __init__(self, name: str, symbol: str, next: callable, init: callable, account: Account, mode: Mode = Mode.PAPER, stratvars: AttributeDict = None, debug: bool = False) -> None:
        super().__init__(name, symbol, next, init, account, mode, stratvars, debug)

    async def orderUpdateBuy(self, data: TradeUpdate):
        if data.event == TradeEvent.FILL or data.event == TradeEvent.PARTIAL_FILL:
            #ic("vstupujeme do orderupdatebuy")
            print(data)
            o: Order = data.order
            #dostavame zde i celkové akutální množství - ukládáme
            self.state.positions = data.position_qty
            if self.state.vars.limitka is None:
                self.state.avgp = float(data.price)
                self.state.vars.limitka = await self.interface.sell_l(price=trunc(float(o.filled_avg_price)+self.state.vars.profit,2), size=o.filled_qty)
            else:
                #avgp, pos
                self.state.avgp, self.state.positions = self.state.interface.pos()
                cena = round(float(self.state.avgp) + float(self.state.vars.profit),2)
                try:
                    self.state.vars.limitka = await self.interface.repl(price=cena,orderid=self.state.vars.limitka,size=int(self.state.positions))
                except APIError as e:
                    #stejne parametry - stava se pri rychle obratce, nevadi
                    if e.code == 42210000: return 0,0
                    else:
                        print("Neslo nahradit profitku. Problem",str(e))
                        raise Exception(e)

    async def orderUpdateSell(self, data: TradeUpdate):
        if data.event == TradeEvent.PARTIAL_FILL:
            #ic("partial fill udpatujeme pozice")
            self.state.avgp, self.state.positions = self.interface.pos()
        elif data.event == TradeEvent.FILL:
            #muzeme znovu nakupovat, mazeme limitku
            #self.state.blockbuy = 0
            #ic("notifikace sell mazeme limitku")
            self.state.vars.limitka = None
            self.state.vars.lastbuyindex = -5
    
    #this parent method is called by strategy just once before waiting for first data
    def strat_init(self):
        #ic("strat INI function")
        #lets connect method overrides
        self.state.buy = self.buy
        self.state.buy_l = self.buy_l

    #overidden methods
    def buy(self, size = None, repeat: bool = False):
        print("overriden method to size&check maximum ")
        if int(self.state.positions) >= self.state.vars.maxpozic:
            print("max mnostvi naplneno")
            return 0
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