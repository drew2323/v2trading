from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
from v2realbot.strategy.base import StrategyState
from v2realbot.indicators.indicators import ema, natr, roc
from v2realbot.strategyblocks.indicators.helpers import get_source_series
from rich import print as printanyway
from traceback import format_exc
from v2realbot.ml.ml import ModelML
import numpy as np
from collections import defaultdict

#vstupem je bud indicator nebo bar parametr
#na tomto vstupu dokaze provest zakladni statisticke funkce pro subpole X hodnot zpatky
#podporovane functions: min, max, mean
def basestats(state, params):
    funcName = "basestats"
    #name of indicator or 
    source = safe_get(params, "source", None)
    lookback = safe_get(params, "lookback", None)
    func = safe_get(params, "function", None)

    source_dict = defaultdict(list)
    source_dict[source] = get_source_series(state, source)

    if lookback is None:
        source_array = source_dict[source]
    else:
        try:
            source_array = source_dict[source][-lookback-1:]
        except IndexError:
            source_array = source_dict[source]

    if func == "min":
        val = np.amin(source_array)
    elif func == "max":
        val = np.amax(source_array)
    elif func == "mean":
        val = np.mean(source_array)
    else:
        return -2, "wrong function"

    return 0, val
    
