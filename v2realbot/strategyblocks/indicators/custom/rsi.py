from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
from v2realbot.strategy.base import StrategyState
from v2realbot.indicators.indicators import ema as ext_ema
from v2realbot.strategyblocks.indicators.helpers import get_source_series
from rich import print as printanyway
from traceback import format_exc
import numpy as np
from v2realbot.indicators.oscillators import rsi as ind_rsi
from collections import defaultdict
from v2realbot.strategyblocks.indicators.helpers import value_or_indicator
#strength, absolute change of parameter between current value and lookback value (n-past)
#used for example to measure unusual peaks
def rsi(state, params, name):
    req_source = safe_get(params, "source", "vwap")
    rsi_length = safe_get(params, "length",14)
    start = safe_get(params, "start","linear") #linear/sharp

    #lookback muze byt odkaz na indikator, pak berem jeho hodnotu
    rsi_length = int(value_or_indicator(state, rsi_length))
    source = get_source_series(state, req_source)
    delka = len(source)

    if delka > rsi_length or start == "linear":
        if delka <= rsi_length and start == "linear":
            rsi_length = delka

        rsi_res = ind_rsi(source, rsi_length)
        val =  rsi_res[-1] if np.isfinite(rsi_res[-1]) else 0
        return 0, round(val,4)

    else:
        state.ilog(lvl=0,e=f"IND {name} RSI necháváme 0", message="not enough source data", source=source, rsi_length=rsi_length)
        return -2, "necháváma 0 nedostatek hodnot"
