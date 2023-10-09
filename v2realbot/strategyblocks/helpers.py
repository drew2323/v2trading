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
#from icecream import install, ic
from rich import print as printanyway
from threading import Event
import os
from traceback import format_exc

def normalize_tick(state, data, tick: float, price: float = None, return_two_decimals: bool = False):
    """
    Pokud je nastaveno v direktive:
    #zda normalizovat vsechyn ticky (tzn. profit, maxprofit, SL atp.)
    Normalize_ticks= true
    Normalized Tick base price = 30

    prevede normalizovany tick na tick odpovidajici vstupni cene
    vysledek je zaokoruhleny na 2 des.mista

    u cen pod 30, vrací 0.01. U cen nad 30 vrací pomerne zvetsene, 

    """
    #nemusime dodavat cenu, bereme aktualni
    if price is None:
        price = data["close"]

    normalize_ticks = safe_get(state.vars, "normalize_ticks",False)
    normalized_base_price = safe_get(state.vars, "normalized_base_price",30)
    if normalize_ticks:
        if price<normalized_base_price:
            return tick
        else:
            #ratio of price vs base price
            ratio = price/normalized_base_price
            normalized_tick = ratio*tick
        return price2dec(normalized_tick) if return_two_decimals else normalized_tick
    else:
        return tick
