from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
from v2realbot.strategy.base import StrategyState
from v2realbot.indicators.indicators import ema, natr, roc
from v2realbot.strategyblocks.indicators.helpers import get_source_series
from rich import print as printanyway
from traceback import format_exc
from v2realbot.ml.ml import ModelML
import numpy as np
from collections import defaultdict
import bisect

#strength, absolute change of parameter between current value and lookback value (n-past)
#used for example to measure unusual peaks
def sameprice(state, params):
    funcName = "sameprice"
    typ = safe_get(params, "type", None)

    def find_first_bigger_than_lastitem_backwards(list1):
        last_item = list1[-1]
        for i in range(len(list1) - 2, -1, -1):
            if list1[i] > last_item:
                return i
        return -1
    
    def find_first_smaller_than_lastitem_backwards(list1):
        last_item = list1[-1]
        for i in range(len(list1) - 2, -1, -1):
            if list1[i] < last_item:
                return i
        return -1
    
    if typ == "up":
        pozice_prvniho_vetsiho = find_first_bigger_than_lastitem_backwards(state.bars["vwap"])
    elif typ == "down":
        pozice_prvniho_vetsiho = find_first_smaller_than_lastitem_backwards(state.bars["vwap"])
    else:
        return -2, "unknow type"
    
    celkova_delka = len(state.bars["vwap"])

    #jde o daily high
    if pozice_prvniho_vetsiho == -1:
        state.ilog(lvl=1,e=f"INSIDE {funcName} {typ} {pozice_prvniho_vetsiho=} vracime 1")
        return 0, celkova_delka
    
    delka_k_predchozmu = celkova_delka - pozice_prvniho_vetsiho
    normalizovano = delka_k_predchozmu/celkova_delka

    state.ilog(lvl=1,e=f"INSIDE {funcName} {typ} {pozice_prvniho_vetsiho=} {celkova_delka=} {delka_k_predchozmu=} {normalizovano=}", pozice_prvniho_vetsiho=pozice_prvniho_vetsiho, celkova_delka=celkova_delka, delka_k_predchozmu=delka_k_predchozmu, **params)   

    return 0, delka_k_predchozmu

