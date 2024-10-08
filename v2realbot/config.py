from alpaca.data.enums import DataFeed
from v2realbot.enums.enums import Mode, Account, FillCondition
from appdirs import user_data_dir
from pathlib import Path
import os
from collections import defaultdict
from dotenv import load_dotenv
# Global flag to track if the ml module has been imported (solution for long import times of tensorflow)
#the first occurence of using it will load it globally
_ml_module_loaded = False

#directory for generated images and basic reports
MEDIA_DIRECTORY = Path(__file__).parent.parent.parent / "media"
VBT_DOC_DIRECTORY = Path(__file__).parent.parent.parent / "vbt-doc" #directory for vbt doc
RUNNER_DETAIL_DIRECTORY = Path(__file__).parent.parent.parent / "runner_detail"

#location of strat.log - it is used to fetch by gui
LOG_PATH = Path(__file__).parent.parent
LOG_FILE = Path(__file__).parent.parent / "strat.log"
JOB_LOG_FILE = Path(__file__).parent.parent / "job.log"
DOTENV_DIRECTORY = Path(__file__).parent.parent.parent
ENV_FILE = DOTENV_DIRECTORY / '.env'


#stratvars that cannot be changed in gui
STRATVARS_UNCHANGEABLES = ['pendingbuys', 'blockbuy', 'jevylozeno', 'limitka']
DATA_DIR = user_data_dir("v2realbot", False)
MODEL_DIR = Path(DATA_DIR)/"models"
#BT DELAYS
#profiling
PROFILING_NEXT_ENABLED = False
PROFILING_OUTPUT_DIR = DATA_DIR

#NALOADUJEME DOTENV ENV VARIABLES
if load_dotenv(ENV_FILE, verbose=True) is False:
    print(f"Error loading.env file {ENV_FILE}. Now depending on ENV VARIABLES set externally.")
else:
    print(f"Loaded env variables from file {ENV_FILE}")

#WIP - FILL CONFIGURATION CLASS FOR BACKTESTING
class BT_FILL_CONF:
    """"
    Trida pro konfiguraci backtesting fillu pro dany symbol, pokud neexistuje tak fallback na obecny viz vyse-

    MOžná udělat i separátní profil PAPER/LIVE. Nějak vymyslet profily a jejich správa.
    """
    def __init__(self, symbol, BT_FILL_CONS_TRADES_REQUIRED, BT_FILL_CONDITION_BUY_LIMIT, BT_FILL_CONDITION_SELL_LIMIT,BT_FILL_PRICE_MARKET_ORDER_PREMIUM):
        self.symbol = symbol
        self.BT_FILL_CONS_TRADES_REQUIRED = BT_FILL_CONS_TRADES_REQUIRED
        self.BT_FILL_CONDITION_BUY_LIMIT=BT_FILL_CONDITION_BUY_LIMIT
        self.BT_FILL_CONDITION_SELL_LIMIT=BT_FILL_CONDITION_SELL_LIMIT
        self.BT_FILL_PRICE_MARKET_ORDER_PREMIUM=BT_FILL_PRICE_MARKET_ORDER_PREMIUM

class Keys:
    def __init__(self, api_key, secret_key, paper, feed) -> None:
        self.API_KEY = api_key
        self.SECRET_KEY = secret_key
        self.PAPER = paper
        self.FEED = feed

# podle modu (PAPER, LIVE) vrati objekt
# obsahujici klice pro pripojeni k alpace - používá se pro Trading API a order updates websockets (pristupy relevantni per strategie)
#pro real time data se bere LIVE_DATA_API_KEY, LIVE_DATA_SECRET_KEY, LIVE_DATA_FEED nize - jelikoz jde o server wide nastaveni
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

WEB_API_KEY=os.environ.get('WEB_API_KEY')

#PRIMARY PAPER
ACCOUNT1_PAPER_API_KEY = os.environ.get('ACCOUNT1_PAPER_API_KEY')
ACCOUNT1_PAPER_SECRET_KEY = os.environ.get('ACCOUNT1_PAPER_SECRET_KEY')
ACCOUNT1_PAPER_MAX_BATCH_SIZE = 1
ACCOUNT1_PAPER_PAPER = True
#ACCOUNT1_PAPER_FEED = DataFeed.SIP

# Load the data feed type from environment variable
data_feed_type_str = os.environ.get('ACCOUNT1_PAPER_FEED', 'iex')  # Default to 'sip' if not set

# Convert the string to DataFeed enum
try:
    ACCOUNT1_PAPER_FEED = DataFeed(data_feed_type_str)
except ValueError:
    # Handle the case where the environment variable does not match any enum member
    print(f"Invalid data feed type: {data_feed_type_str} in ACCOUNT1_PAPER_FEED defaulting to 'iex'")
    ACCOUNT1_PAPER_FEED = DataFeed.SIP

#PRIMARY LIVE
ACCOUNT1_LIVE_API_KEY = os.environ.get('ACCOUNT1_LIVE_API_KEY')
ACCOUNT1_LIVE_SECRET_KEY = os.environ.get('ACCOUNT1_LIVE_SECRET_KEY')
ACCOUNT1_LIVE_MAX_BATCH_SIZE = 1
ACCOUNT1_LIVE_PAPER = False
#ACCOUNT1_LIVE_FEED = DataFeed.SIP

# Load the data feed type from environment variable
data_feed_type_str = os.environ.get('ACCOUNT1_LIVE_FEED', 'iex')  # Default to 'sip' if not set

# Convert the string to DataFeed enum
try:
    ACCOUNT1_LIVE_FEED = DataFeed(data_feed_type_str)
except ValueError:
    # Handle the case where the environment variable does not match any enum member
    print(f"Invalid data feed type: {data_feed_type_str} in ACCOUNT1_LIVE_FEED defaulting to 'iex'")
    ACCOUNT1_LIVE_FEED = DataFeed.IEX

#SECONDARY PAPER - Martin
ACCOUNT2_PAPER_API_KEY = os.environ.get('ACCOUNT2_PAPER_API_KEY')
ACCOUNT2_PAPER_SECRET_KEY = os.environ.get('ACCOUNT2_PAPER_SECRET_KEY')
ACCOUNT2_PAPER_MAX_BATCH_SIZE = 1
ACCOUNT2_PAPER_PAPER = True
#ACCOUNT2_PAPER_FEED = DataFeed.IEX

# Load the data feed type from environment variable
data_feed_type_str = os.environ.get('ACCOUNT2_PAPER_FEED', 'iex')  # Default to 'sip' if not set

# Convert the string to DataFeed enum
try:
    ACCOUNT2_PAPER_FEED = DataFeed(data_feed_type_str)
except ValueError:
    # Handle the case where the environment variable does not match any enum member
    print(f"Invalid data feed type: {data_feed_type_str} in ACCOUNT2_PAPER_FEED defaulting to 'iex'")
    ACCOUNT2_PAPER_FEED = DataFeed.IEX


#SECONDARY LIVE - Martin
# ACCOUNT2_LIVE_API_KEY = os.environ.get('ACCOUNT2_LIVE_API_KEY')
# ACCOUNT2_LIVE_SECRET_KEY = os.environ.get('ACCOUNT2_LIVE_SECRET_KEY')
# ACCOUNT2_LIVE_MAX_BATCH_SIZE = 1
# ACCOUNT2_LIVE_PAPER = True
# #ACCOUNT2_LIVE_FEED = DataFeed.IEX

# # Load the data feed type from environment variable
# data_feed_type_str = os.environ.get('ACCOUNT2_LIVE_FEED', 'iex')  # Default to 'sip' if not set

# # Convert the string to DataFeed enum
# try:
#     ACCOUNT2_LIVE_FEED = DataFeed(data_feed_type_str)
# except ValueError:
#     # Handle the case where the environment variable does not match any enum member
#     print(f"Invalid data feed type: {data_feed_type_str} in ACCOUNT2_LIVE_FEED defaulting to 'iex'")
#     ACCOUNT2_LIVE_FEED = DataFeed.IEX

#zatim jsou LIVE_DATA nastaveny jako z account1_paper
LIVE_DATA_API_KEY = ACCOUNT1_PAPER_API_KEY
LIVE_DATA_SECRET_KEY = ACCOUNT1_PAPER_SECRET_KEY
#LIVE_DATA_FEED je nastaveny v config_handleru

class KW:
    activate: str = "activate"
    dont_go: str = "dont_go"
    dont_exit: str = "dont_exit"
    go: str = "go"
    # wip addsize: str = "addsize"
    exit: str = "exit"
    #wip exitsize: str = "exitsize"
    exitadd: str = "exitadd"
    reverse: str = "reverse"
    #exitaddsize: str = "exitaddsize"
    slreverseonly: str = "slreverseonly"
    #klicove slovo pro Indikatory
    change_val: str = "change_val"
