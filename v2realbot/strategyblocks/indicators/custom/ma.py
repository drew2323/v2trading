from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
from v2realbot.strategy.base import StrategyState
import v2realbot.indicators.moving_averages as mi
from v2realbot.strategyblocks.indicators.helpers import get_source_series
from rich import print as printanyway
from traceback import format_exc
import numpy as np
from collections import defaultdict
from v2realbot.strategyblocks.indicators.helpers import value_or_indicator
# from talib import BBANDS, MACD, RSI, MA_Type


#IMPLEMENTS different types of moving averages in package v2realbot.indicators.moving_averages
def ma(state, params, name):
    funcName = "ma"
    type = safe_get(params, "type", "ema")
    source = safe_get(params, "source", None)
    lookback = safe_get(params, "lookback",14)
    start = safe_get(params, "start","linear") #linear/sharp
    defval = safe_get(params, "defval",0)
    #lookback muze byt odkaz na indikator, pak berem jeho hodnotu
    lookback = int(value_or_indicator(state, lookback))
    defval = int(value_or_indicator(state, defval))

    source_series = get_source_series(state, source)

    #pokud je mene elementu, pracujeme s tim co je
    akt_pocet = len(source_series)
    if akt_pocet < lookback and start == "linear":
        lookback = akt_pocet

    #source_series = source_series[-lookback:]

    type = "mi."+type
    ma_function = eval(type)

    ma_value = ma_function(source_series, lookback)

    if not np.isfinite(ma_value[-1]):
        val = defval
    else:
        val = round(ma_value[-1],4)

    if val == 0:
        val = defval

    state.ilog(lvl=1,e=f"INSIDE {name}:{funcName} {val} {type=} {source=} {lookback=}", **params)
    return 0, val