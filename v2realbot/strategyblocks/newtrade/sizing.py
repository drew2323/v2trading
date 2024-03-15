from v2realbot.strategy.base import StrategyState
from v2realbot.common.PrescribedTradeModel import Trade, TradeDirection, TradeStatus
import v2realbot.utils.utils as utls
from v2realbot.config import KW
from uuid import uuid4
from datetime import datetime
from rich import print as printanyway
from traceback import format_exc
from v2realbot.strategyblocks.newtrade.conditions import go_conditions_met, common_go_preconditions_check
from v2realbot.strategyblocks.indicators.helpers import get_source_series
import numpy as np
from scipy.interpolate import interp1d

def get_size(state: StrategyState, data, signaloptions: dict, direction: TradeDirection):
    return state.vars.chunk * get_multiplier(state, signaloptions, direction)

def get_multiplier(state: StrategyState, data, signaloptions: dict, direction: TradeDirection):
    """"
    Function return dynamic sizing multiplier according to directive and current trades.

    Default: state.vars.chunk

    Additional sizing logic is layered on top of each other according to directives.

    Currently supporting:
    1) pattern sizing U-shape, hat-shape (x - bars, minutes, y - sizing multiplier 0 to 1 )
    2) probes

    Future ideas:
    - ML sizing model

    DIRECTIVES:
    #sondy na zacatku market
    probe_enabled = true # sonda zapnuta
    number = 1 # pocet sond
    probe_size = 0.01 #velikost sondy, nasobek def size

    #pattern - dynamicka uprava na zaklade casu
    pattern_enabled = true
    pattern_source = "minutes" #or any series - indicators, bars or state etc. (index[-1], np.sum(state.rel_profit_cum)...)
    pattern_source_vals = [0,30,90, 200, 300, 390]
    pattern_sizing_vals = [0.1,0.5, 0.8, 1, 0.6, 0.1]
    
    #np.interp(atr10, [0.001, 0.06], [1, 5])
    #size_multiplier = np.interp(pattern_source, [SIZING_pattern_source_vals], [SIZING_pattern_sizing_vals])
    

    #TODO 
    - pomocna graf pro vizualizaci interpolace - v tools/sizingpatternvisual.py
    - dopsat do dokumentace direktiv - do tabulky
    - ukládat sizing coeff do prescrTrades
    - upravit výpočet denního relativniho profitu u tradu na základě vstupního sizing koeficientu
    - vyresit zda max_oss_to_quit_rel aplikovat bud per alokovana pozice nebo trade 
    (pokud mam na trade, pak mi zafunguje i na minimalni sodnu) Zatim bude
    realizován takto

        - nejprve ověří rel profit tradu a pokud přesáhne, strategie se suspendne
        - poté se rel profit tradu vynásobí multiplikátorem a započte se do denního rel profitu, jehož
          výše se následně také ověří

    NOTE: zatim neupraveno, a do denniho rel profitu se zapocitava plnym pomerem, diky tomu
    si muzu dat i na sondu -0.5 suspend strategie. Nevyhoda: rel.profit presne neodpovida

    [stratvars.signals.morning1.sizing] #specificke pro dany signal
    probe_enabled = true
    probe_size = 0.01
    pattern_enabled = true
    # pattern_source = "minutes" #or any series - indicators, bars or state etc. (index[-1], np.sum(state.rel_profit_cum)...)
    pattern_source_axis = [0,30,90, 200, 300, 390]
    pattern_size_axis = [0.1,0.5, 0.8, 1, 0.6, 0.1]   

    [stratvars.sizing] #obecne jako fallback pro vsechny signaly
    probe_enabled = true
    probe_size = 0.01
    pattern_enabled = true
    # pattern_source = "minutes" #or any series - indicators, bars or state etc. (index[-1], np.sum(state.rel_profit_cum)...)
    pattern_source_axis = [0,30,90, 200, 300, 390]
    pattern_size_axis = [0.1,0.5, 0.8, 1, 0.6, 0.1]

    """""
    multiplier = 1

    #fallback common sizing sekci
    fallback_options = utls.safe_get(state.vars, 'sizing', None)

    #signal specific sekce
    options = utls.safe_get(signaloptions, 'sizing', fallback_options)

    if options is None:
        state.ilog(lvl=1,e="No sizing options common or signal specific in stratvars")
        return multiplier

    #PROBE ENABLED
    # probe_enabled = true # sonda zapnuta
    # probe_number = 1 # pocet sond
    # probe_size = 0.01 #velikost sondy, nasobek def size

    probe_enabled = utls.safe_get(options, "probe_enabled", False)

    if probe_enabled:
        #zatim pouze probe number 1 natvrdo, tzn. nesmi byt trade pro aktivace
        if state.vars.last_in_index is None:
            #probe_number = utls.safe_get(options, "probe_number",1)
            probe_size = float(utls.safe_get(options, "probe_size", 0.1))
            state.ilog(lvl=1,e=f"SIZER - PROBE - setting multiplier to {probe_size}", options=options)
            return probe_size

    #SIZING PATTER
    # pattern_enabled = true
    # pattern_source = "minutes" #or any series - indicators, bars or state etc. (index[-1], np.sum(state.rel_profit_cum)...)
    # pattern_source_axis = [0,30,90, 200, 300, 390]
    # pattern_size_axis = [0.1,0.5, 0.8, 1, 0.6, 0.1]  
    pattern_enabled = utls.safe_get(options, "pattern_enabled", False)

    if pattern_enabled:
        input_value = None
        pattern_source = utls.safe_get(options, "pattern_source", "minutes")

        #TODO do budoucna mozna sem dát libovolnou series např. index, time, profit, rel_profit?
        if pattern_source != "minutes":

            input_value = eval(pattern_source, {'state': state, 'np': np, 'utls': utls}, state.ind_mapping)

            if input_value is None:
                state.ilog(lvl=1,e=f"SIZER - ERROR Pattern source is None, after evaluation of expression", options=str(options))
                return multiplier
        else:
            input_value = utls.minutes_since_market_open(datetime.fromtimestamp(data['updated']).astimezone(utls.zoneNY))

        pattern_source_axis = utls.safe_get(options, "pattern_source_axis", None)
        pattern_size_axis = utls.safe_get(options, "pattern_size_axis", None)

        if pattern_source_axis is None or pattern_size_axis is None:
            state.ilog(lvl=1,e=f"SIZER - Pattern source  and size axis must be set", options=str(options))
            return multiplier

        state.ilog(lvl=1,e=f"SIZER - Input value of {pattern_source} value {input_value}", options=options, time=state.time)   

        #puvodni jednoducha interpolace
        #multiplier = np.interp(input_value, pattern_source_axis, pattern_size_axis)

        # Updated interpolation function for smoother results
        # Create the interpolation function
        f = interp1d(pattern_source_axis, pattern_size_axis, kind='cubic')

        # Interpolate the input value using the interpolation function
        multiplier = f(input_value)
        state.ilog(lvl=1,e=f"SIZER - Interpolated value  {multiplier}", input_value=input_value, pattern_source_axis=pattern_source_axis, pattern_size_axis=pattern_size_axis, options=options, time=state.time)
    
    martingale_enabled = utls.safe_get(options, "martingale_enabled", False)    

    #pocet ztrátových obchodů v řadě mi udává multiplikátor (0 - 1, 1 ztráta 2x, 3 v řadě - 4x atp.)
    if martingale_enabled:

        #martingale base - základ umocňování - klasicky 2
        base = float(utls.safe_get(options, "martingale_base", 2))
        #pocet aktuálních konsekutivních ztrát
        cont_loss_series_cnt = state.vars["transferables"]["martingale"]["cont_loss_series_cnt"]
        if cont_loss_series_cnt == 0:
            multiplier = 1
        else:
            multiplier = base ** cont_loss_series_cnt
        state.ilog(lvl=1,e=f"SIZER - MARTINGALE {multiplier}", options=options, time=state.time, cont_loss_series_cnt=cont_loss_series_cnt)
        
    if (martingale_enabled is False and multiplier > 1) or multiplier <= 0:
        state.ilog(lvl=1,e=f"SIZER - Mame nekde problem MULTIPLIER mimo RANGE ERROR {multiplier}", options=options, time=state.time)
        multiplier = 1
    return multiplier
