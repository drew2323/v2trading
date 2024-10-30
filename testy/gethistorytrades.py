import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import CryptoLatestTradeRequest, StockLatestTradeRequest, StockLatestBarRequest, StockTradesRequest
from alpaca.data.enums import DataFeed
from v2realbot.config import ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY
from v2realbot.utils.utils import zoneNY
from datetime import datetime, timezone, time, timedelta, date
import pytz
from rich import print
import time

parametry = {}
symbol = ["BAC"]
client = StockHistoricalDataClient(ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY, raw_data=True)
datetime_object_from = datetime(2023, 4, 12, 15, 45, 8, tzinfo=zoneNY)
datetime_object_to = datetime(2023, 4, 13, 15, 45, 10, tzinfo=zoneNY)
trades_request = StockTradesRequest(symbol_or_symbols=symbol, feed = DataFeed.SIP, start=datetime_object_from, end=datetime_object_to, page_limit=100000)

#time this for performance
start_time = time.time()
all_trades = client.get_stock_trades(trades_request)
# End the timer
end_time = time.time()

# Calculate elapsed time
elapsed_time = end_time - start_time
print(f"Call duration: {elapsed_time:.4f} seconds")
#35s s 100.000 page_limit #alpaca-py 0.18.1 - DAY
#35s      10.000 limit
#installed 0.31.0

# print(len(all_trades['BAC']))
# print(all_trades['BAC'])

# for i in all_trades:
#     print(all_trades[i])

# if __name__ == "__main__":
#     # bar will be invoked if this module is being run directly, but not via import!
#     print("hello")