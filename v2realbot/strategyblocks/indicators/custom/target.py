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
v teto funkci bere posledni cenu (future price) porovname s cenou X baru zpet(current_price) a vysledek ulozime jako hodnotu X baru zpet

source - target priceline
window_length_value = 3 #delka okna ve kterem pocitame target (current_price and future_price)
window_length_unit = "bar", "time" #zatim jen v barech
no_move_threshold = 0.033 #zmene v procentech povazovana za no move, v % (1tick pri cene 30 je 0.033%), pripadne rozlisit na _upper and _lower
pct_change_full_scale = #pct change that is considered 1, used in scaler to determine target_value based on price change


TODO musi se signal trochu tahnout az kde se opravdu rozjede, aby si to model spojil
"""""
def target(state, params, name):
    funcName = "target"
    source = safe_get(params, "source", "vwap")
    source_series = get_source_series(state, source)
    #zatim podporovano jen bar - dokud nepridame o level vyse do "custom" save_to_past na urovni casu
    window_length_value = safe_get(params, "window_length_value", None)
    window_length_unit= safe_get(params, "window_length_unit", "position")
    smoothing_window= int(safe_get(params, "smoothing_window", 1))   #pocet jednotek casu, kdy se signal drzi (zatm jen pro cas, TODO pro pozice)
    no_move_threshold= safe_get(params, "no_move_threshold", 0.033)
    pct_change_full_scale = safe_get(params, "pct_change_full_scale", 0.1) #pct change that is considered for full scaling factor
    move_base= safe_get(params, "move_base", 0.2)  #base output value for move up/down, to this value scaling factor is added based on magnitude of change
    scaling_factor= safe_get(params, "scaling_factor", 0.8)# This represents the maximum additional value to be added to 0.5, based on steepness of the move
    #ukládáme si do cache incializaci
    lookback_idx = None
    #workaround for state
    #params["last_activated_up"] = None
    #params["last_activated_down"] = None
    
    if window_length_value is None or source is None:
        return -2, "window_length_value/source required"

    state.ilog(lvl=0,e=f"INSIDE {name} {funcName}", **params)

    #0 = no move value
    val = 0

    future_price = float(source_series[-1])

    #LOOKUP of current_price (price in the past)
    if window_length_unit == "position":
        try:
            current_price = float(source_series[-window_length_value])
        except IndexError:
            return 0, val
    #seconds type, predpoklada opet source v kompletnim tvaru a predpoklada save_to_past typu seconds
    else:
        if state.cache.get(name, None) is None:
            split_index = source.find("|")
            if split_index == -1:
                return -2, "for second based window length, source is required in format bars|close"
            dict_name = source[:split_index]
            if dict_name == "bars":
                #u baru je time v datetime, proto bereme udpated
                time_series = getattr(state, dict_name)["updated"]
            else:
                time_series = getattr(state, dict_name)["time"]
            state.cache[name]["time_series"] = time_series
        else:
            time_series = state.cache[name]["time_series"]
        
        lookback_idx = find_index_optimized(time_list=time_series, seconds=window_length_value)
        current_price = source_series[lookback_idx]        
         
    upper_move_threshold = add_pct(no_move_threshold, current_price)
    lower_move_threshold = add_pct(-no_move_threshold, current_price)
    
    #5 a 7
    def fill_skipped_indx(pastidx, curridx):
        #mame mezi indexy mezeru, iterujeme mezi temito a doplnime predchozi hodnoty primo do indikatoru
        if pastidx + 1 < curridx:
            for i in range(pastidx+1, curridx):
                ind_dict = get_source_series(state, name)
                ind_dict[i] = ind_dict[i-1]

    if params.get("last_returned_idx", None) is not None:
        #pokud je mezi poslednim indexem a aktualnim dira pak je vyplnime predchozi hodnotou
        fill_skipped_indx(params["last_returned_idx"],lookback_idx)

    #no move
    if lower_move_threshold <= future_price <= upper_move_threshold:
        #SMOOTHING WINDOW (3 secs) - workaround of state
        #pokud no move, ale jsme 2 sekundy po signálu tak vracíme predchozi hodnotu (realizováno vrácním -2)
        #zatim pouze pro casove okno
        #po osvedceni do conf
        if params.get("last_activated_up",None) is not None:
            #jsme v okno, vracime predchozi hodnotu
            last_plus_window = float(time_series[params["last_activated_up"]]) + smoothing_window
            if last_plus_window > float(time_series[lookback_idx]):
                val = params["last_returned_val"]
            #okno prekroceno, nulujeme a vracime 0
            else:
                params["last_activated_up"] = None

        elif params.get("last_activated_down",None) is not None:
            last_plus_window = float(time_series[params["last_activated_down"]]) + smoothing_window
            if last_plus_window > float(time_series[lookback_idx]):
                val = params["last_returned_val"]
            else:
                params["last_activated_down"] = None
        params["last_returned_val"] = val
        params["last_returned_idx"] = lookback_idx
        return 0, val

    #calculates weight based on magnitude of change
    def calculate_factor(current_price, future_price):
        #podle vzdalenosti od no_move_thresholdu vratime hodnotu
        # pct_change_full_scale - pct that is considered maximum for scaling_factor value above
        current_pct_delta = abs(pct_delta(current_price, future_price)) #aktuální pct gap mezi curr a price
        magnitude_val = min(current_pct_delta / pct_change_full_scale, 1) * scaling_factor
        return magnitude_val

    #price is bigger than threshold
    if upper_move_threshold < future_price:
        params["last_activated_down"] = None
        magnitude_val = calculate_factor(current_price, future_price)
        params["last_activated_up"] = lookback_idx
        params["last_returned_val"] = move_base + magnitude_val
        params["last_returned_idx"] = lookback_idx
        return 0, params["last_returned_val"]

    #price is bigger than threshold
    if lower_move_threshold > future_price:
        params["last_activated_up"] = None
        magnitude_val = calculate_factor(current_price, future_price)
        params["last_activated_down"] = lookback_idx
        params["last_returned_val"] = - move_base - magnitude_val
        params["last_returned_idx"] = lookback_idx
        return 0, params["last_returned_val"]


def pct_delta(base, second_number):
    """
    Calculate the percentage difference between the base and the second number.

    Parameters:
    base (float): The base value.
    second_number (float): The second number to compare against the base.

    Returns:
    float: The percentage difference (delta) between the second number and the base.
    """
    if base == 0:
        raise ValueError("Base cannot be zero.")

    return ((second_number - base) / base) * 100

def add_pct(pct, value):
    """
    Add a percentage to a value. If pct is negative it is subtracted.

    Parameters:
    pct (float): The percentage to add (e.g., 10 for 10%).
    value (float): The original value.

    Returns:
    float: The new value after adding the percentage.
    """
    return value * (1 + pct / 100)


if __name__ == '__main__':
    print(add_pct(1,100))
    print(add_pct(-1,100))
    print(pct_delta(100,102))
    print(pct_delta(100,98))