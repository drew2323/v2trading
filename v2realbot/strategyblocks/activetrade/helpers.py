from v2realbot.enums.enums import RecordType, StartBarAlign, Mode, Account, Followup
from v2realbot.common.model import Trade, TradeDirection, TradeStatus
from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
from v2realbot.utils.directive_utils import get_conditions_from_configuration
from v2realbot.common.model import SLHistory
from v2realbot.config import KW
from uuid import uuid4
from datetime import datetime
from v2realbot.strategyblocks.indicators.helpers import value_or_indicator
#import random
import orjson
import numpy as np
#from icecream import install, ic
from rich import print as printanyway
from threading import Event
import os
from traceback import format_exc
from v2realbot.strategyblocks.helpers import normalize_tick
from v2realbot.strategyblocks.indicators.helpers import evaluate_directive_conditions

#TODO zde dodelat viz nize get get_signal_section_directive a pak pokracovat v close positions
#otestuje keyword podminky (napr. reverse_if, nebo exitadd_if)
def keyword_conditions_met(state, data, activeTrade: Trade, direction: TradeDirection, keyword: KW, skip_conf_validation: bool = False):
        action = str(keyword).upper()
        if direction == TradeDirection.LONG:
            smer = "long"
        else:
            smer = "short"

        mother_signal = activeTrade.generated_by

        if skip_conf_validation is False: 
            directive_name = "exit_cond_only_on_confirmed"
            exit_cond_only_on_confirmed = get_signal_section_directive(state, signal_name=activeTrade.generated_by, directive_name=directive_name, default_value=safe_get(state.vars, directive_name, False))

            if exit_cond_only_on_confirmed and data['confirmed'] == 0:
                state.ilog(lvl=0,e=f"{action} CHECK COND ONLY ON CONFIRMED BAR")
                return False

        #TOTO zatim u REVERSU neresime
        # #POKUD je nastaven MIN PROFIT, zkontrolujeme ho a az pripadne pustime CONDITIONY
        # directive_name = "exit_cond_min_profit"
        # exit_cond_min_profit = get_signal_section_directive(directive_name=directive_name, default_value=safe_get(state.vars, directive_name, None))

        # #máme nastavený exit_cond_min_profit
        # # zjistíme, zda jsme v daném profit a případně nepustíme dál
        # # , zjistíme aktuální cenu a přičteme k avgp tento profit a podle toho pustime dal

        # if exit_cond_min_profit is not None:
        #     exit_cond_min_profit_normalized = normalize_tick(float(exit_cond_min_profit))
        #     exit_cond_goal_price = price2dec(float(state.avgp)+exit_cond_min_profit_normalized,3) if int(state.positions) > 0 else price2dec(float(state.avgp)-exit_cond_min_profit_normalized,3) 
        #     curr_price = float(data["close"])
        #     state.ilog(lvl=0,e=f"EXIT COND min profit {exit_cond_goal_price=} {exit_cond_min_profit=} {exit_cond_min_profit_normalized=} {curr_price=}")
        #     if (int(state.positions) < 0 and curr_price<=exit_cond_goal_price) or (int(state.positions) > 0 and curr_price>=exit_cond_goal_price):
        #         state.ilog(lvl=0,e=f"EXIT COND min profit PASS - POKRACUJEME")
        #     else:
        #         state.ilog(lvl=0,e=f"EXIT COND min profit NOT PASS")
        #         return False

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
        state.ilog(lvl=0,e=f"{action} CONDITIONS ENTRY {smer}", conditions=state.vars.conditions[KW.reverse])

        if mother_signal is not None:
            cond_dict = state.vars.conditions[keyword][mother_signal][smer]
            result, conditions_met = evaluate_directive_conditions(state, cond_dict, "OR")
            state.ilog(lvl=1,e=f"{action} CONDITIONS of {mother_signal} =OR= {result}", **conditions_met, cond_dict=cond_dict)
            if result:
                return True
            
            #OR neprosly testujeme AND
            result, conditions_met = evaluate_directive_conditions(state, cond_dict, "AND")
            state.ilog(lvl=1,e=f"{action} CONDITIONS of {mother_signal}  =AND= {result}", **conditions_met, cond_dict=cond_dict)
            if result:
                return True


        #pokud nemame mother signal nebo exit nevratil nic, fallback na common
        cond_dict = state.vars.conditions[keyword]["common"][smer]
        result, conditions_met = evaluate_directive_conditions(state, cond_dict, "OR")
        state.ilog(lvl=1,e=f"{action} CONDITIONS of COMMON =OR= {result}", **conditions_met, cond_dict=cond_dict)
        if result:
            return True
        
        #OR neprosly testujeme AND
        result, conditions_met = evaluate_directive_conditions(state, cond_dict, "AND")
        state.ilog(lvl=0,e=f"{action} CONDITIONS of COMMON =AND= {result}", **conditions_met, cond_dict=cond_dict)
        if result:
            return True


#mozna do SL helpers tuto
def insert_SL_history(state, activeTrade: Trade):
#insert stoploss history as key sl_history into runner archive extended data
    state.extData["sl_history"].append(SLHistory(id=activeTrade.id, time=state.time, sl_val=activeTrade.stoploss_value, direction=activeTrade.direction, account=activeTrade.account))


def get_default_sl_value(state, signal_name, direction: TradeDirection):

    if direction == TradeDirection.LONG:
        smer = "long"
    else:
        smer = "short"
    
    #TODO zda signal, ktery activeTrade vygeneroval, nema vlastni nastaveni + fallback na general

    options = safe_get(state.vars, 'exit', None)

    if options is None:
        state.ilog(lvl=1,e="No options for exit in stratvars. Fallback.")
        return 0.01
    directive_name = 'SL_defval_'+str(smer)
    val = get_signal_section_directive(state, signal_name, directive_name=directive_name, default_value=safe_get(options, directive_name, 0.01))
    return val
#funkce pro direktivy, ktere muzou byt overridnute v signal sekci
#tato funkce vyhleda signal sekci aktivniho tradu a pokusi se danou direktivu vyhledat tam,
#pokud nenajde tak vrati default, ktery byl poskytnut
#TODO toto predelat na jiny nazev get_overide_for_directive_section (vstup muze byt opuze signal_name)
def get_signal_section_directive(state, signal_name: str, directive_name: str, default_value: str):
    val = default_value
    override = "NO"
    mother_signal = signal_name

    if mother_signal is not None:
        override = "YES "+mother_signal
        val = safe_get(state.vars.signals[mother_signal], directive_name, default_value)

    state.ilog(lvl=0,e=f"{directive_name} OVERRIDE {override} NEWVAL:{val} ORIGINAL:{default_value} {mother_signal}", mother_signal=mother_signal,default_value=default_value)
    return val

def get_profit_target_price(state, data, activeTrade, direction: TradeDirection):
    if direction == TradeDirection.LONG:
        smer = "long"
    else:
        smer = "short"

    directive_name = "profit"
    def_profit_both_directions = get_signal_section_directive(state, signal_name=activeTrade.generated_by, directive_name=directive_name, default_value=safe_get(state.vars, directive_name, 0.50))

    #profit pro dany smer
    directive_name = 'profit_'+str(smer)
    def_profit = get_signal_section_directive(state, signal_name=activeTrade.generated_by, directive_name=directive_name, default_value=def_profit_both_directions)

    #mame v direktivve ticky
    if isinstance(def_profit, (float, int)):
        to_return = get_normalized_profitprice_from_tick(state, data, def_profit, activeTrade.account, direction)
    #mame v direktive indikator
    elif isinstance(def_profit, str):
        to_return = float(value_or_indicator(state, def_profit))

        #min profit (ochrana extremnich hodnot indikatoru)
        directive_name = 'profit_min_ind_tick_value'
        profit_min_ind_tick_value = get_signal_section_directive(state, signal_name=activeTrade.generated_by, directive_name=directive_name, default_value=def_profit_both_directions)
        profit_min_ind_price_value = get_normalized_profitprice_from_tick(state, data, profit_min_ind_tick_value, activeTrade.account, direction)

        #ochrana pri nastaveni profitu prilis nizko
        if direction == TradeDirection.LONG and to_return < profit_min_ind_price_value or direction == TradeDirection.SHORT and to_return > profit_min_ind_price_value:
            state.ilog(lvl=1,e=f"SPATNA HODOTA DOTAZENEHO PROFITU z ind {def_profit} {to_return=} MINIMUM:{profit_min_ind_price_value} {smer} {data['close']}")
            #fallback na profit_min_ind_price_value
            to_return = profit_min_ind_price_value
        state.ilog(lvl=1,e=f"PROFIT z indikatoru {def_profit} {to_return=}")
    return to_return

##based on tick a direction, returns normalized prfoit price (LONG = avgp(nebo currprice)+norm.tick, SHORT=avgp(or currprice)-norm.tick)
def get_normalized_profitprice_from_tick(state, data, tick, account: Account, direction: TradeDirection):
        avgp = state.account_variables[account.name].avgp
        normalized_tick = normalize_tick(state, data, float(tick))
        base_price = avgp if avgp != 0 else data["close"]
        returned_price = price2dec(float(base_price)+normalized_tick,3) if direction == TradeDirection.LONG else price2dec(float(base_price)-normalized_tick,3)
        state.ilog(lvl=0,e=f"NORMALIZED TICK {tick=} {normalized_tick=} NORM.PRICE {returned_price}")
        return returned_price

def get_max_profit_price(state, activeTrade: Trade, data, direction: TradeDirection):
    if direction == TradeDirection.LONG:
        smer = "long"
    else:
        smer = "short"

    directive_name = "max_profit"
    max_profit_both_directions = get_signal_section_directive(state, signal_name=activeTrade.generated_by, directive_name=directive_name, default_value=safe_get(state.vars, directive_name, 0.35))

    avgp = state.account_variables[activeTrade.account.name].avgp
    positions = state.account_variables[activeTrade.account.name].positions

    #max profit pro dany smer, s fallbackem na bez smeru
    directive_name = 'max_profit_'+str(smer)
    max_profit = get_signal_section_directive(state, signal_name=activeTrade.generated_by, directive_name=directive_name, default_value=max_profit_both_directions)

    normalized_max_profit = normalize_tick(state,data,float(max_profit))

    state.ilog(lvl=0,e=f"MAX PROFIT {max_profit=} {normalized_max_profit=}")

    return price2dec(float(avgp)+normalized_max_profit,3) if int(positions) > 0 else price2dec(float(avgp)-normalized_max_profit,3)    
