from v2realbot.strategy.base import StrategyState
from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
from v2realbot.strategy.base import StrategyState
from v2realbot.indicators.indicators import ema, natr, roc
from v2realbot.indicators.oscillators import rsi
from traceback import format_exc

#WIP
def populate_cbar_rsi_indicator(data, state):
    #CBAR RSI indicator
    options = safe_get(state.vars.indicators, 'crsi', None)
    if options is None:
        state.ilog(lvl=1,e="No options for crsi in stratvars")
        return

    try:
        crsi_length = int(safe_get(options, 'crsi_length', 14))
        source = state.cbar_indicators.tick_price #[-rsi_length:] #state.bars.vwap
        crsi_res = rsi(source, crsi_length)
        crsi_value = crsi_res[-1]
        if str(crsi_value) == "nan":
            crsi_value = 0
        state.cbar_indicators.CRSI[-1]=crsi_value
        #state.ilog(lvl=0,e=f"RSI {rsi_length=} {rsi_value=} {rsi_dont_buy=} {rsi_buy_signal=}", rsi_indicator=state.indicators.RSI14[-5:])
    except Exception as e:
        state.ilog(lvl=1,e=f"CRSI {crsi_length=} necháváme 0", message=str(e)+format_exc())
        #state.indicators.RSI14[-1]=0
