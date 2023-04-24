from alpaca.data.historical import CryptoHistoricalDataClient, StockHistoricalDataClient
from alpaca.data.requests import CryptoLatestTradeRequest, StockLatestTradeRequest, StockLatestBarRequest, StockTradesRequest
from alpaca.data.enums import DataFeed
from v2realbot.config import ACCOUNT1_LIVE_API_KEY, ACCOUNT1_LIVE_SECRET_KEY
from datetime import datetime
import time
from v2realbot.utils.utils import zoneNY

parametry = {}

# no keys required
#client = CryptoHistoricalDataClient()
client = StockHistoricalDataClient(ACCOUNT1_LIVE_API_KEY, ACCOUNT1_LIVE_SECRET_KEY, raw_data=True)

# single symbol request
#request_trade_params = StockTradesRequest(symbol_or_symbols="BAC", feed = DataFeed.SIP)
#request_last_bar_params = StockLatestBarRequest(symbol_or_symbols="BAC", feed=DataFeed.SIP)

#2023, 2, 27, 18, 51, 38
client = StockHistoricalDataClient(ACCOUNT1_LIVE_API_KEY, ACCOUNT1_LIVE_SECRET_KEY, raw_data=False)
ted = datetime.now()
timstp=ted.timestamp()
print(f"{timstp=}")
datumfromtimestamp = datetime.fromtimestamp(timstp, zoneNY)
print(datumfromtimestamp)
datetime_object_from = datetime(2023, 4, 14, 15, 51, 38, tzinfo=zoneNY)
datetime_object_to = datetime(2023, 4, 14, 15, 51, 39, tzinfo=zoneNY)
# datetime_object_from = datetime.fromtimestamp(1682310012.024338)
# datetime_object_to = datetime.fromtimestamp(1682310015.024338)
print(datetime_object_from.timestamp())
print(datetime_object_to.timestamp())
trades_request = StockTradesRequest(symbol_or_symbols="BAC", feed = DataFeed.SIP, start=datetime_object_from, end=datetime_object_to)
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
#print(len(all_trades["C"]))
#1682310012.024338
print(all_trades["BAC"])
# raw True
# [{'t': '2023-04-14T19:51:38.432128256Z', 'x': 'D', 'p': 49.805, 's': 100, 'c': [' '], 'i': 71696766285400, 'z': 'A'}, {'t': '2023-04-14T19:51:38.518662144Z', 'x': 'T', 'p': 49.8, 's': 9, 'c': [' ', 'I'], 'i': 62880002366518, 'z': 'A'}]
# raw False
# [{   'conditions': [' '],
#     'exchange': 'D',
#     'id': 71696766285400,
#     'price': 49.805,
#     'size': 100.0,
#     'symbol': 'C',
#     'tape': 'A',
#     'timestamp': datetime.datetime(2023, 4, 14, 19, 51, 38, 432128, tzinfo=datetime.timezone.utc)}, ]