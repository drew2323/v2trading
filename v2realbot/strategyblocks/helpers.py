from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
from v2realbot.utils.directive_utils import get_conditions_from_configuration
from v2realbot.common.model import SLHistory
from v2realbot.config import KW
from uuid import uuid4
from datetime import datetime
#import random
#from icecream import install, ic
from rich import print as printanyway
from threading import Event
import os
from traceback import format_exc

def normalize_tick(state, data, tick: float, price: float = None, return_two_decimals: bool = False):
    """
    In stratvars directives the values can be either in ticks, relative ticks based on base price or in percentage.

    This function converts all those types to absolute values considering the type and current price.
    Returns absolute value of tick with required precision.

    How are each variants recognized:
    - ticks - absolute ticks regargless of asset price
        - When: value is positive and normalize_ticks = False
    
    - relative ticks based on base price (number of ticks in relation of base price)
        - When: value is positive, normalize_ticks = True and normalized_base_price is set (default is 30)
        - Returns relative absolute tick based on base price vs current price.
        - When price is under base price, it considers price = base price

    - relative percentages from the asset price
        - When: value is negative
        - Returns percentage from the current price

    Applies to directive like profit, maxprofit, SL etc. 
    """
    #nemusime dodavat cenu, bereme aktualni
    if price is None:
        price = data["close"]

    normalize_ticks = safe_get(state.vars, "normalize_ticks",False)
    normalized_base_price = safe_get(state.vars, "normalized_base_price",30)

    if tick > 0 and normalize_ticks:
        if price<normalized_base_price:
            return tick
        else:
            #ratio of price vs base price
            ratio = price/normalized_base_price
            normalized_tick = ratio*tick
        return price2dec(normalized_tick) if return_two_decimals else normalized_tick
    elif tick < 0:
        value = abs(tick) * price / 100.0
        return price2dec(value) if return_two_decimals else value
    else:
        return tick
