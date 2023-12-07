from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
from v2realbot.strategy.base import StrategyState
from v2realbot.indicators.indicators import ema, natr, roc
from v2realbot.strategyblocks.indicators.helpers import get_source_series, evaluate_directive_conditions
from rich import print as printanyway
from traceback import format_exc
import numpy as np
from collections import defaultdict
import importlib
#EXAMPLE of directives:
# [stratvars.indicators.cusum]
#     type = "custom"
#     subtype = "classed"
#     on_confirmed_only = true
#     cp.source = "close" #source posilany explicitne do next, note that next has access to state
# [stratvars.indicators.cusum.cp.init] #params is send to init
#     threshold = 1000

#ROZSIRENI DO BUDOUCNA:
# [stratvars.indicators.cusum.cp.next] #params explciitely sent to next, note that next has access to state
#    source = "close" #indicator

#OBECNA trida pro statefull indicators - realized by class with the same name,  deriving from parent IndicatorBase class
#todo v initu inicializovat state.classed_indicators a ve stopu uklidit - resetovat
def classed(state, params, name):
    funcName = "classed"
    if params is None:
        return -2, "params required"
    
    init_params = safe_get(params, "init", None) #napr sekce obcahuje threshold = 1222, ktere jdou kwargs do initu fce
    #next_params = safe_get(params, "next", None)

    source = safe_get(params, "source", None) #source, ktery jde do initu
    source = get_source_series(state, source)
    #lookback = int(value_or_indicator(state, lookback))

    #class_next_params = safe_get(params, "class_next_params", None)
    
    try:
        if name not in state.classed_indicators:
            classname = name
            class_module = importlib.import_module("v2realbot.strategyblocks.indicators.custom.classes."+classname)
            indicatorClass = getattr(class_module, classname)
            instance = indicatorClass(state=state, **init_params)
            print("instance vytvorena", instance)
            state.classed_indicators[name] = instance
            state.ilog(lvl=1,e=f"IND CLASS {name} INITIALIZED", **params)

        if source is not None:
            val = state.classed_indicators[name].next(source[-1])
        else:
            val = state.classed_indicators[name].next()

        state.ilog(lvl=1,e=f"IND CLASS {name} NEXT {val}", **params)
        return 0, val

    except Exception as e:
        printanyway(str(e)+format_exc())
        return -2, str(e)+format_exc()        

