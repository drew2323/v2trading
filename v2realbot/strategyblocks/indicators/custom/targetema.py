from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
from v2realbot.strategy.base import StrategyState
from v2realbot.indicators.indicators import ema, natr, roc
from v2realbot.strategyblocks.indicators.helpers import get_source_series, find_index_optimized
from rich import print as printanyway
from traceback import format_exc
import numpy as np
from collections import defaultdict

#target algorithm for ML
""""
GOLDEN CROSS
Target algorithm. 

if divergence of ema_slow and source is above/below threshold it labels the area as 1 or -1.
Where
- start is last crossing of source with ema and 
- end is the current position -1
"""""
def targetema(state, params, name, returns):
    try:
        funcName = "targetema"
        window_length_value = safe_get(params, "window_length_value", None)
        window_length_unit= safe_get(params, "window_length_unit", "position")

        downtrend, notrend, uptrend = safe_get(params, "output_vals", [-1,0,1])
        source = safe_get(params, "source", None)
        source_series = get_source_series(state, source, True)
        ema_slow = safe_get(params, "ema_slow", None)
        ema_slow_series = get_source_series(state, ema_slow, True)
        ema_div = safe_get(params, "ema_div", None)
        ema_div_series = get_source_series(state, ema_div)
        div_pos_threshold = safe_get(params, "div_pos_threshold", None)
        div_neg_threshold = safe_get(params, "div_neg_threshold", None)
        #mezi start a end price musi byt tento threshold
        req_min_pct_chng = float(safe_get(params, "req_min_pct_chng", 0.04))   #required PCT chng

        #kvalifikuji divergence s cenou jen vyssi nez posledni (pozor pri reverse trendu musime resetovat)
        if div_pos_threshold is not None and ema_div_series[-1] > div_pos_threshold and float(source_series[-1])>params.get("last_pos",0): 

            # Finding first index where vwap is smaller than ema_slow (last cross)
            idx = np.where(source_series < ema_slow_series)[0]

            #there is no cross yet (beginning of the market)
            #TODO jeste to zbytecne protahuje tento signal az do doby protnuti (prvni signal je delsi a obcas zasahuje do konzolidace)
            if idx.size ==0:
                #if price exists lower than qualifying price
                idx = np.where(source_series*(1 + req_min_pct_chng/100) < source_series[-1])[0]

                if idx.size == 0:
                    pass
                else:
                    #we are qualified, oznacime
                    first_idx = -len(source_series) + idx[-1]
                    #fill target list with 1 from crossed point until last
                    target_list = get_source_series(state, name)
                    target_list[first_idx:] = [uptrend] * abs(first_idx)
                    params["last_pos"] = float(source_series[-1])
                return 0, notrend
            #idx.size > 0:
            else:
                #if the value on the cross has min_pct from current price to qualify
                qual_price = source_series[idx[-1]] * (1 + req_min_pct_chng/100)
                qualified = qual_price < source_series[-1]
                if qualified:
                    first_idx = -len(source_series) + idx[-1]
                    #fill target list with 1 from crossed point until last
                    target_list = get_source_series(state, name)
                    target_list[first_idx:] = [uptrend] * abs(first_idx)
                    params["last_pos"] = float(source_series[-1])
                return 0, notrend
        elif div_neg_threshold is not None and ema_div_series[-1] < div_neg_threshold and float(source_series[-1])<params.get("last_neg",99999999): 

            # Finding first index where vwap is smaller than ema_slow (last cross) and price at cross must respect min PCT threshold
            idx = np.where(source_series > ema_slow_series)[0]
            #there is no cross yet (beginning of the market), 
            if idx.size ==0:
                #if price exists higher than qualifying price
                idx = np.where(source_series*(1 - req_min_pct_chng/100) > source_series[-1])[0]

                if idx.size == 0:
                    pass
                else:
                    #we are qualified, oznacime
                    first_idx = -len(source_series) + idx[-1]
                    #fill target list with 1 from crossed point until last
                    target_list = get_source_series(state, name)
                    target_list[first_idx:] = [downtrend] * abs(first_idx)
                    params["last_neg"] = float(source_series[-1])
                return 0, notrend
            #idx.size < 0:
            else:
                #porovname zda mezi aktualni cenou a cenou v crossu je dostatecna pro kvalifikaci
                qual_price = source_series[idx[-1]] * (1 - req_min_pct_chng/100)
                qualified = qual_price>source_series[-1]
                if qualified:
                    first_idx = -len(source_series) + idx[-1]
                    #fill target list with 1 from crossed point until last
                    target_list = get_source_series(state, name)
                    target_list[first_idx:] = [downtrend] * abs(first_idx)
                    params["last_neg"] = float(source_series[-1])
                return 0, notrend
            
        #test resetujeme nejvyssi body po uplynuti 20 pozic od trendu (tim konci ochranne okno)
        # Finding the first 1 from backwards and its position
        target_numpy = get_source_series(state, name, True)
        position = np.where(target_numpy[::-1] == uptrend)[0][0] + 1
        if position % 20 == 0:
            params["last_pos"] = 0
        position = np.where(target_numpy[::-1] == downtrend)[0][0] + 1
        if position % 20 == 0:
            params["last_neg"] = 99999999

        return 0, notrend
    #pri chybe vracime explciitne notrend (muze mit jinou hodnotu nez 0)
    except Exception as e:
        state.ilog(lvl=1,e=f"IND ERROR {name} necháváme původní", message=str(e)+format_exc())
        return 0, notrend

def add_pct(pct, value):
    """
    Add a percentage to a value. If pct is negative it is subtracted.
    print(add_pct(1,100))
    
    Parameters:
    pct (float): The percentage to add (e.g., 10 for 10%).
    value (float): The original value.

    Returns:
    float: The new value after adding the percentage.
    """
    return value * (1 + pct / 100)
