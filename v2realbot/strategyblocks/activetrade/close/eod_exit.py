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
#import random
import orjson
import numpy as np
#from icecream import install, ic
from rich import print as printanyway
from threading import Event
import os
from traceback import format_exc
from v2realbot.strategyblocks.activetrade.helpers import insert_SL_history
from v2realbot.strategyblocks.activetrade.close.conditions import dontexit_protection_met, exit_conditions_met
from v2realbot.strategyblocks.activetrade.helpers import get_max_profit_price, get_profit_target_price, get_override_for_active_trade, keyword_conditions_met


def eod_exit_activated(state: StrategyState, data, direction: TradeDirection):
    """
    Function responsible for end of day management

    V budoucnu bude obsahovat optimalizace pro uzaviraci okno 
    (obsahuje subokna - nejprve ceka na snizený profit, pak na minimálně breakeven a naposledy až forced exit)

    1) zatim pouze - na breakeven(cele okno) + forced exit(posledni minuta)


    do budoucna udelat interpolacni krivku s ubývajícím časem na snížování profit
    tzn. mam např. 60minut, tak rozdělím 4:2 +poslední minuta
    - 40 snižující profit (aktuální profit je např. 0.20ticků - tzn. 40 je 0.20, 0 je 0) - print(np.interp(atr10, [1, 10,11,12], [0, 1,100,1]))
    - 19 waiting for breakeven
    - 1 min forced immediate
    """

    directive_name = "forced_exit_window_start"
    forced_exit_window_start = get_override_for_active_trade(state, directive_name=directive_name, default_value=safe_get(state.vars, directive_name, None))

    if forced_exit_window_start is None:
        state.ilog(lvl=0,e="Forced exit not required.")
        return False

    
    directive_name = "forced_exit_window_end"
    forced_exit_window_end = get_override_for_active_trade(state, directive_name=directive_name, default_value=safe_get(state.vars, directive_name, 389))

    if forced_exit_window_start>389:
        state.ilog(lvl=0,e="Forced exit window end max is 389")
        return False

    #TBD - mozna brat skutecny cas (state.time) - nez cas tradu? mozna do budoucna
    if is_window_open(datetime.fromtimestamp(data['updated']).astimezone(zoneNY), forced_exit_window_start, forced_exit_window_end) is False:
        state.ilog(lvl=1,e=f"Forced Exit Window CLOSED", msg=f"{forced_exit_window_start=} {forced_exit_window_end=} ", time=str(datetime.fromtimestamp(data['updated']).astimezone(zoneNY)))
        return False     

    # #dokdy konci okno snizujiciho se profitu (zbytek je breakeven a posledni minuta forced) - default pulka okna
    # directive_name = "forced_exit_decreasing_profit_window_end"
    # forced_exit_decreasing_profit_window_end = get_override_for_active_trade(state, directive_name=directive_name, default_value=safe_get(state.vars, directive_name, (forced_exit_window_end-forced_exit_window_end)/2))

    # if forced_exit_decreasing_profit_window_end > forced_exit_window_end-1:
    #     state.ilog(lvl=0,e="Decreasing profit window must be less than window end -1.")
    #     return False

    #TODO v rámci profit optimalizace, udelat decreasing profit window direktivu jez kontroluje interpolovaný snizujici zisk až do 0 a pak až jede breakeven
    #TODO v rámci tech optimalizace nevolat is_window_open dvakrat - volá se per tick
    if is_window_open(datetime.fromtimestamp(data['updated']).astimezone(zoneNY), forced_exit_window_start, forced_exit_window_end-1) is True:
        state.ilog(lvl=1,e=f"Forced Exit Window OPEN - breakeven check", msg=f"{forced_exit_window_start=} {forced_exit_window_end=} ", time=str(datetime.fromtimestamp(data['updated']).astimezone(zoneNY)))
 
        directive_name = "forced_exit_breakeven_period"
        forced_exit_breakeven_period = get_override_for_active_trade(state, directive_name=directive_name, default_value=safe_get(state.vars, directive_name, True))

        if forced_exit_breakeven_period is False:
            return False

        #zatim krom posledni minuty cekame alespon na breakeven
        curr_price = float(data['close'])
        #short smer
        if direction == TradeDirection.SHORT and curr_price<=float(state.avgp):
            state.ilog(lvl=1,e=f"Forced Exit - price better than avgp, dir SHORT")
            return True
    
        if direction == TradeDirection.LONG and curr_price>=float(state.avgp):
            state.ilog(lvl=1,e=f"Forced Exit - price better than avgp, dir LONG")
            return True
        
        return False
    else:
        state.ilog(lvl=1,e=f"Forced Exit - last minute - EXIT IMMEDIATE")
        return True

