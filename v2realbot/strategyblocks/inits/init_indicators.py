from v2realbot.strategy.base import StrategyState
from v2realbot.strategy.StrategyOrderLimitVykladaciNormalizedMYSELL import StrategyOrderLimitVykladaciNormalizedMYSELL
from v2realbot.enums.enums import RecordType, StartBarAlign, Mode, Account, Followup
from v2realbot.common.PrescribedTradeModel import Trade, TradeDirection, TradeStatus
from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
from v2realbot.utils.directive_utils import get_conditions_from_configuration
import mlroom.utils.mlutils as ml
from v2realbot.common.model import SLHistory
from v2realbot.config import KW, MODEL_DIR
from uuid import uuid4
from datetime import datetime
#import random
import orjson
import numpy as np
#from icecream import install, ic
from rich import print as printanyway
from threading import Event
import os
from traceback import format_exc

def initialize_dynamic_indicators(state):
    #pro vsechny indikatory, ktere maji ve svych stratvars TYPE inicializujeme
    ##ßprintanyway(state.vars, state)
    dict_copy = state.vars.indicators.copy()
    for indname, indsettings in dict_copy.items():
        #inicializace indikatoru na dane urovni
        output = safe_get(indsettings, 'output', "bar")
        match output:
                case "bar":
                    indicators_dict = state.indicators
                case "tick":
                    indicators_dict = state.cbar_indicators
                case _:
                    raise(f"ind output must be bar or tick {indname}")

        indicators_dict[indname] = []
        #pokud ma MA_length incializujeme i MA variantu
        if safe_get(indsettings, 'MA_length', False):
            indicators_dict[indname+"MA"] = []

        #Specifické Inicializace dle type
        for option,value in list(indsettings.items()):
            #specifika pro slope
            if option == "type":
                if value == "slope":
                    #inicializujeme statinds (pro uhel na FE)
                    state.statinds[indname] = dict(minimum_slope=safe_get(indsettings, 'minimum_slope', -1), maximum_slope=safe_get(indsettings, 'maximum_slope', 1))
                if value == "custom":
                    #pro typ custom inicializujeme promenne
                    state.vars.indicators[indname]["last_run_time"] = None
                    state.vars.indicators[indname]["last_run_index"] = None
            if option == "subtype":
                if value == "model":
                    active = safe_get(indsettings, 'active', True)
                    if active is False:
                        continue
                    #load the model
                    modelname = safe_get(indsettings["cp"], 'name', None)
                    modelversion = safe_get(indsettings["cp"], 'version', "1")
                    if modelname is not None:
                        state.vars.loaded_models[modelname] =  ml.load_model(modelname, modelversion, None, MODEL_DIR)
                        if state.vars.loaded_models[modelname] is not None:
                            printanyway(f"model {modelname} loaded")
                        else:
                            printanyway(f"ERROR model {modelname} NOT loaded")
                #pro conditional indikatory projedeme podminky [conditions] a pro kazdou pripravime (cond_dict)
                if value == "conditional":
                    conditions = state.vars.indicators[indname]["cp"]["conditions"]
                    for condname,condsettings in conditions.items():
                        state.vars.indicators[indname]["cp"]["conditions"][condname]["cond_dict"] = get_conditions_from_configuration(action=KW.change_val+"_if", section=condsettings)
                        printanyway(f'creating workdict for {condname} value {state.vars.indicators[indname]["cp"]["conditions"][condname]["cond_dict"]}')
