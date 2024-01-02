from v2realbot.strategy.base import StrategyState
import numpy as np
import math
from rich import print as printanyway
from traceback import format_exc
import v2realbot.utils.utils as utls
from copy import deepcopy
# from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists


#allows executing a expression - pozor neni sanitized a zatim se spousti i v globalni scopu
#v pripade jineho nez soukromeho uziti zabezpecit

#do budoucna prozkoumat NUMEXPR - ten omezuje jen na operatory a univerzalni funkce
#eval nyni umi i user-defined function, string operation and control statements

#teroeticky se dá pouzit i SYMPY - kde se daji vytvorit jednotlive symboly s urcitou funkcni
def expression(state: StrategyState, params, name):
    try:
        funcName = "expression"
        #indicator name
        operation = utls.safe_get(params, "expression", None)
        
        if operation is None :
            return -2, "required param missing"
        
        #list of indicators that should be converted beforehands
        convertToNumpy = utls.safe_get(params, "convertToNumpy", [])

        state.ilog(lvl=0,e=f"BEFORE {name}:{funcName} {operation=}", **params)

        #nyni vytvarime kazdou iteraci nove numpy pole
        #pro optimalizaci by slo pouzit array.array ktery umi
        #sdilet s numpy pamet a nevytvari se pak kopie pole
        #nevyhoda: neumi comprehensions a dalsi
        #viz https://chat.openai.com/c/03bb0c1d-450e-4f0e-8036-d338692c1082

        #opt by chatGPT
        temp_ind_mapping = {k: np.array(v) if k in convertToNumpy else v for k, v in state.ind_mapping.items()}
     
        # temp_ind_mapping = {}
        # if len(convertToNumpy) > 0:
        #     #mozna msgpack ext in
        #     temp_ind_mapping = deepcopy(state.ind_mapping)
        #     for key in convertToNumpy:
        #         try:
        #             temp_ind_mapping[key] = np.array(state.ind_mapping[key])
        #             print(f"numpyed {key}")
        #         except Exception:
        #             pass
        
        # if len(temp_ind_mapping) == 0:
        #     temp_ind_mapping = state.ind_mapping

        #pro zacatek eval
        val = eval(operation, {'state': state, 'np': np, 'utls': utls, 'math' : math}, temp_ind_mapping)

        #printanyway(val)
        val = 0 if not np.isfinite(val) else val
        #val = ne.evaluate(operation, state.ind_mapping)

        state.ilog(lvl=1,e=f"IND {name}:{funcName} {operation=} res:{val}", **params)
    except Exception as e:
        printanyway(name + str(e) + format_exc())
        raise e
    return 0, val






