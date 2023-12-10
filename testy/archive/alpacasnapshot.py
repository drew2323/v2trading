# 2 clients for historical data StockHistoricalDataClient (needs keys), CryptoHistoricalDataClient
# 2 clients for real time data CryptoDataStream, StockDataStream


# naimportuju si daneho clienta
from alpaca.data.historical import StockHistoricalDataClient, CryptoHistoricalDataClient


#pokdu pouzivam historicke data(tzn. REST) tak si naimportuju dany request object
from alpaca.data.requests import StockLatestQuoteRequest, StockBarsRequest, StockTradesRequest, StockSnapshotRequest

#objekty se kterymi pak pracuju (jsou soucasi package výše, tady jen informačně)
from alpaca.data import Quote, Trade, Snapshot, Bar
from alpaca.data.models import BarSet, QuoteSet, TradeSet
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from v2realbot.utils.utils import zoneNY
from v2realbot.config import ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY
from config import API_KEY, SECRET_KEY
from alpaca.data.enums import DataFeed
from datetime import datetime, timedelta
import pandas as pd
from rich import print
from collections import defaultdict
from pandas import to_datetime
from msgpack.ext import Timestamp
from v2realbot.utils.historicals import convert_historical_bars

def get_last_close():
   pass

def get_todays_open():
    pass

##vrati historicke bary v nasem formatu
def get_historical_bars(symbol: str, time_from: datetime, time_to: datetime, timeframe: TimeFrame):
    stock_client = StockHistoricalDataClient(ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY, raw_data=True)
    bar_request = StockBarsRequest(symbol_or_symbols=symbol,timeframe=timeframe, start=time_from, end=time_to, feed=DataFeed.SIP)
    bars: BarSet = stock_client.get_stock_bars(bar_request)
    print("puvodni bars", bars["BAC"])
    print(bars)
    return convert_historical_bars(bars[symbol])


#v initu plnime pozadovana historicka data do historicals[]
#zatim natvrdo 
#last 30 days bars


#get 30 days
time_to = datetime.now(tz=zoneNY)
time_from = time_to - timedelta(days=2)

bary = get_historical_bars("BAC", time_from, time_to, TimeFrame.Hour)
print(bary)
historicals = defaultdict(dict)
historicals["30"] = bary
print(historicals)

# stock_client = StockHistoricalDataClient(ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY, raw_data=True)
# snapshotRequest = StockSnapshotRequest(symbol_or_symbols=["BAC"], feed="sip")
# snapshotResponse = stock_client.get_stock_snapshot(snapshotRequest)
# print("snapshot", snapshotResponse)
# snapshotResponse["BAC"]["dailyBar"]

