from v2realbot.strategyblocks.activetrade.close.close_position import close_position
from v2realbot.strategy.base import StrategyState
from v2realbot.enums.enums import  Followup
from v2realbot.common.PrescribedTradeModel import Trade, TradeDirection, TradeStatus
from v2realbot.utils.utils import safe_get
from v2realbot.config import KW
#from icecream import install, ic
from rich import print as printanyway
from threading import Event
import os
from traceback import format_exc
from v2realbot.strategyblocks.activetrade.close.conditions import dontexit_protection_met, exit_conditions_met
from v2realbot.strategyblocks.activetrade.helpers import get_max_profit_price, get_profit_target_price, get_override_for_active_trade, keyword_conditions_met

def eval_close_position(state: StrategyState, data):
    curr_price = float(data['close'])
    state.ilog(lvl=0,e="Eval CLOSE", price=curr_price, pos=state.positions, avgp=state.avgp, pending=state.vars.pending, activeTrade=str(state.vars.activeTrade))

    if int(state.positions) != 0 and float(state.avgp)>0 and state.vars.pending is None:
        
        #close position handling
        #TBD pridat OPTIMALIZACI POZICE - EXIT 1/2

        #mame short pozice - (IDEA: rozlisovat na zaklade aktivniho tradu - umozni mi spoustet i pri soucasne long pozicemi)
        if int(state.positions) < 0:
            #get TARGET PRICE pro dany smer a signal
            goal_price = get_profit_target_price(state, data, TradeDirection.SHORT)
            max_price = get_max_profit_price(state, data, TradeDirection.SHORT)
            state.ilog(lvl=1,e=f"Goal price {str(TradeDirection.SHORT)} {goal_price} max price {max_price}")


            #EOD EXIT - TBD
            #FORCED EXIT PRI KONCI DNE

            #SL - execution
            if curr_price > state.vars.activeTrade.stoploss_value:

                directive_name = 'reverse_for_SL_exit_short'
                reverse_for_SL_exit = get_override_for_active_trade(state=state, directive_name=directive_name, default_value=safe_get(state.vars, directive_name, "no"))

                if reverse_for_SL_exit == "always":
                    followup_action = Followup.REVERSE
                elif reverse_for_SL_exit == "cond":
                    followup_action = Followup.REVERSE if keyword_conditions_met(state, data, direction=TradeDirection.SHORT, keyword=KW.slreverseonly, skip_conf_validation=True) else None
                else:
                    followup_action = None
                close_position(state=state, data=data, direction=TradeDirection.SHORT, reason="SL REACHED", followup=followup_action)
                return
            
            #REVERSE BASED ON REVERSE CONDITIONS
            if keyword_conditions_met(state, data, direction=TradeDirection.SHORT, keyword=KW.reverse):
                    close_position(state=state, data=data, direction=TradeDirection.SHORT, reason="REVERSE COND MET", followup=Followup.REVERSE)
                    return  

            #EXIT ADD CONDITIONS MET (exit and add)
            if keyword_conditions_met(state, data, direction=TradeDirection.SHORT, keyword=KW.exitadd):
                    close_position(state=state, data=data, direction=TradeDirection.SHORT, reason="EXITADD COND MET", followup=Followup.ADD)
                    return  

            #CLOSING BASED ON EXIT CONDITIONS
            if exit_conditions_met(state, data, TradeDirection.SHORT):
                    directive_name = 'reverse_for_cond_exit_short'
                    reverse_for_cond_exit_short = get_override_for_active_trade(state=state, directive_name=directive_name, default_value=safe_get(state.vars, directive_name, False))
                    directive_name = 'add_for_cond_exit_short'
                    add_for_cond_exit_short = get_override_for_active_trade(state=state, directive_name=directive_name, default_value=safe_get(state.vars, directive_name, False))
                    if reverse_for_cond_exit_short:
                        followup_action = Followup.REVERSE
                    elif add_for_cond_exit_short: 
                        followup_action = Followup.ADD
                    else:
                        followup_action = None
                    close_position(state=state, data=data, direction=TradeDirection.SHORT, reason="EXIT COND MET", followup=followup_action)
                    return                   

            #PROFIT
            if curr_price<=goal_price:
                #TODO cekat az slope prestane intenzivn erust, necekat az na klesani
                #TODO mozna cekat na nejaky signal RSI
                #TODO pripadne pokud dosahne TGTBB prodat ihned
                max_price_signal = curr_price<=max_price
                #OPTIMALIZACE pri stoupajícím angle
                if max_price_signal or dontexit_protection_met(state=state, data=data,direction=TradeDirection.SHORT) is False:
                    close_position(state=state, data=data, direction=TradeDirection.SHORT, reason=f"PROFIT or MAXPROFIT REACHED {max_price_signal=}")
                    return
        #mame long
        elif int(state.positions) > 0:

            #get TARGET PRICE pro dany smer a signal
            goal_price = get_profit_target_price(state, data, TradeDirection.LONG)
            max_price = get_max_profit_price(state, data, TradeDirection.LONG)
            state.ilog(lvl=1,e=f"Goal price {str(TradeDirection.LONG)} {goal_price} max price {max_price}")

            #EOD EXIT - TBD

            #SL - execution
            if curr_price < state.vars.activeTrade.stoploss_value:
                directive_name = 'reverse_for_SL_exit_long'
                reverse_for_SL_exit = get_override_for_active_trade(state, directive_name=directive_name, default_value=safe_get(state.vars, directive_name, "no"))

                state.ilog(lvl=1, e=f"reverse_for_SL_exit {reverse_for_SL_exit}")

                if reverse_for_SL_exit == "always":
                    followup_action = Followup.REVERSE
                elif reverse_for_SL_exit == "cond":
                    followup_action = Followup.REVERSE if keyword_conditions_met(state, data, direction=TradeDirection.LONG, keyword=KW.slreverseonly, skip_conf_validation=True) else None
                else:
                    followup_action = None

                close_position(state=state, data=data, direction=TradeDirection.LONG, reason="SL REACHED", followup=followup_action)
                return
            

            #REVERSE BASED ON REVERSE CONDITIONS
            if keyword_conditions_met(state, data,TradeDirection.LONG, KW.reverse):
                    close_position(state=state, data=data, direction=TradeDirection.LONG, reason="REVERSE COND MET", followup=Followup.REVERSE)
                    return  

            #EXIT ADD CONDITIONS MET (exit and add)
            if keyword_conditions_met(state, data, TradeDirection.LONG, KW.exitadd):
                    close_position(state=state, data=data, direction=TradeDirection.LONG, reason="EXITADD COND MET", followup=Followup.ADD)
                    return  

            #EXIT CONDITIONS
            if exit_conditions_met(state, data, TradeDirection.LONG):
                    directive_name = 'reverse_for_cond_exit_long'
                    reverse_for_cond_exit_long = get_override_for_active_trade(state, directive_name=directive_name, default_value=safe_get(state.vars, directive_name, False))
                    directive_name = 'add_for_cond_exit_long'
                    add_for_cond_exit_long = get_override_for_active_trade(state, directive_name=directive_name, default_value=safe_get(state.vars, directive_name, False))
                    if reverse_for_cond_exit_long:
                        followup_action = Followup.REVERSE
                    elif add_for_cond_exit_long: 
                        followup_action = Followup.ADD
                    else:
                        followup_action = None
                    close_position(state=state, data=data, direction=TradeDirection.LONG, reason="EXIT CONDS MET", followup=followup_action)
                    return    

            #PROFIT
            if curr_price>=goal_price:
                #TODO cekat az slope prestane intenzivn erust, necekat az na klesani
                #TODO mozna cekat na nejaky signal RSI
                #TODO pripadne pokud dosahne TGTBB prodat ihned
                max_price_signal = curr_price>=max_price
                #OPTIMALIZACE pri stoupajícím angle
                if max_price_signal or dontexit_protection_met(state, data, direction=TradeDirection.LONG) is False:
                    close_position(state=state, data=data, direction=TradeDirection.LONG, reason=f"PROFIT or MAXPROFIT REACHED {max_price_signal=}")
                    return
