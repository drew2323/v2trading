from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
from v2realbot.strategy.base import StrategyState
from v2realbot.strategyblocks.indicators.helpers import get_source_series, value_or_indicator

#allows basic mathematical operators to one or more indicators (add two indicator, add value to a indicator etc.)
def mathop(state, params):
    funcName = "mathop"
    #indicator name
    source1 = safe_get(params, "source1", None)
    source1_series = get_source_series(state, source1)
    #indicator or value
    source2 = safe_get(params, "source2", None)
    operator = safe_get(params, "operator", None)
    #state.ilog(lvl=0,e=f"INSIDE {funcName} {source1=} {source2=}", **params)

    if source1 is None or source2 is None or operator is None:
        return -2, "required source1 source2 operator"
    druhy = float(value_or_indicator(state, source2))
    if operator == "+":
        val = round(float(source1_series[-1] + druhy),4)
    elif operator == "-":
        val = round(float(source1_series[-1] - druhy),4)
    elif operator == "*":
        val = round(float(source1_series[-1] * druhy),4)    
    else:
        return -2, "unknow operator"
    state.ilog(lvl=1,e=f"INSIDE {funcName} {source1=} {source2=} {val} {druhy=}", **params)
    return 0, val






