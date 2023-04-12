from alpaca.data.live import StockDataStream
from alpaca.common.enums import BaseURL
import datetime
import pandas as pd
from alpaca.data.models import Bar, Quote, Trade
import csv
from config import API_KEY, SECRET_KEY

key = 'PKHVMXQA09IVXALL92JR'
secret = 'FmPwQRFIl7jhLRrXee0Ui73zM9NmAf5O4VH2tyAf'

# keys required for stock historical data client
#client = StockHistoricalDataClient(key, secret)

# keys required
client = StockDataStream(api_key=API_KEY,secret_key=SECRET_KEY)

df_glob = pd.DataFrame(columns=['timestamp','symbol', 'exchange','size','price','id','conditions','tape'])

file = open('Trades.txt', 'w')

# async handler
async def quote_data_handler(data):
    #global df_glob
    #f_loc = pd.DataFrame(data)
    #df_glob = df_glob.append(df_loc, ignore_index=True)
    # quote data will arrive here
    print(data)
    ne = str(data) + "\n"
    file.write(ne)
    #print(data.timestamp,data.symbol, data.price, data.size, data.exchange, data.id, data.conditios,tape)
    print("-"*40)

#client.subscribe_updated_bars(quote_data_handler, "BAC")
#client.subscribe_quotes(quote_data_handler, "BAC")
client.subscribe_trades(quote_data_handler, "BAC")

print("pred spustenim run")
try:
    client.run()
    #print(df)
except Exception as err:
    print(f"{type(err).__name__} was raised: {err}")
    print("globalni dataframe")
    print(df_glob)
    file.close()

print(df_glob)

#    timestamp symbol exchange size price   id conditions tape           0                                 1
# 0        NaN    NaN      NaN  NaN   NaN  NaN        NaN  NaN      symbol                               BAC
# 1        NaN    NaN      NaN  NaN   NaN  NaN        NaN  NaN   timestamp  2023-02-15 19:47:19.430511+00:00
# 2        NaN    NaN      NaN  NaN   NaN  NaN        NaN  NaN    exchange                                 V
# 3        NaN    NaN      NaN  NaN   NaN  NaN        NaN  NaN       price                             35.52
# 4        NaN    NaN      NaN  NaN   NaN  NaN        NaN  NaN        size                              50.0
# ..       ...    ...      ...  ...   ...  ...        ...  ...         ...                               ...
# 59       NaN    NaN      NaN  NaN   NaN  NaN        NaN  NaN       price                             35.51
# 60       NaN    NaN      NaN  NaN   NaN  NaN        NaN  NaN        size                               7.0
# 61       NaN    NaN      NaN  NaN   NaN  NaN        NaN  NaN          id                    56493486924086
# 62       NaN    NaN      NaN  NaN   NaN  NaN        NaN  NaN  conditions                            [ , I]
# 63       NaN    NaN      NaN  NaN   NaN  NaN        NaN  NaN        tape                                 A

    order_data_json = request.get_json()

    # validate data
    MarketOrderRequest(**order_data_json)