from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
from v2realbot.strategy.base import StrategyState
from v2realbot.indicators.indicators import ema, natr, roc
from v2realbot.strategyblocks.indicators.helpers import get_source_series
from rich import print as printanyway
from traceback import format_exc
import numpy as np
from collections import defaultdict

#abs/rel divergence of two indicators
def divergence(state, params, name):
    funcName = "indicatorDivergence"
    source1 = safe_get(params, "source1", None)
    source1_series = get_source_series(state, source1)
    source2 = safe_get(params, "source2", None)
    source2_series = get_source_series(state, source2)
    mode = safe_get(params, "type")
    state.ilog(lvl=0,e=f"INSIDE {name} {funcName} {source1=} {source2=} {mode=}", **params)
    val = 0
    if mode == "abs":
        val =  round(abs(float(source1_series[-1]) - float(source2_series[-1])),4)
    elif mode == "absn":
        val =  round((abs(float(source1_series[-1]) - float(source2_series[-1])))/float(source1_series[-1]),4)
    elif mode == "rel":
        val =  round(float(source1_series[-1]) - float(source2_series[-1]),4)
    elif mode == "reln": #div = a+b   /   a-b  will give value between -1 and 1
        val =  round((float(source1_series[-1]) - float(source2_series[-1]))/(float(source1_series[-1])+float(source2_series[-1])),4)
    elif mode == "pctabs":
        val = pct_diff(num1=float(source1_series[-1]),num2=float(source2_series[-1]), absolute=True)
    elif mode == "pct":
        val = pct_diff(num1=float(source1_series[-1]),num2=float(source2_series[-1]))
    return 0, val

#model - naloadovana instance modelu
#seq - sekvence pro vstup







