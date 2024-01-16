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
import talib


# příklad toml pro indikátor ATR(high, low, close, timeperiod=14)
# POSITION MATTERS
# params.series.high = "high"   //series key určuje, že jde o série
# params.series.low = "low"
# params.series.low = "close"
# params.val.timeperiod = 14  //val key určuje, že jde o konkrétní hodnotu, tzn. buď hodnotu nebo název série, ze které vezmu poslední hodnotu (v tom případě by to byl string)


# params.series = ["high","low","close"] #pozicni parametry
# params.keys.timeperiod = 14 #keyword argumenty

#TA-lib prijma positional arguments (zejmena teda ty series)m tzn. series musi byt pozicni

# lookback se aplikuje na vsechy ?


#IMPLEMENTS usiong of any indicator from TA-lib library
def talib_ind(state, params, name, returns):
    funcName = "ma"
    type = safe_get(params, "type", "SMA")
    #ßsource = safe_get(params, "source", None)
    lookback = safe_get(params, "lookback",None) #celkovy lookback pro vsechny vstupni serie
    start = safe_get(params, "start","linear") #linear/sharp
    defval = safe_get(params, "defval",0)

    params = safe_get(params, "params", dict(series=[], keys=[]))
    #lookback muze byt odkaz na indikator, pak berem jeho hodnotu
    lookback = int(value_or_indicator(state, lookback))
    defval = int(value_or_indicator(state, defval))


    #TODO dopracovat caching, tzn. jen jednou pri inicializaci (linkuje se list) nicmene pri kazde iteraci musime prevest na numpy
    #NOTE doresit, kdyz je val indiaktor, aby se i po inicializaci bral z indikatoru (doresit az pokud bude treba)
    #NOTE doresit lookback, zda se aplikuje na vsechny pred volanim funkce nebo kdy?
    series_list = []
    keyArgs = {}
    for index, item in enumerate(params.get("series",[])):
        source_series = get_source_series(state, item)
        #upravujeme lookback pokud not enough values (staci jen pro prvni - jsou vsechny stejne)
        if index == 0 and lookback is not None:
            akt_pocet = len(source_series)
            if akt_pocet < lookback and start == "linear":
                lookback = akt_pocet

        series_list.append(np.array(source_series[-lookback:] if lookback is not None else source_series))

    for key, val in params.get("keys",{}).items():
         keyArgs[key] = int(value_or_indicator(state, val))

    type = "talib."+type
    talib_function = eval(type)

    ma_value = talib_function(*series_list, **keyArgs)

    if not np.isfinite(ma_value[-1]):
        val = defval
    else:
        val = round(ma_value[-1],4)

    if val == 0:
        val = defval

    state.ilog(lvl=1,e=f"INSIDE {name}:{funcName} {val} {type=} {lookback=}", **params)
    return 0, val