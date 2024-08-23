from v2realbot.strategy.base import StrategyState
from v2realbot.common.model import Trade, TradeDirection, TradeStatus
from v2realbot.utils.utils import gaka, isrising, isfalling,zoneNY, price2dec, print, safe_get
#from icecream import install, ic
from rich import print as printanyway
from threading import Event
import os
from traceback import format_exc
from v2realbot.strategyblocks.activetrade.helpers import get_signal_section_directive, normalize_tick, insert_SL_history

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
    
def trail_SL_management(state: StrategyState, accountsWithActiveTrade, data):
    #iterate over accountsWithActiveTrade
    for account_str, activeTrade in accountsWithActiveTrade.items():
        positions = state.account_variables[account_str].positions
        avgp = state.account_variables[account_str].avgp
        pending = state.account_variables[account_str].pending    
        signal_name = activeTrade.generated_by
        last_entry_index = state.account_variables[account_str].last_entry_index
        if int(positions) != 0 and float(avgp)>0 and pending is None:

            if int(positions) < 0:
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
            sl_trailing_enabled = get_signal_section_directive(state=state, signal_name=signal_name, directive_name=directive_name, default_value=safe_get(options, directive_name, False))
        

            #SL_trailing_protection_window_short
            directive_name = 'SL_trailing_protection_window_'+str(smer)
            SL_trailing_protection_window = get_signal_section_directive(state=state, signal_name=signal_name, directive_name=directive_name, default_value=safe_get(options, directive_name, 0))
            index_to_compare = int(last_entry_index)+int(SL_trailing_protection_window) 
            if index_to_compare > int(data["index"]):
                state.ilog(lvl=1,e=f"SL trail PROTECTION WINDOW {SL_trailing_protection_window} - TOO SOON", currindex=data["index"], index_to_compare=index_to_compare, last_entry_index=last_entry_index)
                return


            
            if sl_trailing_enabled is True:
                directive_name = 'SL_trailing_stop_at_breakeven_'+str(smer)
                stop_breakeven = get_signal_section_directive(state=state, signal_name=signal_name, directive_name=directive_name, default_value=safe_get(options, directive_name, False))
                directive_name = 'SL_defval_'+str(smer)
                def_SL = get_signal_section_directive(state=state, signal_name=signal_name, directive_name=directive_name, default_value=safe_get(options, directive_name, 0.01))
                directive_name = "SL_trailing_offset_"+str(smer)
                offset = get_signal_section_directive(state=state, signal_name=signal_name, directive_name=directive_name, default_value=safe_get(options, directive_name, 0.01))
                directive_name = "SL_trailing_step_"+str(smer)
                step = get_signal_section_directive(state=state, signal_name=signal_name, directive_name=directive_name, default_value=safe_get(options, directive_name, offset))

                #pokud je pozadovan trail jen do breakeven a uz prekroceno
                if (direction == TradeDirection.LONG and stop_breakeven and activeTrade.stoploss_value >= float(avgp)) or (direction == TradeDirection.SHORT and stop_breakeven and activeTrade.stoploss_value <= float(avgp)):
                    state.ilog(lvl=1,e=f"SL trail STOP at breakeven {str(smer)} SL:{activeTrade.stoploss_value} UNCHANGED", stop_breakeven=stop_breakeven)
                    return
                
                #Aktivace SL pokud vystoupa na "offset", a nasledne posunuti o "step"

                offset_normalized = normalize_tick(state, data, offset) #to ticks and from options
                step_normalized = normalize_tick(state, data, step)
                def_SL_normalized = normalize_tick(state, data, def_SL)
                if direction == TradeDirection.LONG:
                    move_SL_threshold = activeTrade.stoploss_value + offset_normalized + def_SL_normalized
                    state.ilog(lvl=1,e=f"SL TRAIL EVAL {smer} SL:{round(activeTrade.stoploss_value,3)} TRAILGOAL:{move_SL_threshold}", def_SL=def_SL, offset=offset, offset_normalized=offset_normalized, step_normalized=step_normalized, def_SL_normalized=def_SL_normalized)
                    if (move_SL_threshold) < data['close']:
                        activeTrade.stoploss_value += step_normalized
                        insert_SL_history(state)
                        state.ilog(lvl=1,e=f"SL TRAIL TH {smer} reached {move_SL_threshold} SL moved to {activeTrade.stoploss_value}", offset_normalized=offset_normalized, step_normalized=step_normalized, def_SL_normalized=def_SL_normalized)
                elif direction == TradeDirection.SHORT:
                    move_SL_threshold = activeTrade.stoploss_value - offset_normalized - def_SL_normalized
                    state.ilog(lvl=0,e=f"SL TRAIL EVAL {smer} SL:{round(activeTrade.stoploss_value,3)} TRAILGOAL:{move_SL_threshold}", def_SL=def_SL, offset=offset, offset_normalized=offset_normalized, step_normalized=step_normalized, def_SL_normalized=def_SL_normalized)
                    if (move_SL_threshold) > data['close']:
                        activeTrade.stoploss_value -= step_normalized
                        insert_SL_history(state)
                        state.ilog(lvl=1,e=f"SL TRAIL GOAL {smer} reached {move_SL_threshold} SL moved to {activeTrade.stoploss_value}", offset_normalized=offset_normalized, step_normalized=step_normalized, def_SL_normalized=def_SL_normalized)                            
