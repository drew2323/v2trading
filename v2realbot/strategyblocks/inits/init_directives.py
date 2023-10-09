from v2realbot.strategy.base import StrategyState
from v2realbot.strategy.StrategyOrderLimitVykladaciNormalizedMYSELL import StrategyOrderLimitVykladaciNormalizedMYSELL
from v2realbot.enums.enums import RecordType, StartBarAlign, Mode, Account, Followup
from v2realbot.common.PrescribedTradeModel import Trade, TradeDirection, TradeStatus
from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
from v2realbot.utils.directive_utils import get_conditions_from_configuration
from v2realbot.ml.mlutils import load_model
from v2realbot.common.model import SLHistory
from v2realbot.config import KW
from uuid import uuid4
from datetime import datetime
#import random
import json
import numpy as np
#from icecream import install, ic
from rich import print as printanyway
from threading import Event
import os
from traceback import format_exc

def intialize_directive_conditions(state):
    #inciializace pro akce: short, long, dont_short, dont_long, activate

    state.vars.conditions = {}

    #KEYWORDS_if_CONDITION = value
    # např. go_short_if_below = 10

    #possible KEYWORDS in directive: (AND/OR) support
    #  go_DIRECTION(go_long_if, go_short_if)
    #  dont_go_DIRECTION (dont_long_if, dont_short_if)
    #  exit_DIRECTION (exit_long_if, exit_short_if)
    #  activate (activate_if)

    #possible CONDITIONs:
    # below, above, falling, rising, crossed_up, crossed_down

    #Tyto mohou byt bud v sekci conditions a nebo v samostatne sekci common

    #pro kazdou sekci "conditions" v signals
    #si vytvorime podminkove dictionary pro kazdou akci
    #projdeme vsechny singaly


    #nejprve genereujeme ze SIGNALu
    for signalname, signalsettings in state.vars.signals.items():

        if "conditions" in signalsettings:
            section = signalsettings["conditions"]

            #directivy non direction related
            state.vars.conditions.setdefault(KW.activate,{})[signalname] = get_conditions_from_configuration(action=KW.activate+"_if", section=section)

            #direktivy direction related
            for smer in TradeDirection:
                #IDEA navrhy condition dictionary - ty v signal sekci
                # state.vars.conditions["nazev_evaluacni_sekce"]["nazevsignalu_smer"] = #sada podminek
                #signal related
                # state.vars.conditions["activate"]["trendfollow"] = #sada podminek
                # state.vars.conditions["dont_go"]["trendfollow"]["long"] = #sada podminek
                # state.vars.conditions["go"]["trendfollow"]["short"] = #sada podminek
                # state.vars.conditions["exit"]["trendfollow"]["long"] = #sada podminek
                #common
                # state.vars.conditions["exit"]["common"]["long"] = #sada podminek
                # state.vars.conditions["exit"]["common"]["long"] = #sada podminek

                state.vars.conditions.setdefault(KW.dont_go,{}).setdefault(signalname,{})[smer] = get_conditions_from_configuration(action=KW.dont_go+"_" + smer +"_if", section=section)
                state.vars.conditions.setdefault(KW.dont_exit,{}).setdefault(signalname,{})[smer] = get_conditions_from_configuration(action=KW.dont_exit+"_" + smer +"_if", section=section)
                state.vars.conditions.setdefault(KW.go,{}).setdefault(signalname,{})[smer] = get_conditions_from_configuration(action=KW.go+"_" + smer +"_if", section=section)
                state.vars.conditions.setdefault(KW.exit,{}).setdefault(signalname,{})[smer] = get_conditions_from_configuration(action=KW.exit+"_" + smer +"_if", section=section)
                state.vars.conditions.setdefault(KW.reverse,{}).setdefault(signalname,{})[smer] = get_conditions_from_configuration(action=KW.reverse+"_" + smer +"_if", section=section)
                state.vars.conditions.setdefault(KW.exitadd,{}).setdefault(signalname,{})[smer] = get_conditions_from_configuration(action=KW.exitadd+"_" + smer +"_if", section=section)
                state.vars.conditions.setdefault(KW.slreverseonly,{}).setdefault(signalname,{})[smer] = get_conditions_from_configuration(action=KW.slreverseonly+"_" + smer +"_if", section=section)
                # state.vars.work_dict_dont_do[signalname+"_"+ smer] = get_work_dict_with_directive(starts_with=signalname+"_dont_"+ smer +"_if")
                # state.vars.work_dict_signal_if[signalname+"_"+ smer] = get_work_dict_with_directive(starts_with=signalname+"_"+smer+"_if")

    #POTOM generujeme z obecnych sekci, napr. EXIT.EXIT_CONDITIONS, kde je fallback pro signal exity
    section = state.vars.exit["conditions"]
    for smer in TradeDirection:
        state.vars.conditions.setdefault(KW.exit,{}).setdefault("common",{})[smer] = get_conditions_from_configuration(action=KW.exit+"_" + smer +"_if", section=section)
        state.vars.conditions.setdefault(KW.dont_exit,{}).setdefault("common",{})[smer] = get_conditions_from_configuration(action=KW.dont_exit+"_" + smer +"_if", section=section)
        state.vars.conditions.setdefault(KW.reverse,{}).setdefault("common",{})[smer] = get_conditions_from_configuration(action=KW.reverse+"_" + smer +"_if", section=section)
        state.vars.conditions.setdefault(KW.exitadd,{}).setdefault("common",{})[smer] = get_conditions_from_configuration(action=KW.exitadd+"_" + smer +"_if", section=section)
        state.vars.conditions.setdefault(KW.slreverseonly,{}).setdefault("common",{})[smer] = get_conditions_from_configuration(action=KW.slreverseonly+"_" + smer +"_if", section=section)
