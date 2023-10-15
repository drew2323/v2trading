from v2realbot.strategy.base import StrategyState
from v2realbot.common.PrescribedTradeModel import Trade, TradeDirection, TradeStatus
from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get
#from icecream import install, ic
from rich import print as printanyway
from threading import Event
import os
from traceback import format_exc
from v2realbot.strategyblocks.activetrade.helpers import get_override_for_active_trade, normalize_tick, insert_SL_history


#pokud se cena posouva nasim smerem olespon o (0.05) nad (SL + 0.09val), posuneme SL o offset
#+ varianta - skoncit breakeven

#DIREKTIVY:
#maximalni stoploss, fallout pro "exit_short_if" direktivy
# SL_defval_short = 0.10
# SL_defval_long = 0.10
# SL_trailing_enabled_short = true
# SL_trailing_enabled_long = true
# #minimalni vzdalenost od aktualni SL, aby se SL posunula na 
# SL_trailing_offset_short = 0.05
# SL_trailing_offset_long = 0.05
# #zda trailing zastavit na brakeeven
# SL_trailing_stop_at_breakeven_short = true
# SL_trailing_stop_at_breakeven_long = true
    
def trail_SL_management(state: StrategyState, data):
    if int(state.positions) != 0 and float(state.avgp)>0 and state.vars.pending is None:

        if int(state.positions) < 0:
            direction = TradeDirection.SHORT
            smer = "short"
        else:
            direction = TradeDirection.LONG
            smer = "long"
        
        # zatim nastaveni SL plati pro vsechny - do budoucna per signal - pridat sekci

        options = safe_get(state.vars, 'exit', None)
        if options is None:
            state.ilog(lvl=1,e="Trail SL. No options for exit conditions in stratvars.")
            return
        
        directive_name = 'SL_trailing_enabled_'+str(smer)
        sl_trailing_enabled = get_override_for_active_trade(state=state, directive_name=directive_name, default_value=safe_get(options, directive_name, False))
    

        #SL_trailing_protection_window_short
        directive_name = 'SL_trailing_protection_window_'+str(smer)
        SL_trailing_protection_window = get_override_for_active_trade(state=state, directive_name=directive_name, default_value=safe_get(options, directive_name, 0))
        index_to_compare = int(state.vars.last_in_index)+int(SL_trailing_protection_window) 
        if index_to_compare > int(data["index"]):
            state.ilog(lvl=1,e=f"SL trail PROTECTION WINDOW {SL_trailing_protection_window} - TOO SOON", currindex=data["index"], index_to_compare=index_to_compare, last_in_index=state.vars.last_in_index)
            return


        
        if sl_trailing_enabled is True:
            directive_name = 'SL_trailing_stop_at_breakeven_'+str(smer)
            stop_breakeven = get_override_for_active_trade(state=state, directive_name=directive_name, default_value=safe_get(options, directive_name, False))
            directive_name = 'SL_defval_'+str(smer)
            def_SL = get_override_for_active_trade(state=state, directive_name=directive_name, default_value=safe_get(options, directive_name, 0.01))
            directive_name = "SL_trailing_offset_"+str(smer)
            offset = get_override_for_active_trade(state=state, directive_name=directive_name, default_value=safe_get(options, directive_name, 0.01))
            directive_name = "SL_trailing_step_"+str(smer)
            step = get_override_for_active_trade(state=state, directive_name=directive_name, default_value=safe_get(options, directive_name, offset))

            #pokud je pozadovan trail jen do breakeven a uz prekroceno
            if (direction == TradeDirection.LONG and stop_breakeven and state.vars.activeTrade.stoploss_value >= float(state.avgp)) or (direction == TradeDirection.SHORT and stop_breakeven and state.vars.activeTrade.stoploss_value <= float(state.avgp)):
                state.ilog(lvl=1,e=f"SL trail STOP at breakeven {str(smer)} SL:{state.vars.activeTrade.stoploss_value} UNCHANGED", stop_breakeven=stop_breakeven)
                return
            
            #Aktivace SL pokud vystoupa na "offset", a nasledne posunuti o "step"

            offset_normalized = normalize_tick(state, data, offset) #to ticks and from options
            step_normalized = normalize_tick(state, data, step)
            def_SL_normalized = normalize_tick(state, data, def_SL)
            if direction == TradeDirection.LONG:
                move_SL_threshold = state.vars.activeTrade.stoploss_value + offset_normalized + def_SL_normalized
                state.ilog(lvl=1,e=f"SL TRAIL EVAL {smer} SL:{round(state.vars.activeTrade.stoploss_value,3)} TRAILGOAL:{move_SL_threshold}", def_SL=def_SL, offset=offset, offset_normalized=offset_normalized, step_normalized=step_normalized, def_SL_normalized=def_SL_normalized)
                if (move_SL_threshold) < data['close']:
                    state.vars.activeTrade.stoploss_value += step_normalized
                    insert_SL_history(state)
                    state.ilog(lvl=1,e=f"SL TRAIL TH {smer} reached {move_SL_threshold} SL moved to {state.vars.activeTrade.stoploss_value}", offset_normalized=offset_normalized, step_normalized=step_normalized, def_SL_normalized=def_SL_normalized)
            elif direction == TradeDirection.SHORT:
                move_SL_threshold = state.vars.activeTrade.stoploss_value - offset_normalized - def_SL_normalized
                state.ilog(lvl=0,e=f"SL TRAIL EVAL {smer} SL:{round(state.vars.activeTrade.stoploss_value,3)} TRAILGOAL:{move_SL_threshold}", def_SL=def_SL, offset=offset, offset_normalized=offset_normalized, step_normalized=step_normalized, def_SL_normalized=def_SL_normalized)
                if (move_SL_threshold) > data['close']:
                    state.vars.activeTrade.stoploss_value -= step_normalized
                    insert_SL_history(state)
                    state.ilog(lvl=1,e=f"SL TRAIL GOAL {smer} reached {move_SL_threshold} SL moved to {state.vars.activeTrade.stoploss_value}", offset_normalized=offset_normalized, step_normalized=step_normalized, def_SL_normalized=def_SL_normalized)                            
