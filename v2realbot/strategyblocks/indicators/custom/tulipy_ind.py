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
import tulipy

#NOTE if Exception is raised by the plugin - the system stores previous value for the indicator
#plugin returns configurable default value when exception happens
#this overrides default behaviour which is when plugin raises exception the custom_hub will store previous value of the indicator as next value

#IMPLEMENTS usiong of any indicator from tulipy library
def tulipy_ind(state, params, name, returns):
    funcName = "tulipy_ind"
    type = safe_get(params, "type", None)
    if type is None:
        return -2, "type is required"
    #ßsource = safe_get(params, "source", None)
    lookback = safe_get(params, "lookback",None) #celkovy lookback pro vsechny vstupni serie
    if lookback is not None:
        #lookback muze byt odkaz na indikator, pak berem jeho hodnotu
        lookback = int(value_or_indicator(state, lookback))  

    start = safe_get(params, "start","sharp") #linear/sharp
    defval = safe_get(params, "defval",0)

    params = safe_get(params, "params", dict(series=[], keys=[]))
    defval = float(value_or_indicator(state, defval))

    try:
        #TODO dopracovat caching, tzn. jen jednou pri inicializaci (linkuje se list) nicmene pri kazde iteraci musime prevest na numpy
        #NOTE doresit, kdyz je val indiaktor, aby se i po inicializaci bral z indikatoru (doresit az pokud bude treba)
        #NOTE doresit lookback, zda se aplikuje na vsechny pred volanim funkce nebo kdy?
        series_list = []
        keyArgs = {}
        for index, item in enumerate(params.get("series",[])):
            source_series = get_source_series(state, item)
            #upravujeme lookback pokud not enough values (staci jen pro prvni - jsou vsechny stejne)
            #REMOVED: neupravujeme lookback, ale az options nize
            # if index == 0 and lookback is not None:
            #     akt_pocet = len(source_series)
            #     if akt_pocet < lookback and start == "linear":
            #         lookback = akt_pocet

            #to same pokud mame nejake op

            series_list.append(np.array(source_series[-lookback:] if lookback is not None else source_series, dtype=np.float64))

        for key, val in params.get("keys",{}).items():
            keyArgs[key] = int(value_or_indicator(state, val))

            #pokud jsou zde nejake options s period nebo timeperiodou a mame nastaveny linear, pak zkracujeme pro lepsi rozjezd
            #zatim porovnavame s prvni serii - bereme ze jsou vsechny ze stejne skupiny
            #zatim pri linearu davame vzdy akt. - 1 (napr. RSI potrebuje extra datapoint)
            if key in ["period", "timeperiod"]:
                akt_pocet = len(series_list[0])
                if akt_pocet < keyArgs[key] and start == "linear" and akt_pocet != 1:
                    keyArgs[key] = akt_pocet - 1
                    printanyway(f"zkracujeme na rozjezd celkem v serii {akt_pocet} nastavujeme period na {keyArgs[key]}")       

        type = "tulipy."+type
        talib_function = eval(type)

        ma_value = talib_function(*series_list, **keyArgs)

        #jde o multioutput, dostavame tuple a prevedeme na list (odpovida poradi v returns)
        #TODO zapracovat sem def val a isfinite
        if isinstance(ma_value, tuple):
            ma_value = list(ma_value)
            for index, res in enumerate(ma_value):
                if not np.isfinite(res[-1]):
                    ma_value[index] = defval
                else:
                    ma_value[index] = round(res[-1],5)

                if res[-1] == 0:
                    ma_value[index] = defval 
            val = ma_value           
        #single output
        else:
            if not np.isfinite(ma_value[-1]):
                val = defval
            else:
                val = round(ma_value[-1],4)

            if val == 0:
                val = defval

        state.ilog(lvl=1,e=f"INSIDE {name}:{funcName} {str(val)} {type=} {lookback=}", **params)
    #pri Exceptione vracime default value (pokud raisneme Exception do custom_hubu o patro vys, tak ten pouzije posledni hodnotu)
    except Exception as e:
        state.ilog(lvl=1,e=f"IND ERROR {name} {funcName} vracime default {defval}", message=str(e)+format_exc())
        val = defval if defval is not None else 0
    finally:
        return 0, val