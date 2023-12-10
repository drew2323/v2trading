from v2realbot.strategy.base import StrategyState
from v2realbot.strategy.StrategyOrderLimitVykladaciNormalizedMYSELL import StrategyOrderLimitVykladaciNormalizedMYSELL
from v2realbot.enums.enums import RecordType, StartBarAlign, Mode, Account, Followup
from v2realbot.common.PrescribedTradeModel import Trade, TradeDirection, TradeStatus
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
from v2realbot.strategyblocks.indicators.indicators_hub import populate_all_indicators
from v2realbot.strategyblocks.indicators.helpers import evaluate_directive_conditions

#preconditions and conditions of LONG/SHORT SIGNAL
def go_conditions_met(state, data, signalname: str, direction: TradeDirection):
    if direction == TradeDirection.LONG:
        smer = "long"
    else:
        smer = "short"
    #preconditiony dle smer

    #SPECIFICKE DONT BUYS - direktivy zacinajici dont_buy
    #dont_buy_below = value nebo nazev indikatoru
    #dont_buy_above = value nebo hazev indikatoru

    #TESTUJEME SPECIFICKY DONT_GO - 
    #jak OR tak i AND
    cond_dict = state.vars.conditions[KW.dont_go][signalname][smer]
    result, conditions_met = evaluate_directive_conditions(state, cond_dict, "OR")
    state.ilog(lvl=1,e=f"SPECIFIC PRECOND =OR= {smer} {result}", **conditions_met, cond_dict=cond_dict)
    if result:
        return False

    #OR neprosly testujeme AND
    result, conditions_met = evaluate_directive_conditions(state, cond_dict, "AND")
    state.ilog(lvl=1,e=f"SPECIFIC PRECOND =AND={smer} {result}", **conditions_met, cond_dict=cond_dict)
    if result:
        return False

    #tyto timto nahrazeny - dat do konfigurace (dont_short_when, dont_long_when)
    #dont_buy_when['rsi_too_high'] = state.indicators.RSI14[-1] > safe_get(state.vars, "rsi_dont_buy_above",50)
    #dont_buy_when['slope_too_low'] = slope_too_low()
    #dont_buy_when['slope_too_high'] = slope_too_high()
    #dont_buy_when['rsi_is_zero'] = (state.indicators.RSI14[-1] == 0)
    #dont_buy_when['reverse_position_waiting_amount_not_0'] = (state.vars.reverse_position_waiting_amount != 0)

    #u indikatoru muzoun byt tyto directivy pro generovani signaliu long/short
    # long_if_crossed_down - kdyz prekrocil dolu, VALUE: hodnota nebo nazev indikatoru
    # long_if_crossed_up - kdyz prekrocil nahoru, VALUE: hodnota nebo nazev indikatoru
    # long_if_crossed - kdyz krosne obema smery, VALUE: hodnota nebo nazev indikatoru
    # long_if_falling - kdyz je klesajici po N, VALUE: hodnota
    # long_if_rising - kdyz je rostouci po N, VALUE: hodnota
    # long_if_below - kdyz je pod prahem, VALUE: hodnota nebo nazev indikatoru
    # long_if_above - kdyz je nad prahem, VALUE: hodnota nebo nazev indikatoru
    # long_if_pivot_a - kdyz je pivot A. VALUE: delka nohou
    # long_if_pivot_v - kdyz je pivot V. VALUE: delka nohou
    
    # direktivy se mohou nachazet v podsekci AND nebo OR - daneho indikatoru (nebo na volno, pak = OR)
    # OR - staci kdyz plati jedna takova podminka a buysignal je aktivni
    # AND - musi platit vsechny podminky ze vsech indikatoru, aby byl buysignal aktivni

    #populate work dict - muze byt i jen jednou v INIT nebo 1x za cas
    #dict oindexovane podminkou (OR/AND) obsahuje vsechny buy_if direktivy v tuplu (nazevind,direktiva,hodnota
    # {'AND': [('nazev indikatoru', 'nazev direktivy', 'hodnotadirektivy')], 'OR': []}
    #work_dict_signal_if = get_work_dict_with_directive(starts_with=signalname+"_"+smer+"_if")
    
    #TESTUJEME GO SIGNAL
    cond_dict = state.vars.conditions[KW.go][signalname][smer]
    result, conditions_met = evaluate_directive_conditions(state, cond_dict, "OR")
    state.ilog(lvl=1,e=f"EVAL GO SIGNAL {smer} =OR= {result}", **conditions_met, cond_dict=cond_dict)
    if result:
        return True
    
    #OR neprosly testujeme AND
    result, conditions_met = evaluate_directive_conditions(state, cond_dict, "AND")
    state.ilog(lvl=1,e=f"EVAL GO SIGNAL {smer} =AND= {result}", **conditions_met, cond_dict=cond_dict)
    if result:
        return True
    
    return False

#obecne precondition preds vstupem - platne jak pro condition based tak pro plugin
def common_go_preconditions_check(state, data, signalname: str, options: dict):
    #ZAKLADNI KONTROLY ATRIBUTU s fallbackem na obecné
    #check working windows (open - close, in minutes from the start of marker)

    window_open = safe_get(options, "window_open",safe_get(state.vars, "window_open",0))
    window_close = safe_get(options, "window_close",safe_get(state.vars, "window_close",390))

    if is_window_open(datetime.fromtimestamp(data['updated']).astimezone(zoneNY), window_open, window_close) is False:
        state.ilog(lvl=1,e=f"SIGNAL {signalname} - WINDOW CLOSED", msg=f"{window_open=} {window_close=} ", time=str(datetime.fromtimestamp(data['updated']).astimezone(zoneNY)))
        return False           

    min_bar_index = safe_get(options, "min_bar_index",safe_get(state.vars, "min_bar_index",0))
    if int(data["index"]) < int(min_bar_index):
        state.ilog(lvl=1,e=f"MIN BAR INDEX {min_bar_index} waiting - TOO SOON", currindex=data["index"])
        return False

    next_signal_offset = safe_get(options, "next_signal_offset_from_last_exit",safe_get(state.vars, "next_signal_offset_from_last_exit",0))
    #muze byt i indikator
    next_signal_offset = int(value_or_indicator(state, next_signal_offset))

    if state.vars.last_exit_index is not None:
        index_to_compare = int(state.vars.last_exit_index)+int(next_signal_offset) 
        if index_to_compare > int(data["index"]):
            state.ilog(lvl=1,e=f"NEXT SIGNAL OFFSET from EXIT {next_signal_offset} waiting - TOO SOON {signalname}", currindex=data["index"], index_to_compare=index_to_compare, last_exit_index=state.vars.last_exit_index)
            return False

    # if is_open_rush(datetime.fromtimestamp(data['updated']).astimezone(zoneNY), open_rush) or is_close_rush(datetime.fromtimestamp(data['updated']).astimezone(zoneNY), close_rush):
    #     state.ilog(lvl=0,e=f"SIGNAL {signalname} - WINDOW CLOSED", msg=f"{open_rush=} {close_rush=} ")
    #     return False

    #natvrdo nebo na podminku
    activated = safe_get(options, "activated", True)

    #check activation
    if activated is False:
        state.ilog(lvl=1,e=f"{signalname} not ACTIVATED")
        cond_dict = state.vars.conditions[KW.activate][signalname]
        result, conditions_met = evaluate_directive_conditions(state, cond_dict, "OR")
        state.ilog(lvl=1,e=f"EVAL ACTIVATION CONDITION =OR= {result}", **conditions_met, cond_dict=cond_dict)

        if result is False:            
            #OR neprosly testujeme AND
            result, conditions_met = evaluate_directive_conditions(state, cond_dict, "AND")
            state.ilog(lvl=1,e=f"EVAL ACTIVATION CONDITION  =AND= {result}", **conditions_met, cond_dict=cond_dict)

        if result is False:
            state.ilog(lvl=1,e=f"not ACTIVATED")
            return False
        else:
            state.ilog(lvl=1,e=f"{signalname} JUST ACTIVATED")
            state.vars.signals[signalname]["activated"] = True
    
    # OBECNE PRECONDITIONS - typu dont_do_when
    precond_check = dict(AND=dict(), OR=dict())

    # #OBECNE DONT BUYS
    if safe_get(options, "signal_only_on_confirmed",safe_get(state.vars, "signal_only_on_confirmed",True)):
        precond_check['bar_not_confirmed'] = (data['confirmed'] == 0)
    # #od posledniho vylozeni musi ubehnout N baru
    # dont_buy_when['last_buy_offset_too_soon'] =  data['index'] < (int(state.vars.lastbuyindex) + int(safe_get(state.vars, "lastbuy_offset",3)))
    # dont_buy_when['blockbuy_active'] = (state.vars.blockbuy == 1)
    # dont_buy_when['jevylozeno_active'] = (state.vars.jevylozeno == 1)

    #obecne open_rush platne pro vsechny
    #precond_check['on_confirmed_only'] = safe_get(options, 'on_confirmed_only', False) - chybi realizace podminky, pripadne dodelat na short_on_confirmed

    # #testing preconditions
    result, cond_met = eval_cond_dict(precond_check)
    if result:
        state.ilog(lvl=1,e=f"PRECOND GENERAL not met {cond_met}", message=cond_met, precond_check=precond_check)
        return False
    
    state.ilog(lvl=1,e=f"{signalname} ALL PRECOND MET")
    return True
