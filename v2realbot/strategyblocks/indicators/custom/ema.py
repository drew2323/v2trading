from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
from v2realbot.strategy.base import StrategyState
from v2realbot.indicators.indicators import ema as ext_ema
from v2realbot.strategyblocks.indicators.helpers import get_source_series
from rich import print as printanyway
from traceback import format_exc
import numpy as np
from collections import defaultdict
from v2realbot.strategyblocks.indicators.helpers import value_or_indicator
#strength, absolute change of parameter between current value and lookback value (n-past)
#used for example to measure unusual peaks
def ema(state, params, name):
    funcName = "ema"
    source = safe_get(params, "source", None)
    lookback = safe_get(params, "lookback",14)

    #lookback muze byt odkaz na indikator, pak berem jeho hodnotu
    lookback = int(value_or_indicator(state, lookback))
    
    source_series = get_source_series(state, source)[-lookback:] 
    ema_value = ext_ema(source_series, lookback)
    val = round(ema_value[-1],4)

    state.ilog(lvl=1,e=f"INSIDE {name}:{funcName} {val} {source=} {lookback=}", **params)
    return 0, val