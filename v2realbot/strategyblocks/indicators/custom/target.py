from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
from v2realbot.strategy.base import StrategyState
from v2realbot.indicators.indicators import ema, natr, roc
from v2realbot.strategyblocks.indicators.helpers import get_source_series
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
    window_length_unit= safe_get(params, "window_length_unit", "bar")    
    no_move_threshold= safe_get(params, "no_move_threshold", 0.033)
    pct_change_full_scale = safe_get(params, "pct_change_full_scale", 0.1) #pct change that is considered for full scaling factor
    move_base= safe_get(params, "move_base", 0.2)  #base output value for move up/down, to this value scaling factor is added based on magnitude of change
    scaling_factor= safe_get(params, "scaling_factor", 0.8)# This represents the maximum additional value to be added to 0.5, based on steepness of the move

    if window_length_value is None or source is None:
        return -2, "window_length_value/source required"

    state.ilog(lvl=0,e=f"INSIDE {name} {funcName}", **params)

    #0 = no move value
    val = 0

    future_price = float(source_series[-1])

    try:
        current_price = float(source_series[-window_length_value])
    except IndexError:
        return 0, val
    
    upper_move_threshold = add_pct(no_move_threshold, current_price)
    lower_move_threshold = add_pct(-no_move_threshold, current_price)
    
    #no move
    if lower_move_threshold <= future_price <= upper_move_threshold:
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
        magnitude_val = calculate_factor(current_price, future_price)
        return 0, move_base + magnitude_val

    #price is bigger than threshold
    if lower_move_threshold > future_price:
        magnitude_val = calculate_factor(current_price, future_price)
        return 0, - move_base - magnitude_val


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