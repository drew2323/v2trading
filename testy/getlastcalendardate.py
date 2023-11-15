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

clientTrading = TradingClient(ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY, raw_data=False)

#get previous days bar

datetime_object_from = datetime.datetime(2023, 10, 11, 4, 0, 00, tzinfo=datetime.timezone.utc)
datetime_object_to = datetime.datetime(2023, 10, 16, 16, 1, 00, tzinfo=datetime.timezone.utc)
calendar_request = GetCalendarRequest(start=datetime_object_from,end=today)
cal_dates = clientTrading.get_calendar(calendar_request)
print(cal_dates)