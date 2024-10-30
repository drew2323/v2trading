from v2realbot.strategy.base import StrategyState
from v2realbot.common.model import TradeDirection, TradeStatus
from v2realbot.utils.utils import zoneNY, json_serial,transform_data, gaka
from datetime import datetime
#import random
import orjson
from v2realbot.strategyblocks.activetrade.helpers import insert_SL_history, get_default_sl_value, normalize_tick, get_profit_target_price
from v2realbot.strategyblocks.indicators.helpers import value_or_indicator

#TODO nad prescribed trades postavit vstupni funkce
def execute_prescribed_trades(state: StrategyState, data):
    ##evaluate prescribed trade, prvni eligible presuneme do activeTrade, zmenime stav and vytvorime objednavky

    #for multiaccount setup we check if there is active trade for each account
    
    if len(state.vars.prescribedTrades) == 0 :
        return
    
    accountsWithNoActiveTrade = gaka(state.account_variables, "activeTrade", None, lambda x: x is None)

    if len(accountsWithNoActiveTrade.values()) == 0:
        #print("active trades on all accounts")
        return

    #returns true if all values are not None
    #all(v is not None for v in d.keys())

    #evaluate long (price/market)
    #support multiaccount trades
    state.ilog(lvl=1,e="evaluating prescr trades", trades=transform_data(state.vars.prescribedTrades, json_serial))
    for trade in state.vars.prescribedTrades:
        if trade.account.name not in accountsWithNoActiveTrade.keys() or state.account_variables[trade.account.name].pending is not None: #availability or pending
            continue
        if trade.status == TradeStatus.READY and trade.direction == TradeDirection.LONG and (trade.entry_price is None or trade.entry_price >= data['close']):
            trade.status = TradeStatus.ACTIVATED
            trade.last_update = datetime.fromtimestamp(state.time).astimezone(zoneNY)
            state.ilog(lvl=1,e=f"evaluated LONG", trade=transform_data(trade, json_serial), prescrTrades=transform_data(state.vars.prescribedTrades, json_serial))
            execute_trade(state, data, trade) #TBD ERROR HANDLING
            del accountsWithNoActiveTrade[trade.account.name] #to avoid other entries on the same account
            continue
    #evaluate shorts
        if trade.status == TradeStatus.READY and trade.direction == TradeDirection.SHORT and (trade.entry_price is None or trade.entry_price <= data['close']):
            state.ilog(lvl=1,e=f"evaluaed SHORT", trade=transform_data(trade, json_serial), prescrTrades=transform_data(state.vars.prescribedTrades, json_serial))
            trade.status = TradeStatus.ACTIVATED
            trade.last_update = datetime.fromtimestamp(state.time).astimezone(zoneNY)
            execute_trade(state, data, trade) #TBD ERROR HANDLING
            del accountsWithNoActiveTrade[trade.account.name] #to avoid other entries on the same account
            continue


    #TODO konzolidovat nize na spolecny kod pro short a long
#odeslani ORDER + NASTAVENI STOPLOSS (zatim hardcoded)
#TODO doplnit error management
def execute_trade(state, data, trade):
            if trade.direction == TradeDirection.LONG:
                state.ilog(lvl=1,e="odesilame LONG ORDER", trade=transform_data(trade, json_serial))
                size = trade.size  if trade.size is not None else state.vars.chunk
                res = state.buy(size=size, account=trade.account)
                #TODO ukládáme někam ID objednávky? už zde je vráceno v res
                #TODO error handling
                if isinstance(res, int) and res < 0:
                    raise Exception(f"error in required operation LONG {res}")
                    #TODO error handling
                #defaultni goal price pripadne nastavujeme az v notifikaci
                state.account_variables[trade.account.name].activeTrade = trade

                #TODO nastaveni SL az do notifikace, kdy je známá
                #pokud neni nastaveno SL v prescribe, tak nastavuji default dle stratvars
                if trade.stoploss_value is None:
                    sl_defvalue = get_default_sl_value(state=state, signal_name=trade.generated_by, direction=trade.direction)

                    if isinstance(sl_defvalue, (float, int)):
                        #normalizuji dle aktualni ceny 
                        sl_defvalue_normalized = normalize_tick(state, data,sl_defvalue)
                        state.account_variables[trade.account.name].activeTrade.stoploss_value = float(data['close']) - sl_defvalue_normalized
                        state.ilog(lvl=1,e=f"Nastaveno SL na {sl_defvalue}, priced normalized: {sl_defvalue_normalized} price: {state.account_variables[trade.account.name].activeTrade.stoploss_value }")
                    elif isinstance(sl_defvalue, str):
                        #from indicator
                        ind = sl_defvalue
                        sl_defvalue_abs = float(value_or_indicator(state, sl_defvalue))
                        if sl_defvalue_abs >= float(data['close']):
                            raise Exception(f"error in stoploss {ind} {sl_defvalue_abs} >= curr price")
                        state.account_variables[trade.account.name].activeTrade.stoploss_value = sl_defvalue_abs
                        state.ilog(lvl=1,e=f"Nastaveno SL na {sl_defvalue_abs} dle indikatoru {ind}")
                    insert_SL_history(state, state.account_variables[trade.account.name].activeTrade)
            elif trade.direction == TradeDirection.SHORT:
                state.ilog(lvl=1,e="odesilame SHORT ORDER", trade=transform_data(trade, json_serial))
                size = trade.size if trade.size is not None else state.vars.chunk
                res = state.sell(size=size, account=trade.account)
                if isinstance(res, int) and res < 0:
                    print(f"error in required operation SHORT {res}")
                    raise Exception(f"error in required operation SHORT {res}")
                #defaultní goalprice nastavujeme az v notifikaci

                state.account_variables[trade.account.name].activeTrade = trade
                #pokud neni nastaveno SL v prescribe, tak nastavuji default dle stratvars
                if trade.stoploss_value is None:
                    sl_defvalue = get_default_sl_value(state, signal_name=trade.generated_by,direction=trade.direction)

                    if isinstance(sl_defvalue, (float, int)):
                        #normalizuji dle aktualni ceny 
                        sl_defvalue_normalized = normalize_tick(state, data,sl_defvalue)
                        state.account_variables[trade.account.name].activeTrade.stoploss_value = float(data['close']) + sl_defvalue_normalized
                        state.ilog(lvl=1,e=f"Nastaveno SL na {sl_defvalue}, priced normalized: {sl_defvalue_normalized} price: {state.account_variables[trade.account.name].activeTrade.stoploss_value }")
                    elif isinstance(sl_defvalue, str):
                        #from indicator
                        ind = sl_defvalue
                        sl_defvalue_abs = float(value_or_indicator(state, sl_defvalue))
                        if sl_defvalue_abs <= float(data['close']):
                            raise Exception(f"error in stoploss {ind} {sl_defvalue_abs} <= curr price")
                        state.account_variables[trade.account.name].activeTrade.stoploss_value = sl_defvalue_abs
                        state.ilog(lvl=1,e=f"Nastaveno SL na {sl_defvalue_abs} dle indikatoru {ind}")
                    insert_SL_history(state, state.account_variables[trade.account.name].activeTrade)

            state.account_variables[trade.account.name].pending = trade.id
            state.account_variables[trade.account.name].activeTrade = trade
            state.account_variables[trade.account.name].last_entry_index =data["index"] #last_entry_index per account
            state.vars.last_entry_index = data["index"] #spolecne pro vsechny accounty