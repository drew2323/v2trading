from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
from v2realbot.strategy.base import StrategyState
import v2realbot.indicators.moving_averages as mi
from v2realbot.strategyblocks.indicators.helpers import get_source_series
from rich import print as printanyway
from traceback import format_exc
from v2realbot.ml.ml import ModelML
import numpy as np
from collections import defaultdict
from v2realbot.strategyblocks.indicators.helpers import value_or_indicator


#IMPLEMENTS different types of moving averages
def ma(state, params):
    funcName = "ma"
    type = safe_get(params, "type", "ema")
    source = safe_get(params, "source", None)
    lookback = safe_get(params, "lookback",14)

    #lookback muze byt odkaz na indikator, pak berem jeho hodnotu
    lookback = int(value_or_indicator(state, lookback))

    source_series = get_source_series(state, source)

    #pokud je mene elementu, pracujeme s tim co je
    if len(source_series) > lookback:
        source_series = source_series[-lookback:] 

    type = "mi."+type
    ma_function = eval(type)

    ma_value = ma_function(source_series, lookback)
    val = round(ma_value[-1],4)

    state.ilog(lvl=1,e=f"INSIDE {funcName} {val} {type=} {source=} {lookback=}", **params)
    return 0, val