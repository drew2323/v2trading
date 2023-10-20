
from v2realbot.strategy.base import StrategyState
from v2realbot.strategyblocks.indicators.cbar_price import populate_cbar_tick_price_indicator
from v2realbot.strategyblocks.indicators.custom_hub import populate_dynamic_custom_indicator
from v2realbot.strategyblocks.indicators.slope import populate_dynamic_slope_indicator
from v2realbot.strategyblocks.indicators.slopeLP import populate_dynamic_slopeLP_indicator
from v2realbot.strategyblocks.indicators.ema import populate_dynamic_ema_indicator
from v2realbot.strategyblocks.indicators.RSI import populate_dynamic_RSI_indicator
from v2realbot.strategyblocks.indicators.natr import populate_dynamic_natr_indicator
from v2realbot.strategyblocks.indicators.atr import populate_dynamic_atr_indicator
import numpy as np
from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
import json

def populate_all_indicators(data, state: StrategyState):

    #TYTO MOZNA TAKY POSUNOUT OUT
    def get_last_ind_vals():
        last_ind_vals = {}
        #print(state.indicators.items())
        for key in state.indicators:
            if key != 'time':
                last_ind_vals[key] = state.indicators[key][-6:]
        
        for key in state.cbar_indicators:
            if key != 'time':
                last_ind_vals[key] = state.cbar_indicators[key][-6:]

        # for key in state.secondary_indicators:
        #     if key != 'time':
        #         last_ind_vals[key] = state.secondary_indicators[key][-5:]   

        return last_ind_vals
    #zobrazí jak daleko od sebe chodí updaty (skupiny tradů co mění cenu) a průměr za 50jejich
    def process_delta():
        last_update_delta = round((float(data['updated']) - state.vars.last_update_time),6) if state.vars.last_update_time != 0 else 0
        state.vars.last_update_time = float(data['updated'])

        if len(state.vars.last_50_deltas) >=50:
            state.vars.last_50_deltas.pop(0)
        state.vars.last_50_deltas.append(last_update_delta)
        avg_delta = np.mean(state.vars.last_50_deltas)
        return last_update_delta, avg_delta
    
    conf_bar = data['confirmed']
    last_update_delta, avg_delta = process_delta()
    
    conf = "-----"
    if conf_bar == 1:
        conf = "CONF"
    
    lp = data['close']
    state.ilog(lvl=1,e=f"{conf} {data['index']}-{conf_bar}--delta:{last_update_delta}---AVGdelta:{avg_delta}", data=data)
 
    #TODO tento lof patri spis do nextu classic SL - je poplatny typu stratefie
    #TODO na toto se podivam, nejak moc zajasonovani a zpatky -
    #PERF PROBLEM
    state.ilog(lvl=1,e="ENTRY", msg=f"LP:{lp} P:{state.positions}/{round(float(state.avgp),3)} SL:{state.vars.activeTrade.stoploss_value if state.vars.activeTrade is not None else None} profit:{round(float(state.profit),2)} profit_rel:{round(np.mean(state.rel_profit_cum),6) if len(state.rel_profit_cum)>0 else 0} Trades:{len(state.tradeList)} pend:{state.vars.pending}", rel_profit_cum=str(state.rel_profit_cum), activeTrade=json.loads(json.dumps(state.vars.activeTrade, default=json_serial)), prescribedTrades=json.loads(json.dumps(state.vars.prescribedTrades, default=json_serial)), pending=str(state.vars.pending))
    
    #kroky pro CONFIRMED BAR only
    if conf_bar == 1:
        #logika pouze pro potvrzeny bar
        state.ilog(lvl=0,e="BAR potvrzeny")

        #pri potvrzem CBARu nulujeme counter volume pro tick based indicator
        state.vars.last_tick_volume = 0
        state.vars.next_new = 1
    #kroky pro CONTINOUS TICKS only
    else:
        #CBAR INDICATOR pro tick price a deltu VOLUME
        populate_cbar_tick_price_indicator(data, state)
        #TBD nize predelat na typizovane RSI (a to jak na urovni CBAR tak confirmed)
        #populate_cbar_rsi_indicator()

    #populate indicators, that have type in stratvars.indicators
    populate_dynamic_indicators(data, state)

    #vytiskneme si indikatory
    inds = get_last_ind_vals()
    state.ilog(lvl=1,e="Indikatory", **inds)

def populate_dynamic_indicators(data, state: StrategyState):
    #pro vsechny indikatory, ktere maji ve svych stratvars TYPE, poustime populaci daneho typu indikaotru
    for indname, indsettings in state.vars.indicators.items():
        for option,value in indsettings.items():
            if option == "type":
                if value == "slope":
                    populate_dynamic_slope_indicator(data, state, name = indname)
                #slope variant with continuous Left Point
                elif value == "slopeLP":
                    populate_dynamic_slopeLP_indicator(data, state, name = indname)
                elif value == "RSI":
                    populate_dynamic_RSI_indicator(data, state, name = indname)
                elif value == "EMA":
                    populate_dynamic_ema_indicator(data, state, name = indname)
                elif value == "NATR":
                    populate_dynamic_natr_indicator(data, state, name = indname)
                elif value == "ATR":
                    populate_dynamic_atr_indicator(data, state, name = indname)
                elif value == "custom":
                    populate_dynamic_custom_indicator(data, state, name = indname)




