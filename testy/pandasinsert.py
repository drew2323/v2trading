from uuid import UUID, uuid4
from alpaca.trading.enums import OrderSide, OrderStatus, TradeEvent, OrderType
from common.model import TradeUpdate, Order
from rich import print
import threading
import asyncio
from config import BT_DELAYS
from utils.utils import AttributeDict, ltp, zoneNY, trunc
from utils.tlog import tlog
from datetime import datetime
import pandas as pd
import mplfinance as mpf


trade1 = TradeUpdate(order =Order(id=uuid4(),
                                submitted_at = datetime(2023, 3, 17, 9, 30, 0, 0, tzinfo=zoneNY),
                                symbol = "BAC",
                                qty = 1,
                                status = OrderStatus.ACCEPTED,
                                order_type = OrderType.LIMIT,
                                side = OrderSide.BUY,
                                limit_price=22.4),
                    event = TradeEvent.FILL,
                    execution_id = uuid4(),
                    timestamp = datetime.now(),
                    position_qty= 2,
                    price=22.3,
                    qty = 2,
                    value = 44.6)

trade2 = TradeUpdate(order =Order(id=uuid4(),
                                submitted_at = datetime(2023, 3, 17, 9, 34, 0, 0, tzinfo=zoneNY),
                                symbol = "BAC",
                                qty = 1,
                                status = OrderStatus.ACCEPTED,
                                order_type = OrderType.LIMIT,
                                side = OrderSide.SELL,
                                limit_price=22.4),
                    event = TradeEvent.FILL,
                    execution_id = uuid4(),
                    timestamp = datetime.now(),
                    position_qty= 2,
                    price=24.3,
                    qty = 2,
                    value = 48.6)
trades= [trade1,trade2]
#print(trades)
trade_dict = AttributeDict(timestamp=[],symbol=[],qty=[],price=[],position_qty=[],value=[])

for t in trades:
    trade_dict.timestamp.append(t.timestamp)
    trade_dict.symbol.append(t.order.symbol)
    trade_dict.qty.append(t.qty)
    trade_dict.price.append(t.price)
    trade_dict.position_qty.append(t.position_qty)
    trade_dict.value.append(t.value)

print(trade_dict)

trade_df = pd.DataFrame(trade_dict)
trade_df = trade_df.set_index('timestamp')

mpf.plot(trade_df, # the dataframe containing the OHLC (Open, High, Low and Close) data
         type='candle', # use candlesticks 
         volume=True, # also show the volume
         mav=(3,6,9), # use three different moving averages
         figratio=(3,1), # set the ratio of the figure
         style='yahoo',  # choose the yahoo style
         title='Bitcoin on Wednesday morning');

print(trade_df)
#pd.DataFrame()


#self.trades.append(trade)
