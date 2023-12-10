from v2realbot.strategy.base import StrategyState
from v2realbot.common.PrescribedTradeModel import TradeDirection, TradeStatus
from v2realbot.utils.utils import zoneNY, json_serial,transform_data
from datetime import datetime
#import random
import orjson
from v2realbot.strategyblocks.activetrade.helpers import insert_SL_history, get_default_sl_value, normalize_tick, get_profit_target_price
from v2realbot.strategyblocks.indicators.helpers import value_or_indicator

#TODO nad prescribed trades postavit vstupni funkce
def execute_prescribed_trades(state: StrategyState, data):
    ##evaluate prescribed trade, prvni eligible presuneme do activeTrade, zmenime stav and vytvorime objednavky
    
    if state.vars.activeTrade is not None or len(state.vars.prescribedTrades) == 0:
        return
    #evaluate long (price/market)
    state.ilog(lvl=1,e="evaluating prescr trades", trades=transform_data(state.vars.prescribedTrades, json_serial))
    for trade in state.vars.prescribedTrades:
        if trade.status == TradeStatus.READY and trade.direction == TradeDirection.LONG and (trade.entry_price is None or trade.entry_price >= data['close']):
            trade.status = TradeStatus.ACTIVATED
            trade.last_update = datetime.fromtimestamp(state.time).astimezone(zoneNY)
            state.ilog(lvl=1,e=f"evaluated LONG", trade=transform_data(trade, json_serial), prescrTrades=transform_data(state.vars.prescribedTrades, json_serial))
            state.vars.activeTrade = trade
            state.vars.last_buy_index = data["index"]
            state.vars.last_in_index = data["index"]
            break
    #evaluate shorts
    if not state.vars.activeTrade:
        for trade in state.vars.prescribedTrades:
            if trade.status == TradeStatus.READY and trade.direction == TradeDirection.SHORT and (trade.entry_price is None or trade.entry_price <= data['close']):
                state.ilog(lvl=1,e=f"evaluaed SHORT", trade=transform_data(trade, json_serial), prescrTrades=transform_data(state.vars.prescribedTrades, json_serial))
                trade.status = TradeStatus.ACTIVATED
                trade.last_update = datetime.fromtimestamp(state.time).astimezone(zoneNY)
                state.vars.activeTrade = trade
                state.vars.last_buy_index = data["index"]
                state.vars.last_in_index = data["index"]
                break

    #odeslani ORDER + NASTAVENI STOPLOSS (zatim hardcoded)
    if state.vars.activeTrade:
        if state.vars.activeTrade.direction == TradeDirection.LONG:
            state.ilog(lvl=1,e="odesilame LONG ORDER", trade=transform_data(state.vars.activeTrade, json_serial))
            if state.vars.activeTrade.size is not None:
                size = state.vars.activeTrade.size
            else:
                size = state.vars.chunk
            res = state.buy(size=size)
            if isinstance(res, int) and res < 0:
                raise Exception(f"error in required operation LONG {res}")

            #defaultni goal price pripadne nastavujeme az v notifikaci

            #TODO nastaveni SL az do notifikace, kdy je známá
            #pokud neni nastaveno SL v prescribe, tak nastavuji default dle stratvars
            if state.vars.activeTrade.stoploss_value is None:
                sl_defvalue = get_default_sl_value(state, direction=state.vars.activeTrade.direction)

                if isinstance(sl_defvalue, (float, int)):
                    #normalizuji dle aktualni ceny 
                    sl_defvalue_normalized = normalize_tick(state, data,sl_defvalue)
                    state.vars.activeTrade.stoploss_value = float(data['close']) - sl_defvalue_normalized
                    state.ilog(lvl=1,e=f"Nastaveno SL na {sl_defvalue}, priced normalized: {sl_defvalue_normalized} price: {state.vars.activeTrade.stoploss_value }")
                elif isinstance(sl_defvalue, str):
                    #from indicator
                    ind = sl_defvalue
                    sl_defvalue_abs = float(value_or_indicator(state, sl_defvalue))
                    if sl_defvalue_abs >= float(data['close']):
                        raise Exception(f"error in stoploss {ind} {sl_defvalue_abs} >= curr price")
                    state.vars.activeTrade.stoploss_value = sl_defvalue_abs
                    state.ilog(lvl=1,e=f"Nastaveno SL na {sl_defvalue_abs} dle indikatoru {ind}")
                insert_SL_history(state)
            state.vars.pending = state.vars.activeTrade.id
        elif state.vars.activeTrade.direction == TradeDirection.SHORT:
            state.ilog(lvl=1,e="odesilame SHORT ORDER", trade=transform_data(state.vars.activeTrade, json_serial))
            if state.vars.activeTrade.size is not None:
                size = state.vars.activeTrade.size
            else:
                size = state.vars.chunk
            res = state.sell(size=size)
            if isinstance(res, int) and res < 0:
                raise Exception(f"error in required operation SHORT {res}")
            #defaultní goalprice nastavujeme az v notifikaci

            #pokud neni nastaveno SL v prescribe, tak nastavuji default dle stratvars
            if state.vars.activeTrade.stoploss_value is None:
                sl_defvalue = get_default_sl_value(state, direction=state.vars.activeTrade.direction)

                if isinstance(sl_defvalue, (float, int)):
                    #normalizuji dle aktualni ceny 
                    sl_defvalue_normalized = normalize_tick(state, data,sl_defvalue)
                    state.vars.activeTrade.stoploss_value = float(data['close']) + sl_defvalue_normalized
                    state.ilog(lvl=1,e=f"Nastaveno SL na {sl_defvalue}, priced normalized: {sl_defvalue_normalized} price: {state.vars.activeTrade.stoploss_value }")
                elif isinstance(sl_defvalue, str):
                    #from indicator
                    ind = sl_defvalue
                    sl_defvalue_abs = float(value_or_indicator(state, sl_defvalue))
                    if sl_defvalue_abs <= float(data['close']):
                        raise Exception(f"error in stoploss {ind} {sl_defvalue_abs} <= curr price")
                    state.vars.activeTrade.stoploss_value = sl_defvalue_abs
                    state.ilog(lvl=1,e=f"Nastaveno SL na {sl_defvalue_abs} dle indikatoru {ind}")
                insert_SL_history(state)
            state.vars.pending = state.vars.activeTrade.id
        else:
            state.ilog(lvl=1,e="unknow direction")
            state.vars.activeTrade = None
