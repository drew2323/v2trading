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
    elif func == "var":
        data = np.array(source_array)
        mean_value = np.mean(data)
        # Calculate the variance of the data
        val = np.mean((data - mean_value) ** 2)
    elif func == "angle":
        delka_pole = len(source_array)
        if delka_pole < 2:
            return 0,0

        x = np.arange(delka_pole)
        y = np.array(source_array)

        # Fit a linear polynomial to the data
        coeffs = np.polyfit(x, y, 1)

        # Calculate the angle in radians angle_rad
        val = np.arctan(coeffs[0]) * 1000

        # Convert the angle to degrees angle_deg
        #angle_deg = np.degrees(angle_rad)
        
        # Normalize the degrees between -1 and 1
        #val = 2 * (angle_deg / 180) - 1
    elif func =="stdev":
        val = np.std(source_array)
    else:
        return -2, "wrong function"

    return 0, val
    
