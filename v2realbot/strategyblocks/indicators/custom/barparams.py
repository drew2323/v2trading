
from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
from v2realbot.strategy.base import StrategyState
from v2realbot.indicators.indicators import ema, natr, roc
from v2realbot.strategyblocks.indicators.helpers import get_source_series
from rich import print as printanyway
from traceback import format_exc
import numpy as np
import math
from collections import defaultdict

#indicator allowing to be based on any bar parameter (index, high,open,close,trades,volume, etc.)
def barparams(state, params, name, returns):
    funcName = "barparams"
    if params is None:
        return -2, "params required"
    source = safe_get(params, "source", None)
    lookback = safe_get(params, "lookback", 1)
    mod = safe_get(params, "mod", "no")
    if source is None:
        return -2, "source required"

    try:
        source_series = get_source_series(state, source)
        match mod:
            case "logreturn":
                val = math.log(source_series[-lookback]/source_series[-lookback-1])
            case _:
                val = source_series[-lookback]

        return 0, val
        #return 0, state.bars[source][-1]
    except Exception as e:
        return -2, str(e)+format_exc()
