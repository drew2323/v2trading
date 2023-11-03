from v2realbot.strategy.base import StrategyState
import numpy as np
from rich import print as printanyway
from traceback import format_exc
import v2realbot.utils.utils as utls
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
        
        state.ilog(lvl=0,e=f"BEFORE {name}:{funcName} {operation=}", **params)
        
        #pro zacatek eval
        val = eval(operation, {'state': state, 'np': np, 'utls': utls}, state.ind_mapping)

        #printanyway(val)

        if not np.isfinite(val):
            val = 0
        #val = ne.evaluate(operation, state.ind_mapping)

        state.ilog(lvl=1,e=f"IND {name}:{funcName} {operation=} res:{val}", **params)
    except Exception as e:
        printanyway(name + str(e) + format_exc())
        raise e
    return 0, val






