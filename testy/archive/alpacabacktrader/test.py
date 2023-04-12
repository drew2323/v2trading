#udajne working example for using a minute
# timeframe in backtrader with alpaca api


import alpaca_backtrader_api
import backtrader as bt
import pandas as pd
from datetime import datetime
from strategies.tos_strategy import TOS

from dotenv import load_dotenv
import os
load_dotenv()

api_key = os.getenv('API_KEY_ID')
api_secret = os.getenv('API_SECRET')
alpaca_paper = os.getenv('ALPACA_PAPER')

cerebro = bt.Cerebro()
cerebro.addstrategy(TOS)

cerebro.broker.setcash(100000)
cerebro.broker.setcommission(commission=0.0)
cerebro.addsizer(bt.sizers.PercentSizer, percents=20)

store = alpaca_backtrader_api.AlpacaStore(
    key_id=api_key,
    secret_key=api_secret,
    paper=alpaca_paper
)

if not alpaca_paper:
  broker = store.getbroker()  # or just alpaca_backtrader_api.AlpacaBroker()
  cerebro.setbroker(broker)

DataFactory = store.getdata  # or use alpaca_backtrader_api.AlpacaData
data0 = DataFactory(
    dataname='AAPL',
    timeframe=bt.TimeFrame.TFrame("Minutes"),
    fromdate=pd.Timestamp('2018-11-15'),
    todate=pd.Timestamp('2018-11-17'),
    historical=True)
cerebro.adddata(data0)

#Resampler for 15 minutes
cerebro.resampledata(data0,timeframe=bt.TimeFrame.Minutes,compression=15)

print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
cerebro.run()
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
cerebro.plot()