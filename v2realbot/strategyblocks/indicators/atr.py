from v2realbot.indicators.indicators import ema, atr, roc
from v2realbot.indicators.oscillators import rsi
from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
from v2realbot.strategy.base import StrategyState
from traceback import format_exc

#TODO ATR INDICATOR -  predelat na CUSTOM a udelat scitani a odecteni od close (atru, atrd)
# type = ATR, ĺength = [14], on_confirmed_only = [true, false]
def populate_dynamic_atr_indicator(data, state: StrategyState, name):
    ind_type = "ATR"
    options = safe_get(state.vars.indicators, name, None)
    if options is None:
        state.ilog(lvl=1,e=f"No options for {name} in stratvars")
        return       
    
    #poustet kazdy tick nebo jenom na confirmed baru (on_confirmed_only = true)
    on_confirmed_only = safe_get(options, 'on_confirmed_only', False)
    atr_length = int(safe_get(options, "length",5))
    if on_confirmed_only is False or (on_confirmed_only is True and data['confirmed']==1):
        try:
            source_high = state.bars["high"][-atr_length:]
            source_low = state.bars["low"][-atr_length:]
            source_close = state.bars["close"][-atr_length:]
            #if len(source) > ema_length:
            atr_value = atr(source_high, source_low, source_close, atr_length)
            val = round(atr_value[-1],4)
            state.indicators[name][-1]= val
            #state.indicators[name][-1]= round2five(val)
            state.ilog(lvl=0,e=f"IND {name} ATR {val} {atr_length=}")
            #else:
            #    state.ilog(lvl=0,e=f"IND {name} EMA necháváme 0", message="not enough source data", source=source, ema_length=ema_length)
        except Exception as e:
            state.ilog(lvl=0,e=f"IND ERROR {name} ATR necháváme 0", message=str(e)+format_exc())
