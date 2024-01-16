from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
from v2realbot.strategy.base import StrategyState
from v2realbot.indicators.indicators import ema, natr, roc
from v2realbot.strategyblocks.indicators.helpers import get_source_series, find_index_optimized
from rich import print as printanyway
from traceback import format_exc
import numpy as np
from collections import defaultdict

#rate of change - last value of source indicator vs lookback value of lookback_priceline indicator
def slope(state, params, name, returns):
    funcName = "slope"
    source = safe_get(params, "source", None)
    source_series = get_source_series(state, source) 
        
    lookback_unit = safe_get(params, "lookback_unit", "position") 
    lookback = safe_get(params, "lookback", 5)
    lookback_priceline = safe_get(params, "lookback_priceline", None) #bars|close
    lookback_series = get_source_series(state, lookback_priceline) 
    #ukládáme si do cache incializaci
    cache = safe_get(params, "CACHE", None)

    match lookback_unit:
        case "position":
            try:
                lookbackprice = lookback_series[-lookback-1]
                lookbacktime = state.bars.updated[-lookback-1]
            except IndexError:
                max_delka = len(lookback_series)
                lookbackprice =lookback_series[-max_delka]
                lookbacktime = state.bars.updated[-max_delka]
        case "second":
            if state.cache.get(name, None) is None: 
                #předpokládáme, že lookback_priceline je ve formě #bars|close
                #abychom ziskali relevantní time
                split_index = lookback_priceline.find("|")
                if split_index == -1:
                    return -2, "for time it is required in format bars|close"
                dict_name = lookback_priceline[:split_index]
                time_series = getattr(state, dict_name)["time"]
                state.cache[name]["time_series"] = time_series         
            else:
                time_series = state.cache[name]["time_series"]
            lookback_idx = find_index_optimized(time_list=time_series, seconds=lookback)
            lookbackprice = lookback_series[lookback_idx]
            lookbacktime = time_series[lookback_idx]   
             

    #výpočet úhlu - a jeho normalizace
    currval = source_series[-1]
    slope = ((currval - lookbackprice)/abs(lookbackprice))*100
    #slope = round(slope, 4)

    state.ilog(lvl=1,e=f"INSIDE {name}:{funcName} {slope} {source=} {lookback=}", currval_source=currval, lookbackprice=lookbackprice, lookbacktime=lookbacktime, **params)
    return 0, slope
