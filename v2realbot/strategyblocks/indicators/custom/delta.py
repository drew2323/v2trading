from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
from v2realbot.strategy.base import StrategyState
from v2realbot.indicators.indicators import ema, natr, roc
from v2realbot.strategyblocks.indicators.helpers import get_source_series
from rich import print as printanyway
from traceback import format_exc
from v2realbot.ml.ml import ModelML
import numpy as np
from collections import defaultdict

#strength, absolute change of parameter between current value and lookback value (n-past)
#used for example to measure unusual peaks
def delta(state, params):
    funcName = "delta"
    source = safe_get(params, "source", None)
    lookback = safe_get(params, "lookback",1)
    source_series = get_source_series(state, source)          

    lookbackval = source_series[-lookback-1]
    currval = source_series[-1]
    delta = currval - lookbackval

    state.ilog(lvl=1,e=f"INSIDE {funcName} {delta} {source=} {lookback=}", currval=currval, lookbackval=lookbackval, **params)
    return 0, delta
