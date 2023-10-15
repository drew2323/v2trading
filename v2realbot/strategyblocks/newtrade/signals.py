from v2realbot.strategy.base import StrategyState
from v2realbot.common.PrescribedTradeModel import Trade, TradeDirection, TradeStatus
from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get
from v2realbot.config import KW
from uuid import uuid4
from datetime import datetime
from rich import print as printanyway
from traceback import format_exc
from v2realbot.strategyblocks.newtrade.conditions import go_conditions_met, common_go_preconditions_check

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

    for signalname, signalsettings in state.vars.signals.items():
        execute_signal_generator(state, data, signalname)

    # #vysledek je vložení Trade Prescription a to bud s cenou nebo immediate
    # pokud je s cenou ceka se na cenu, pokud immmediate tak se hned provede
    # to vse za predpokladu, ze neni aktivni trade

def execute_signal_generator(state, data, name):
    state.ilog(lvl=1,e=f"SIGNAL SEARCH for {name}", cond_go=state.vars.conditions[KW.go][name], cond_dontgo=state.vars.conditions[KW.dont_go][name], cond_activate=state.vars.conditions[KW.activate][name] )
    options = safe_get(state.vars.signals, name, None)

    if options is None:
        state.ilog(lvl=1,e="No options for {name} in stratvars")
        return
    
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
        if long_enabled and go_conditions_met(state, data,signalname=name, direction=TradeDirection.LONG):
            state.vars.prescribedTrades.append(Trade(
                                    id=uuid4(),
                                    last_update=datetime.fromtimestamp(state.time).astimezone(zoneNY),
                                    status=TradeStatus.READY,
                                    generated_by=name,
                                    direction=TradeDirection.LONG,
                                    entry_price=None,
                                    stoploss_value = None))
        elif short_enabled and go_conditions_met(state, data, signalname=name, direction=TradeDirection.SHORT):
            state.vars.prescribedTrades.append(Trade(
                    id=uuid4(),
                    last_update=datetime.fromtimestamp(state.time).astimezone(zoneNY),
                    status=TradeStatus.READY,
                    generated_by=name,
                    direction=TradeDirection.SHORT,
                    entry_price=None,
                    stoploss_value = None))
        else:
            state.ilog(lvl=0,e=f"{name} NO SIGNAL")
