from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists, get_max_anchored_lookback
from v2realbot.strategy.base import StrategyState
from v2realbot.indicators.indicators import ema, natr, roc
from v2realbot.strategyblocks.indicators.helpers import get_source_series
from rich import print as printanyway
from traceback import format_exc
import numpy as np
from collections import defaultdict

#strength, absolute change of parameter between current value and lookback value (n-past)
#used for example to measure unusual peaks
def delta(state, params, name, returns):
    funcName = "delta"
    source = safe_get(params, "source", None)
    lookback = safe_get(params, "lookback",1)
    anchor = safe_get(params, "anchor",None)
    lookback = min(lookback, get_max_anchored_lookback(state, anchor) if anchor is not None else lookback)

    source_series = get_source_series(state, source)          

    lookbackval = source_series[-lookback-1]
    currval = source_series[-1]
    delta = currval - lookbackval

    state.ilog(lvl=1,e=f"INSIDE {name}:{funcName} {delta} {source=} {lookback=}", currval=currval, lookbackval=lookbackval, **params)
    return 0, delta
