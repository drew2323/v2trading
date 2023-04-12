# 2 clients for historical data StockHistoricalDataClient (needs keys), CryptoHistoricalDataClient
# 2 clients for real time data CryptoDataStream, StockDataStream


# naimportuju si daneho clienta
from alpaca.data.historical import StockHistoricalDataClient, CryptoHistoricalDataClient

#pokdu pouzivam historicke data(tzn. REST) tak si naimportuju dany request object
from alpaca.data.requests import StockLatestQuoteRequest, StockBarsRequest, StockTradesRequest

#objekty se kterymi pak pracuju (jsou soucasi package výše, tady jen informačně)
from alpaca.data import Quote, Trade, Snapshot, Bar
from alpaca.data.models import BarSet, QuoteSet, TradeSet


from config import API_KEY, SECRET_KEY
from datetime import datetime, timedelta
import pandas as pd
import rich

# vytvorim si clienta
stock_client = StockHistoricalDataClient(API_KEY, SECRET_KEY, raw_data=True)
crypto_client = CryptoHistoricalDataClient()

time_from = datetime(2023, 2, 17, 14, 30, 0, 0)
time_to = datetime(2023, 2, 17, 14, 30, 1, 0)
#print(time_from)

# vytvorim request objekt
#latestQuoteRequest = StockLatestQuoteRequest(symbol_or_symbols=["SPY", "GLD", "TLT"])
stockTradeRequest = StockTradesRequest(symbol_or_symbols=["BAC","C","MSFT"], start=time_from,end=time_to)

#zavolam na clientovi metodu s request objektem, vrací se mi Dict[str, Quote] - obj.Quote pro kazdy symbol
#latestQuoteObject = stock_client.get_stock_latest_quote(latestQuoteRequest)
tradesResponse = stock_client.get_stock_trades(stockTradeRequest)
print(tradesResponse)

for i in tradesResponse['BAC']:
    print(i)

# vrací m to tradeset dict = Trades identifikovane symbolem

#for 

#access as a list
#print(tradesResponse["BAC"])

# The scope of these changes made to
# pandas settings are local to with statement.
# with pd.option_context('display.max_rows', None,
#                        'display.max_columns', None,
#                        'display.precision', 3,
#                        ):
#     #convert to dataframe
#     print(tradesResponse.df)

# this is the Quote object for 
#bacquote=latestQuoteObject["SPY"]

# print(bacquote)
#vrati se mi objekt typu LatestQuote
# print(type(latestQuoteObject))

# print(latestQuoteObject)
#gld_latest_ask_price = latestQuoteObject["GLD"].ask_price
#print(gld_latest_ask_price, latestQuoteObject["GLD"].timestamp)