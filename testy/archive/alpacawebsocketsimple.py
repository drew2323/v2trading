
from alpaca.data.live import StockDataStream, CryptoDataStream
from alpaca.trading.stream import TradingStream
from alpaca.data.enums import DataFeed
from config import API_KEY, SECRET_KEY, MAX_BATCH_SIZE
from datetime import datetime
import mplfinance as mpf
import matplotlib.pyplot as plt
import threading
# pripadne parametry pro request
# parametry = {
#   "brand": "Ford",
#   "model": "Mustang",
#   "year": 1964
# }
parametry = {}
i = 0
u = 0
async def data_handler1(data):
    print("HANDLER1")
    global i
    i += 1
    print(data)

async def data_handler2(data):
    print("HANDLER2")
    global u
    u += 1
    print(data)

async def data_handler3(data):
    print("HANDLER3")
    global u
    u += 1
    print(data)

# plt.ion()

# def animate(ival):
# 	# PREPARE DATAFRAME WITH OHLC AND "BUYS" AND "SELLS" HERE
	
#         apds = [mpf.make_addplot(buys, color='tab:green', ax=ax_buys),
# 			mpf.make_addplot(sells, color='tab:red', ax=ax_sells)]
# 	for ax in axes:
# 		ax.clear()
# 	mpf.plot(df_ohlc, type='candle', addplot=apds, ax=ax_main)
# 	print('a')


#client = CryptoDataStream(API_KEY, SECRET_KEY, raw_data=True, websocket_params=parametry)
client1 =  TradingStream(API_KEY, SECRET_KEY, paper=True)
client1.subscribe_trade_updates(data_handler1)
t1 = threading.Thread(target=client1.run)
t1.start()
print("started1")
client2 =  TradingStream(API_KEY, SECRET_KEY, paper=True)
client2.subscribe_trade_updates(data_handler2)
t2 = threading.Thread(target=client2.run)
t2.start()
client3 =  TradingStream(API_KEY, SECRET_KEY, paper=True)
client3.subscribe_trade_updates(data_handler3)
t3 = threading.Thread(target=client3.run)
t3.start()
print("started2")
print(threading.enumerate())
t2.join()
t1.join()
t3.join()

# client.subscribe_trades(data_handler, "BTC/USD")
# #client.subscribe_quotes(data_handler_ETH, "ETH/USD")
# print("pred spustenim runu")
# client.run()
# print("po spusteni runu - muzu neco delat?")
