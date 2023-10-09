from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff
from v2realbot.strategy.base import StrategyState
from v2realbot.indicators.indicators import ema, natr, roc
from v2realbot.strategyblocks.indicators.helpers import get_source_series
from rich import print as printanyway
from traceback import format_exc
from v2realbot.ml.ml import ModelML
import numpy as np
from collections import defaultdict

#WIP - 
#testing custom indicator CODE
def opengap(state, params):
    funcName = "opengap"
    param1 = safe_get(params, "param1")
    param2 = safe_get(params, "param2")
    state.ilog(lvl=0,e=f"INSIDE {funcName} {param1=} {param2=}", **params)
    last_close = 28.45
    today_open = 29.45
    val = pct_diff(last_close, today_open)
    return 0, val
    #random.randint(10, 20)