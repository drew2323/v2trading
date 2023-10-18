from alpaca.data.historical import CryptoHistoricalDataClient, StockHistoricalDataClient
from alpaca.data.requests import CryptoLatestTradeRequest, StockLatestTradeRequest, StockLatestBarRequest, StockTradesRequest, StockBarsRequest
from alpaca.data.enums import DataFeed
from config import API_KEY, SECRET_KEY, MAX_BATCH_SIZE
import datetime
import time
from alpaca.data import Quote, Trade, Snapshot, Bar
from alpaca.data.models import BarSet, QuoteSet, TradeSet
from alpaca.data.timeframe import TimeFrame
# import mplfinance as mpf
import pandas as pd
from rich import print
from v2realbot.utils.utils import zoneNY
from v2realbot.config import ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY
from alpaca.trading.requests import GetCalendarRequest
from alpaca.trading.client import TradingClient
parametry = {}

# no keys required
#client = CryptoHistoricalDataClient()
client = StockHistoricalDataClient(ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY, raw_data=False)
clientTrading = TradingClient(ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY, raw_data=False)

#get previous days bar

datetime_object_from = datetime.datetime(2023, 10, 11, 4, 0, 00, tzinfo=datetime.timezone.utc)
datetime_object_to = datetime.datetime(2023, 10, 16, 16, 1, 00, tzinfo=datetime.timezone.utc)
calendar_request = GetCalendarRequest(start=datetime_object_from,end=datetime_object_to)
cal_dates = clientTrading.get_calendar(calendar_request)
print(cal_dates)
bar_request = StockBarsRequest(symbol_or_symbols="BAC",timeframe=TimeFrame.Day, start=datetime_object_from, end=datetime_object_to, feed=DataFeed.SIP)

# bars = client.get_stock_bars(bar_request).df

bars: BarSet = client.get_stock_bars(bar_request)
#bars = bars.drop(['symbol'])

#print(bars.df.close)
#bars = bars.tz_convert('America/New_York')
#print(len(bars))
print(bars)
#print(bars.data["BAC"][0])
#print(bars.df.columns)
#Index(['open', 'high', 'low', 'close', 'volume', 'trade_count', 'vwap'], dtype='object')
# bars.df.set_index('timestamp', inplace=True)

# mpf.plot(bars.df, # the dataframe containing the OHLC (Open, High, Low and Close) data
#          type='candle', # use candlesticks 
#          volume=True, # also show the volume
#          mav=(3,6,9), # use three different moving averages
#          figratio=(3,1), # set the ratio of the figure
#          style='yahoo',  # choose the yahoo style
#          title='Prvni chart');

# #vrací se list od dict
# print(bars["BAC"])

# # k nemu muzeme pristupovat s 
# dict = bars["BAC"]
# print(type(dict))
# print(dict[2].timestamp)

# print(dict[2].close)

# print(dict[].close)


