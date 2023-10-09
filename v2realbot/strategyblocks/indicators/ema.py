from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
from v2realbot.strategy.base import StrategyState
from v2realbot.indicators.indicators import ema, natr, roc
from traceback import format_exc

#EMA INDICATOR
# type = EMA, source = [close, vwap, hlcc4], length = [14], on_confirmed_only = [true, false]
def populate_dynamic_ema_indicator(data, state: StrategyState, name):
    ind_type = "EMA"
    options = safe_get(state.vars.indicators, name, None)
    if options is None:
        state.ilog(lvl=1,e=f"No options for {name} in stratvars")
        return       
    
    if safe_get(options, "type", False) is False or safe_get(options, "type", False) != ind_type:
        state.ilog(lvl=1,e="Type error")
        return
    
    #poustet kazdy tick nebo jenom na confirmed baru (on_confirmed_only = true)
    on_confirmed_only = safe_get(options, 'on_confirmed_only', False)
    req_source = safe_get(options, 'source', 'vwap')
    if req_source not in ["close", "vwap","hlcc4"]:
        state.ilog(lvl=1,e=f"Unknown source error {req_source} for {name}")
        return
    ema_length = int(safe_get(options, "length",14))
    if on_confirmed_only is False or (on_confirmed_only is True and data['confirmed']==1):
        try:
            source = state.bars[req_source][-ema_length:]
            #if len(source) > ema_length:
            ema_value = ema(source, ema_length)
            val = round(ema_value[-1],4)
            state.indicators[name][-1]= val
            #state.indicators[name][-1]= round2five(val)
            state.ilog(lvl=0,e=f"IND {name} EMA {val} {ema_length=}")
            #else:
            #    state.ilog(lvl=0,e=f"IND {name} EMA necháváme 0", message="not enough source data", source=source, ema_length=ema_length)
        except Exception as e:
            state.ilog(lvl=1,e=f"IND ERROR {name} EMA necháváme 0", message=str(e)+format_exc())
