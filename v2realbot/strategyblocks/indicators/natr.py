from v2realbot.indicators.indicators import ema, natr, roc
from v2realbot.indicators.oscillators import rsi
from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
from v2realbot.strategy.base import StrategyState
from traceback import format_exc

#NATR INDICATOR
# type = NATR, ĺength = [14], on_confirmed_only = [true, false]
def populate_dynamic_natr_indicator(data, state: StrategyState, name):
    ind_type = "NATR"
    options = safe_get(state.vars.indicators, name, None)
    if options is None:
        state.ilog(lvl=1,e=f"No options for {name} in stratvars")
        return       
    
    #poustet kazdy tick nebo jenom na confirmed baru (on_confirmed_only = true)
    on_confirmed_only = safe_get(options, 'on_confirmed_only', False)
    natr_length = int(safe_get(options, "length",5))
    if on_confirmed_only is False or (on_confirmed_only is True and data['confirmed']==1):
        try:
            source_high = state.bars["high"][-natr_length:]
            source_low = state.bars["low"][-natr_length:]
            source_close = state.bars["close"][-natr_length:]
            #if len(source) > ema_length:
            natr_value = natr(source_high, source_low, source_close, natr_length)
            val = round(natr_value[-1],4)
            state.indicators[name][-1]= val
            #state.indicators[name][-1]= round2five(val)
            state.ilog(lvl=0,e=f"IND {name} NATR {val} {natr_length=}")
            #else:
            #    state.ilog(lvl=0,e=f"IND {name} EMA necháváme 0", message="not enough source data", source=source, ema_length=ema_length)
        except Exception as e:
            state.ilog(lvl=0,e=f"IND ERROR {name} NATR necháváme 0", message=str(e)+format_exc())
