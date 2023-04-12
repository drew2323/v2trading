from alpaca.data.historical import CryptoHistoricalDataClient, StockHistoricalDataClient
from alpaca.data.requests import CryptoLatestTradeRequest, StockLatestTradeRequest, StockLatestBarRequest, StockTradesRequest
from alpaca.data.enums import DataFeed
from config import API_KEY, SECRET_KEY, MAX_BATCH_SIZE
import datetime
import time

parametry = {}

# no keys required
#client = CryptoHistoricalDataClient()
client = StockHistoricalDataClient(API_KEY, SECRET_KEY, raw_data=True)

# single symbol request
#request_trade_params = StockTradesRequest(symbol_or_symbols="BAC", feed = DataFeed.SIP)
#request_last_bar_params = StockLatestBarRequest(symbol_or_symbols="BAC", feed=DataFeed.SIP)

#2023, 2, 27, 18, 51, 38

datetime_object_from = datetime.datetime(2023, 2, 26, 17, 51, 38, tzinfo=datetime.timezone.utc)

datetime_object_to = datetime.datetime(2023, 2, 28, 17, 51, 39, tzinfo=datetime.timezone.utc)

trades_request = StockTradesRequest(symbol_or_symbols="C", feed = DataFeed.SIP, start=datetime_object_from, end=datetime_object_to)
#latest_trade = client.get_stock_latest_trade(request_trade_params)
#latest_bar = client.get_stock_latest_bar(request_last_bar_params)

# for i in range(1,1000):
#     latest_bar = client.get_stock_latest_bar(request_last_bar_params)
#     data = latest_bar['BAC']
#     print(data.timestamp,data.trade_count, data.trade_count, data.high, data.low, data.close, data.volume, data.vwap)
#     time.sleep(1)

all_trades = client.get_stock_trades(trades_request)
# must use symbol to access even though it is single symbol
# print("last trade",latest_trade)
# print("latest bar",latest_bar)
# print("Trades Today", all_trades)
print(len(all_trades["C"]))
