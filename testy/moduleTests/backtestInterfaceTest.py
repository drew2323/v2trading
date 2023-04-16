from v2realbot.config import Keys, get_key
from v2realbot.enums.enums import Mode, Account, OrderSide
from alpaca.trading.enums import OrderSide, OrderStatus, TradeEvent, OrderType
from v2realbot.common.model import TradeUpdate, Order
from v2realbot.interfaces.live_interface import LiveInterface
from v2realbot.interfaces.backtest_interface import BacktestInterface
from v2realbot.backtesting.backtester import Backtester
from datetime import datetime
from v2realbot.utils.utils  import zoneNY
from uuid import UUID, uuid4

def callback():
    print("callback entry")


start = datetime(2023, 4, 10, 9, 30, 0, 0, tzinfo=zoneNY)
end =   datetime(2023, 4, 10, 9, 35, 0, 0, tzinfo=zoneNY)
btdata: list = []
cash=10000
#key = get_key(mode=Mode.PAPER, account=Account.ACCOUNT1)
symbol = "BAC"  

bt = Backtester(symbol = symbol, order_fill_callback= callback, btdata=btdata, cash=cash, bp_from=start, bp_to=end)

bt.open_orders = [Order(id=uuid4(),
                        submitted_at = datetime(2023, 3, 17, 9, 30, 0, 0, tzinfo=zoneNY),
                        symbol = "BAC",
                        qty = 1,
                        status = OrderStatus.ACCEPTED,
                        order_type = OrderType.LIMIT,
                        side = OrderSide.SELL,
                        limit_price=22.4),
                    Order(id=uuid4(),
                        submitted_at = datetime(2023, 3, 17, 9, 30, 00, 0, tzinfo=zoneNY),
                        symbol = "BAC",
                        qty = 1,
                        order_type = OrderType.MARKET,
                        status = OrderStatus.ACCEPTED,
                        side = OrderSide.BUY)]

bt_interface = BacktestInterface(symbol=symbol, bt=bt)

orderlist = bt.get_open_orders(symbol=symbol, side=None)

print(orderlist)
print(len(orderlist))