from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
from v2realbot.strategy.base import StrategyState
from v2realbot.indicators.indicators import ema, natr, roc
from v2realbot.strategyblocks.indicators.helpers import get_source_series, evaluate_directive_conditions
from rich import print as printanyway
from traceback import format_exc
from v2realbot.ml.ml import ModelML
import numpy as np
from collections import defaultdict

#EXAMPLE of directives:
# [stratvars.indicators.novyconditional]
#     type = "custom"
#     subtype = "conditional"
#     on_confirmed_only = true
#     save_to_past = 5
# [stratvars.indicators.novyconditional.cp.conditions.isfalling]
#     ema200.setindicator_if_falling = 3
#     true_val = -1
# [stratvars.indicators.novyconditional.cp.conditions.isrising]
#     ema200.setindicator_if_rising = 3
#     true_val = 1

#novy podminkovy indikator, muze obsahovat az N podminek ve stejne syntaxy jako u signalu
#u kazde podminky je hodnota, ktera se vraci pokud je true
#hodi se pro vytvareni binarnich targetu pro ML
def conditional(state, params):
    funcName = "conditional"
    if params is None:
        return -2, "params required"
    conditions = safe_get(params, "conditions", None)
    if conditions is None:
        return -2, "conditions required"
    
    try:
        #workdict pro kazdou podminku se pripravi v initiu, v conditions mame pak novyatribut workdict
        #muzeme mit vice podminek, ale prvni True vraci
        for condname,condsettings in conditions.items():
            #true davame jednicku default
            true_val = safe_get(condsettings, "true_val", 1)
            #printanyway(f"ind {name} podminka {condname} true_val {true_val}")
            #zde je pripavena podminka, kterou jen evaluujeme
            cond_dict = condsettings["cond_dict"]
            result, conditions_met = evaluate_directive_conditions(state, cond_dict, "OR")
            state.ilog(lvl=1,e=f"IND PODMINKA {condname} =OR= {result}", **conditions_met, cond_dict=cond_dict)
            if result:
                return 0, true_val
        
            #OR neprosly testujeme AND
            result, conditions_met = evaluate_directive_conditions(state, cond_dict, "AND")
            state.ilog(lvl=1,e=f"IND PODMINKA {condname} =AND= {result}", **conditions_met, cond_dict=cond_dict)
            if result:
                return 0, true_val

        return 0, 0
    except Exception as e:
        printanyway(str(e)+format_exc())
        return -2, str(e)+format_exc()        

