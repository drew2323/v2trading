from v2realbot.strategy.base import StrategyState
from v2realbot.strategy.StrategyOrderLimitVykladaciNormalizedMYSELL import StrategyOrderLimitVykladaciNormalizedMYSELL
from v2realbot.enums.enums import RecordType, StartBarAlign, Mode, Account, Followup
from v2realbot.common.PrescribedTradeModel import Trade, TradeDirection, TradeStatus
from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
from v2realbot.utils.directive_utils import get_conditions_from_configuration
from v2realbot.common.model import SLHistory
from v2realbot.config import KW
#from icecream import install, ic
from rich import print as printanyway
from threading import Event
import os
from traceback import format_exc
from v2realbot.strategyblocks.indicators.helpers import evaluate_directive_conditions
from v2realbot.strategyblocks.activetrade.helpers import get_override_for_active_trade, normalize_tick

def dontexit_protection_met(state, data, direction: TradeDirection):
    if direction == TradeDirection.LONG:
        smer = "long"
    else:
        smer = "short"

    #zapracovana optimalizace, kdy po aktivovanem DONTEXITU to opet klesne pod profit a neprodá se
    #vyreseno pri kazde aktivaci se vyplni flag already_activated
    #pri naslednem false podminky se v pripade, ze je aktivovany flag posle True - 
    #take se vyrusi v closu
    def process_result(result):
        if result:
            state.dont_exit_already_activated = True
            return True
        else:
            return False

    def evaluate_result():
        mother_signal = state.vars.activeTrade.generated_by

        if mother_signal is not None:
            #TESTUJEME DONT_EXIT_
            cond_dict = state.vars.conditions[KW.dont_exit][mother_signal][smer]
            #OR 
            result, conditions_met = evaluate_directive_conditions(state, cond_dict, "OR")
            state.ilog(lvl=1,e=f"DONT_EXIT {mother_signal} {smer} =OR= {result}", **conditions_met, cond_dict=cond_dict, already_activated=str(state.dont_exit_already_activated))
            if result:
                return True
            
            #OR neprosly testujeme AND
            result, conditions_met = evaluate_directive_conditions(state, cond_dict, "AND")
            state.ilog(lvl=1,e=f"DONT_EXIT {mother_signal}  {smer} =AND= {result}", **conditions_met, cond_dict=cond_dict, already_activated=str(state.dont_exit_already_activated))
            if result:
                return True
            
        cond_dict = state.vars.conditions[KW.dont_exit]["common"][smer]            
        #OR 
        result, conditions_met = evaluate_directive_conditions(state, cond_dict, "OR")
        state.ilog(lvl=1,e=f"DONT_EXIT common {smer} =OR= {result}", **conditions_met, cond_dict=cond_dict, already_activated=str(state.dont_exit_already_activated))
        if result:
            return True
        
        #OR neprosly testujeme AND
        result, conditions_met = evaluate_directive_conditions(state, cond_dict, "AND")
        state.ilog(lvl=1,e=f"DONT_EXIT common {smer} =AND= {result}", **conditions_met, cond_dict=cond_dict, already_activated=str(state.dont_exit_already_activated))
        return result

    #nejprve evaluujeme vsechny podminky
    result = evaluate_result()

    #pak evaluujeme vysledek a vracíme
    return process_result(result)


def exit_conditions_met(state, data, direction: TradeDirection):
    if direction == TradeDirection.LONG:
        smer = "long"
    else:
        smer = "short"

    directive_name = "exit_cond_only_on_confirmed"
    exit_cond_only_on_confirmed = get_override_for_active_trade(state, directive_name=directive_name, default_value=safe_get(state.vars, directive_name, False))

    if exit_cond_only_on_confirmed and data['confirmed'] == 0:
        state.ilog(lvl=0,e="EXIT COND ONLY ON CONFIRMED BAR")
        return False
    
    ## minimální počet barů od vstupu
    directive_name = "exit_cond_req_bars"
    exit_cond_req_bars = get_override_for_active_trade(state, directive_name=directive_name, default_value=safe_get(state.vars, directive_name, 1))

    if state.vars.last_in_index is not None:
        index_to_compare = int(state.vars.last_in_index)+int(exit_cond_req_bars) 
        if int(data["index"]) < index_to_compare:
            state.ilog(lvl=1,e=f"EXIT COND WAITING on required bars from IN {exit_cond_req_bars} TOO SOON", currindex=data["index"], index_to_compare=index_to_compare, last_in_index=state.vars.last_in_index)
            return False

    #POKUD je nastaven MIN PROFIT, zkontrolujeme ho a az pripadne pustime CONDITIONY
    directive_name = "exit_cond_min_profit"
    exit_cond_min_profit_nodir = get_override_for_active_trade(state, directive_name=directive_name, default_value=safe_get(state.vars, directive_name, None))

    directive_name = "exit_cond_min_profit_" + str(smer)
    exit_cond_min_profit = get_override_for_active_trade(state, directive_name=directive_name, default_value=exit_cond_min_profit_nodir)


    #máme nastavený exit_cond_min_profit
    # zjistíme, zda jsme v daném profit a případně nepustíme dál
    # , zjistíme aktuální cenu a přičteme k avgp tento profit a podle toho pustime dal

    if exit_cond_min_profit is not None:
        exit_cond_min_profit_normalized = normalize_tick(state, data, float(exit_cond_min_profit))
        exit_cond_goal_price = price2dec(float(state.avgp)+exit_cond_min_profit_normalized,3) if int(state.positions) > 0 else price2dec(float(state.avgp)-exit_cond_min_profit_normalized,3) 
        curr_price = float(data["close"])
        state.ilog(lvl=1,e=f"EXIT COND min profit {exit_cond_goal_price=} {exit_cond_min_profit=} {exit_cond_min_profit_normalized=} {curr_price=}")
        if (int(state.positions) < 0 and curr_price<=exit_cond_goal_price) or (int(state.positions) > 0 and curr_price>=exit_cond_goal_price):
            state.ilog(lvl=1,e=f"EXIT COND min profit PASS - POKRACUJEME")
        else:
            state.ilog(lvl=1,e=f"EXIT COND min profit NOT PASS")
            return False

    #TOTO ZATIM NEMA VYZNAM
    # options = safe_get(state.vars, 'exit_conditions', None)
    # if options is None:
    #     state.ilog(lvl=0,e="No options for exit conditions in stratvars")
    #     return False
    
    # disable_exit_proteciton_when = dict(AND=dict(), OR=dict())

    # #preconditions
    # disable_exit_proteciton_when['disabled_in_config'] = safe_get(options, 'enabled', False) is False
    # #too good to be true (maximum profit)
    # #disable_sell_proteciton_when['tgtbt_reached'] = safe_get(options, 'tgtbt', False) is False
    # disable_exit_proteciton_when['disable_if_positions_above'] = int(safe_get(options, 'disable_if_positions_above', 0)) < abs(int(state.positions))

    # #testing preconditions
    # result, conditions_met = eval_cond_dict(disable_exit_proteciton_when)
    # if result:
    #     state.ilog(lvl=0,e=f"EXIT_CONDITION for{smer} DISABLED by {conditions_met}", **conditions_met)
    #     return False
    
    #bereme bud exit condition signalu, ktery activeTrade vygeneroval+ fallback na general
    state.ilog(lvl=0,e=f"EXIT CONDITIONS ENTRY {smer}", conditions=state.vars.conditions[KW.exit])

    mother_signal = state.vars.activeTrade.generated_by

    if mother_signal is not None:
        cond_dict = state.vars.conditions[KW.exit][state.vars.activeTrade.generated_by][smer]
        result, conditions_met = evaluate_directive_conditions(state, cond_dict, "OR")
        state.ilog(lvl=1,e=f"EXIT CONDITIONS of {mother_signal} =OR= {result}", **conditions_met, cond_dict=cond_dict)
        if result:
            return True
        
        #OR neprosly testujeme AND
        result, conditions_met = evaluate_directive_conditions(state, cond_dict, "AND")
        state.ilog(lvl=1,e=f"EXIT CONDITIONS of {mother_signal}  =AND= {result}", **conditions_met, cond_dict=cond_dict)
        if result:
            return True


    #pokud nemame mother signal nebo exit nevratil nic, fallback na common
    cond_dict = state.vars.conditions[KW.exit]["common"][smer]
    result, conditions_met = evaluate_directive_conditions(state, cond_dict, "OR")
    state.ilog(lvl=1,e=f"EXIT CONDITIONS of COMMON =OR= {result}", **conditions_met, cond_dict=cond_dict)
    if result:
        return True
    
    #OR neprosly testujeme AND
    result, conditions_met = evaluate_directive_conditions(state, cond_dict, "AND")
    state.ilog(lvl=1,e=f"EXIT CONDITIONS of COMMON =AND= {result}", **conditions_met, cond_dict=cond_dict)
    if result:
        return True


    #ZVAZIT JESTLI nesledujici puvodni pravidlo pro dontsellwhen pujdou realizovat inverzne jako exit when
    #PUVODNI NASTAVENI - IDENTIFIKOVAce rustoveho MOMENTA - pokud je momentum, tak prodávat později
    
    # #pokud je slope too high, pak prodavame jakmile slopeMA zacne klesat, napr. 4MA (TODO 3)

    # #TODO zkusit pro pevny profit, jednoduse pozdrzet prodej - dokud tick_price roste nebo se drzi tak neprodavat, pokud klesne prodat
    # #mozna mit dva mody - pri vetsi volatilite pouzivat momentum, pri mensi nebo kdyz potrebuju pryc, tak prodat hned

    #puvodni nastaveni
    #slopeMA_rising = 2
    #rsi_not_falling = 3

    # #toto docasne pryc dont_sell_when['slope_too_high'] = slope_too_high() and not isfalling(state.indicators.slopeMA,4)
    # dont_sell_when['AND']['slopeMA_rising'] = isrising(state.indicators.slopeMA,safe_get(options, 'slopeMA_rising', 2))
    # dont_sell_when['AND']['rsi_not_falling'] = not isfalling(state.indicators.RSI14,safe_get(options, 'rsi_not_falling',3))
    # #dont_sell_when['rsi_dont_buy'] = state.indicators.RSI14[-1] > safe_get(state.vars, "rsi_dont_buy_above",50)

    # result, conditions_met = eval_cond_dict(dont_sell_when)
    # if result:
    #     state.ilog(lvl=0,e=f"SELL_PROTECTION {conditions_met} enabled")
    # return result 
