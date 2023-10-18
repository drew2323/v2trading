#volume weighted exp average
from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
from v2realbot.strategy.base import StrategyState
from v2realbot.indicators.moving_averages import vwma as ext_vwma
from v2realbot.strategyblocks.indicators.helpers import get_source_series
from rich import print as printanyway
from traceback import format_exc
from v2realbot.ml.ml import ModelML
import numpy as np
from collections import defaultdict
from v2realbot.strategyblocks.indicators.helpers import value_or_indicator

# Volume(or reference_source) Weighted moving Average
def vwma(state, params):
    funcName = "vwma"
    source = safe_get(params, "source", None)
    ref_source = safe_get(params, "ref_source", "volume")
    lookback = safe_get(params, "lookback",14)

    #lookback muze byt odkaz na indikator, pak berem jeho hodnotu
    lookback = int(value_or_indicator(state, lookback))
    
    source_series = get_source_series(state, source)
    ref_source_series = get_source_series(state, ref_source)

    pocet_clenu = len(source_series)
    #pokud je mene elementu, pracujeme s tim co je
    if pocet_clenu < lookback:
        lookback = pocet_clenu

    source_series = source_series[-lookback:]
    ref_source_series = ref_source_series[-lookback:]

    vwma_value = ext_vwma(source_series, ref_source_series, lookback)
    val = round(vwma_value[-1],4)

    state.ilog(lvl=1,e=f"INSIDE {funcName} {val} {source=} {ref_source=} {lookback=}", **params)
    return 0, val