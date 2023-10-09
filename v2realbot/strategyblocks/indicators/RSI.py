from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
from v2realbot.strategy.base import StrategyState
from v2realbot.indicators.indicators import ema, natr, roc
from v2realbot.indicators.oscillators import rsi
from traceback import format_exc
#RSI INDICATOR
# type = RSI, source = [close, vwap, hlcc4], rsi_length = [14], MA_length = int (optional), on_confirmed_only = [true, false]
# pokud existuje MA, vytvarime i stejnojnojmenny MAcko
def populate_dynamic_RSI_indicator(data, state: StrategyState, name):
    ind_type = "RSI"
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
    rsi_length = int(safe_get(options, "RSI_length",14))
    rsi_MA_length = safe_get(options, "MA_length", None)

    if on_confirmed_only is False or (on_confirmed_only is True and data['confirmed']==1):
        try:
            source = state.bars[req_source]
            #cekame na dostatek dat
            if len(source) > rsi_length:
                rsi_res = rsi(source, rsi_length)
                rsi_value = round(rsi_res[-1],4)
                state.indicators[name][-1]=rsi_value
                state.ilog(lvl=0,e=f"IND {name} RSI {rsi_value}")

                if rsi_MA_length is not None:
                    src = state.indicators[name][-rsi_MA_length:]
                    rsi_MA_res = ema(src, rsi_MA_length)
                    rsi_MA_value = round(rsi_MA_res[-1],4)
                    state.indicators[name+"MA"][-1]=rsi_MA_value
                    state.ilog(lvl=0,e=f"IND {name} RSIMA {rsi_MA_value}")

            else:
                state.ilog(lvl=0,e=f"IND {name} RSI necháváme 0", message="not enough source data", source=source, rsi_length=rsi_length)
        except Exception as e:
            state.ilog(lvl=1,e=f"IND ERROR {name} RSI necháváme 0", message=str(e)+format_exc())
