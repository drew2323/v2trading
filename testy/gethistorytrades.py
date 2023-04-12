import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from alpaca.data.historical import CryptoHistoricalDataClient, StockHistoricalDataClient
from alpaca.data.requests import CryptoLatestTradeRequest, StockLatestTradeRequest, StockLatestBarRequest, StockTradesRequest
from alpaca.data.enums import DataFeed
from config import API_KEY, SECRET_KEY, MAX_BATCH_SIZE
from datetime import datetime, timezone, time, timedelta, date
import pytz
from rich import print

#práce s datumy

zone_NY = pytz.timezone('America/New_York')

parametry = {}
symbol = ["BAC"]
client = StockHistoricalDataClient(API_KEY, SECRET_KEY, raw_data=True)
datetime_object_from = datetime(2023, 3, 16, 9, 30, 0, tzinfo=zone_NY)
datetime_object_to = datetime(2023, 3, 16, 16, 00, 0, tzinfo=zone_NY)
trades_request = StockTradesRequest(symbol_or_symbols=symbol, feed = DataFeed.SIP, start=datetime_object_from, end=datetime_object_to)

all_trades = client.get_stock_trades(trades_request)

#print(all_trades)

print(len(all_trades['BAC']))

# for i in all_trades:
#     print(all_trades[i])

if __name__ == "__main__":
    # bar will be invoked if this module is being run directly, but not via import!
    print("hello")