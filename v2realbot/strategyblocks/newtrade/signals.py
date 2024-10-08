from v2realbot.strategy.base import StrategyState
from v2realbot.common.model import Trade, TradeDirection, TradeStatus
from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, gaka
from v2realbot.config import KW
from uuid import uuid4
from datetime import datetime
from rich import print as printanyway
from traceback import format_exc
from v2realbot.strategyblocks.newtrade.conditions import go_conditions_met, common_go_preconditions_check
from v2realbot.strategyblocks.newtrade.sizing import get_size, get_multiplier

def signal_search(state: StrategyState, data):
    # SIGNAL sekce ve stratvars obsahuje signaly: Ty se skladaji z obecnych parametru a podsekce podminek.
    # Obecne parametry mohou overridnout root parametry nebo dalsi upresneni(napr. plugin). Podsekce CONDITIONS,obsahuji podminky vstup a vystupu
    # OBECNE:
    # [stratvars.signals.trend2]
    # signal_only_on_confirmed = true
    # open_rush = 2
    # close_rush = 6000
    # short_enabled = false
    # long_enabled = false
    # activated = true
    # profit = 0.2
    # max_profit = 0.4
    # PODMINKY:
    # [stratvars.signals.trend2.conditions]
    # slope20.AND.in_long_if_above = 0.23
    # slope10.AND.in_long_if_rising = 5
    # slope10.out_long_if_crossed_down = -0.1
    # slope10.in_short_if_crossed_down = -0.1
    # slope10.out_short_if_above = 0
    # ema.AND.short_if_below = 28

    accountsWithNoActiveTrade = gaka(state.account_variables, "activeTrade", None, lambda x: x is None)

    if len(accountsWithNoActiveTrade.values()) == 0:
        #print("active trades on all accounts")
        return

    for signalname, signalsettings in state.vars.signals.items():
        execute_signal_generator(state, data, signalname)

    # #vysledek je vložení Trade Prescription a to bud s cenou nebo immediate
    # pokud je s cenou ceka se na cenu, pokud immmediate tak se hned provede
    # to vse za predpokladu, ze neni aktivni trade

def execute_signal_generator(state: StrategyState, data, name):
    state.ilog(lvl=1,e=f"SIGNAL SEARCH for {name}", cond_go=state.vars.conditions[KW.go][name], cond_dontgo=state.vars.conditions[KW.dont_go][name], cond_activate=state.vars.conditions[KW.activate][name] )
    options = safe_get(state.vars.signals, name, None)

    #add account from stratvars (if there) or default to self.state.account

    if options is None:
        state.ilog(lvl=1,e=f"No options for {name} in stratvars")
        return
    
    #get account of the signal, fallback to default
    account = safe_get(options, "account", state.account)
    account_long = safe_get(options, "account_long", account)
    account_short = safe_get(options, "account_short", account)

    if common_go_preconditions_check(state, data, signalname=name, options=options) is False:
        return

    # signal_plugin = "reverzni"
    # signal_plugin_run_once_at_index = 3
    #pokud existuje plugin, tak pro signal search volame plugin a ignorujeme conditiony
    signal_plugin = safe_get(options, 'plugin', None)
    signal_plugin_run_once_at_index = safe_get(options, 'signal_plugin_run_once_at_index', 3)

    #pokud je plugin True, spusti se kod
    if signal_plugin is not None and signal_plugin_run_once_at_index==data["index"]:
        try:
            custom_function = eval(signal_plugin)
            custom_function()
        except NameError:
            state.ilog(lvl=1,e=f"Custom plugin {signal_plugin} not found")
    else:
        short_enabled = safe_get(options, "short_enabled",safe_get(state.vars, "short_enabled",True))
        long_enabled = safe_get(options, "long_enabled",safe_get(state.vars, "long_enabled",True))
        #common signals based on 1) configured signals in stratvars
        #toto umoznuje jednoduchy prescribed trade bez ceny
        if short_enabled is False:
            state.ilog(lvl=1,e=f"{name} SHORT DISABLED")
        if long_enabled is False:
            state.ilog(lvl=1,e=f"{name} LONG DISABLED")
        trade_made = None
        #predkontroloa zda neni pending na accountu nebo aktivni trade
        if state.account_variables[account_long].pending is None and state.account_variables[account_long].activeTrade is None and long_enabled and go_conditions_met(state, data,signalname=name, direction=TradeDirection.LONG):
            multiplier = get_multiplier(state, data, options, TradeDirection.LONG)
            state.vars.prescribedTrades.append(Trade(
                                    account = account_long,
                                    id=uuid4(),
                                    last_update=datetime.fromtimestamp(state.time).astimezone(zoneNY),
                                    status=TradeStatus.READY,
                                    generated_by=name,
                                    size=int(multiplier*state.vars.chunk),
                                    size_multiplier = multiplier,
                                    direction=TradeDirection.LONG,
                                    entry_price=None,
                                    stoploss_value = None))
            trade_made = account_long
        #pri multiaccountu muzeme udelat v jedne iteraci vice tradu avsak vzdy na ruznych accountech
        if (trade_made is None or trade_made != account_short) and state.account_variables[account_short].pending is None and state.account_variables[account_short].activeTrade is None and short_enabled and go_conditions_met(state, data, signalname=name, direction=TradeDirection.SHORT):
            multiplier = get_multiplier(state, data, options, TradeDirection.SHORT)
            state.vars.prescribedTrades.append(Trade(
                    account=account_short,
                    id=uuid4(),
                    last_update=datetime.fromtimestamp(state.time).astimezone(zoneNY),
                    status=TradeStatus.READY,
                    generated_by=name,
                    size=int(multiplier*state.vars.chunk),
                    size_multiplier = multiplier,
                    direction=TradeDirection.SHORT,
                    entry_price=None,
                    stoploss_value = None))
            return
        state.ilog(lvl=0,e=f"{name} NO SIGNAL")
