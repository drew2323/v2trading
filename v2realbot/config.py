from alpaca.data.enums import DataFeed
from v2realbot.enums.enums import Mode, Account, FillCondition
from appdirs import user_data_dir

#no print in console
QUIET_MODE = False
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
#stratvars that cannot be changed in gui
STRATVARS_UNCHANGEABLES = ['pendingbuys', 'blockbuy', 'jevylozeno', 'limitka']
DATA_DIR = user_data_dir("v2realbot")
#BT DELAYS
  
""""
LATENCY DELAYS for LIVE eastcoast
.000 trigger - last_trade_time (.4246266)
+.020 vstup do strategie a BUY (.444606)
+.023 submitted (.469198)
+.008    filled (.476695552)
+.023   fill not(.499888)
"""
#TODO změnit názvy delay promennych vystizneji a obecneji
class BT_DELAYS:
    trigger_to_strat: float = 0.020
    strat_to_sub: float = 0.023
    sub_to_fill: float = 0.008
    fill_to_not: float = 0.023
    #doplnit dle live
    limit_order_offset: float = 0
 
class Keys:
    def __init__(self, api_key, secret_key, paper, feed) -> None:
        self.API_KEY = api_key
        self.SECRET_KEY = secret_key
        self.PAPER = paper
        self.FEED = feed

# podle modu (PAPER, LIVE) vrati objekt
# obsahujici klice pro pripojeni k alpace
def get_key(mode: Mode, account: Account):
    if mode not in [Mode.PAPER, Mode.LIVE]:
        print("has to be LIVE or PAPER only")
        return None
    dict = globals()
    try:
        API_KEY = dict[str.upper(str(account.value)) + "_" + str.upper(str(mode.value)) + "_API_KEY" ]
        SECRET_KEY = dict[str.upper(str(account.value)) + "_" + str.upper(str(mode.value)) + "_SECRET_KEY" ]
        PAPER = dict[str.upper(str(account.value)) + "_" + str.upper(str(mode.value)) + "_PAPER" ]
        FEED = dict[str.upper(str(account.value)) + "_" + str.upper(str(mode.value)) + "_FEED" ]
        return Keys(API_KEY, SECRET_KEY, PAPER, FEED)
    except KeyError:
        print("Not valid combination to get keys for", mode, account)
        return 0

#strategy instance main loop heartbeat
HEARTBEAT_TIMEOUT=5

WEB_API_KEY="david"

#PRIMARY PAPER
ACCOUNT1_PAPER_API_KEY = 'PKGGEWIEYZOVQFDRY70L'
ACCOUNT1_PAPER_SECRET_KEY = 'O5Kt8X4RLceIOvM98i5LdbalItsX7hVZlbPYHy8Y'
ACCOUNT1_PAPER_MAX_BATCH_SIZE = 1
ACCOUNT1_PAPER_PAPER = True
ACCOUNT1_PAPER_FEED = DataFeed.SIP

#PRIMARY LIVE
ACCOUNT1_LIVE_API_KEY = 'AKB5HD32LPDZC9TPUWJT'
ACCOUNT1_LIVE_SECRET_KEY = 'Xq1wPSNOtwmlMTAd4cEmdKvNDgfcUYfrOaCccaAs'
ACCOUNT1_LIVE_MAX_BATCH_SIZE = 1
ACCOUNT1_LIVE_PAPER = False
ACCOUNT1_LIVE_FEED = DataFeed.SIP

#SECONDARY PAPER
ACCOUNT2_PAPER_API_KEY = 'PKQEAAJTVC72SZO3CT3R'
ACCOUNT2_PAPER_SECRET_KEY = 'mqdftzGJlJdvUjdsuQynAURCHRwAI0a8nhJy8nyz'
ACCOUNT2_PAPER_MAX_BATCH_SIZE = 1
ACCOUNT2_PAPER_PAPER = True
ACCOUNT2_PAPER_FEED = DataFeed.IEX

