from alpaca.data.enums import DataFeed
from v2realbot.enums.enums import FillCondition

#Separate file that contains default values for all config variables
#they are loaded by the config_handler and then can be overriden on the fly 
#by configuration profiles

#note if the type is not simple (enum etc.) dont forget to add it to config_handler get_val function to transform

#PREMIUM pro MARKET order, if positive it means absolute value (0.005), if negative it means pct (0.0167)  #0.005 is approximately 0.0167% of base price 30.
BT_FILL_PRICE_MARKET_ORDER_PREMIUM=0.005
#no dense print in the console
QUIET_MODE=True
BT_FILL_CONS_TRADES_REQUIRED=2
BT_FILL_LOG_SURROUNDING_TRADES= 10
LIVE_DATA_FEED=DataFeed.IEX
OFFLINE_MODE = False
#minimalni vzdalenost mezi trady, kterou agregator pousti pro CBAR(0.001 - blokuje mensi nez 1ms)
GROUP_TRADES_WITH_TIMESTAMP_LESS_THAN = 0.003
#normalized price for tick 0.01
NORMALIZED_TICK_BASE_PRICE = 30.00

#DEFAULT AGGREGATOR filter trades
#NOTE pridana F - Inter Market Sweep Order - obcas vytvarela spajky
AGG_EXCLUDED_TRADES = ['C','O','4','B','7','V','P','W','U','Z','F']
#how many consecutive trades with the fill price are necessary for LIMIT fill to happen in backtesting
#0 - optimistic, every knot high will fill the order
#N - N consecutive trades required
#not impl.yet
#minimum is 1, na alpace live to vetsinou vychazi 7-8 u BAC, je to hodne podobne tomu, nez je cena překonaná pul centu. tzn. 7-8 a nebo FillCondition.SLOW
BT_FILL_CONS_TRADES_REQUIRED = 2
#during bt trade execution logs X-surrounding trades of the one that triggers the fill
BT_FILL_LOG_SURROUNDING_TRADES = 10
#fill condition for limit order in bt
# fast - price has to be equal or bigger <=
# slow - price has to be bigger <
BT_FILL_CONDITION_BUY_LIMIT = FillCondition.SLOW
BT_FILL_CONDITION_SELL_LIMIT = FillCondition.SLOW
#backend counter of api requests
COUNT_API_REQUESTS = False
# ilog lvls = 0,1 - 0 debug, 1 info
ILOG_SAVE_LEVEL_FROM  = 1
#currently only prod server has acces to LIVE
PROD_SERVER_HOSTNAMES = ['tradingeastcoast','David-MacBook-Pro.local'] #,'David-MacBook-Pro.local'
TEST_SERVER_HOSTNAMES = ['tradingtest'] 

""""
LATENCY DELAYS for LIVE eastcoast
.000 trigger - last_trade_time (.4246266)
+.020 vstup do strategie a BUY (.444606)
+.023 submitted (.469198)
+.008    filled (.476695552)
+.023   fill not(.499888)
"""
BT_DELAYS = {
    "trigger_to_strat": 0.020,
    "strat_to_sub": 0.023,
    "sub_to_fill": 0.008,
    "fill_to_not": 0.023,
    #doplnit dle live
    "limit_order_offset": 0,
}

#cfh.config_handler.get_val('BT_DELAYS','trigger_to_strat')