from v2realbot.utils.utils import isrising, isfalling,isfallingc, isrisingc, zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
#from v2realbot.strategy.base import StrategyState
from traceback import format_exc


"""
TODO pripadne dat do 
Finds index of first value less than X seconds
This version assumes:
time_list is always non-empty and sorted.
There's always a timestamp at least 5 seconds before the current time.
"""
def find_index_optimized(time_list, seconds):
    current_time = time_list[-1]
    threshold = current_time - seconds
    left, right = 0, len(time_list) - 1

    while left < right:
        mid = (left + right) // 2
        if time_list[mid] < threshold:
            left = mid + 1
        else:
            right = mid

    return left if time_list[left] >= threshold else None

#ZATIM tyto zkopirovany SEM DO HELPERS
#podle toho jak se osvedci se zakl.indikatory to s state
#zatim se mi to moc nezda

def value_or_indicator(state,value):
    #preklad direktivy podle typu, pokud je int anebo float - je to primo hodnota
    #pokud je str, jde o indikator a dotahujeme posledni hodnotu z nej
        if isinstance(value, (float, int)):
            return value
        elif isinstance(value, str):
            try:
                #pokud existuje v indikatoru MA bereme MA jinak indikator, pokud neexistuje bereme bar 
                ret = get_source_or_MA(state, indicator=value)[-1]
                lvl = 0
                if ret == 0:
                    lvl = 1
                state.ilog(lvl=lvl,e=f"Pro porovnani bereme posledni hodnotu {ret} z indikatoru {value}")
            except Exception as e   :
                ret = 0
                state.ilog(lvl=1,e=f"Neexistuje indikator s nazvem {value} vracime 0" + str(e) + format_exc())
            return ret
        
#OPTIMALIZOVANO CHATGPT
#funkce vytvori podminky (bud pro AND/OR) z pracovniho dict
def evaluate_directive_conditions(state, work_dict, cond_type):
    def rev(kw, condition):
        if directive.endswith(kw):
            return not condition
        else:
            return condition

    cond = {}
    cond[cond_type] = {}

    # Create a dictionary to map directives to functions
    directive_functions = {
        "above": lambda ind, val: get_source_or_MA(state, ind)[-1] > value_or_indicator(state,val),
        "equals": lambda ind, val: get_source_or_MA(state, ind)[-1] == value_or_indicator(state,val),
        "below": lambda ind, val: get_source_or_MA(state, ind)[-1] < value_or_indicator(state,val),
        "fallingc": lambda ind, val: isfallingc(get_source_or_MA(state, ind), val),
        "risingc": lambda ind, val: isrisingc(get_source_or_MA(state, ind), val),
        "falling": lambda ind, val: isfalling(get_source_or_MA(state, ind), val),
        "rising": lambda ind, val: isrising(get_source_or_MA(state, ind), val),
        "crossed_down": lambda ind, val: buy_if_crossed_down(state, ind, value_or_indicator(state,val)),
        "crossed_up": lambda ind, val: buy_if_crossed_up(state, ind, value_or_indicator(state,val)),
        "crossed": lambda ind, val: buy_if_crossed_down(state, ind, value_or_indicator(state,val)) or buy_if_crossed_up(state, ind, value_or_indicator(state,val)),
        "pivot_a": lambda ind, val: is_pivot(source=get_source_or_MA(state, ind), leg_number=val, type="A"),
        "pivot_v": lambda ind, val: is_pivot(source=get_source_or_MA(state, ind), leg_number=val, type="V"),
        "still_for": lambda ind, val: is_still(get_source_or_MA(state, ind), val, 2),
    }

    for indname, directive, value in work_dict[cond_type]:
        for keyword, func in directive_functions.items():
            if directive.endswith(keyword):
                cond[cond_type][directive + "_" + indname + "_" + str(value)] = rev("not_" + keyword, func(indname, value))

    return eval_cond_dict(cond)

#TODO toto pripadne sloucit s get_source_series - revidovat dopady

def get_source_or_MA(state, indicator):
    #pokud ma, pouzije MAcko, pokud ne tak standardni indikator
    #pokud to jmeno neexistuje, tak pripadne bere z barů (close,open,hlcc4, vwap atp.)
    try:
        return state.indicators[indicator+"MA"]
    except KeyError:
        try:
            return state.indicators[indicator]
        except KeyError:
            try:
                return state.bars[indicator]
            except KeyError:
                return state.cbar_indicators[indicator]

def get_source_series(state, source: str):
    """
    Podporujeme krome klice v bar a indikatoru a dalsi doplnujici, oddelene _ napr. dailyBars_close
    vezme serii static.dailyBars[close]
    """

    split_index = source.find("|")
    if split_index == -1:
        try:
            return state.bars[source]
        except KeyError:
            try:
                return state.indicators[source]
            except KeyError:
                try:
                    return state.cbar_indicators[source]
                except KeyError:
                    return None
    else:
        dict_name = source[:split_index]
        key = source[split_index + 1:]
        return getattr(state, dict_name)[key]

#TYTO NEJSPIS DAT do util
#vrati true pokud dany indikator prekrocil threshold dolu
def buy_if_crossed_down(state, indicator, value):
    res = crossed_down(threshold=value, list=get_source_or_MA(state, indicator))
    #state.ilog(lvl=0,e=f"signal_if_crossed_down {indicator} {value} {res}")
    return res

#vrati true pokud dany indikator prekrocil threshold nahoru
def buy_if_crossed_up(state, indicator, value):
    res = crossed_up(threshold=value, list=get_source_or_MA(state, indicator))
    #state.ilog(lvl=0,e=f"signal_if_crossed_up {indicator} {value} {res}")
    return res    
   