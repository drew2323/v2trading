import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v2realbot.strategy.base import StrategyState
from v2realbot.strategy.StrategyOrderLimitVykladaciNormalizedMYSELL import StrategyOrderLimitVykladaciNormalizedMYSELL
from v2realbot.enums.enums import RecordType, StartBarAlign, Mode, Account, OrderSide, OrderType, Followup
from v2realbot.indicators.indicators import ema, natr, roc
from v2realbot.indicators.oscillators import rsi
from v2realbot.common.PrescribedTradeModel import Trade, TradeDirection, TradeStatus, TradeStoplossType
from v2realbot.utils.utils import ltp, isrising, isfalling,trunc,AttributeDict, zoneNY, price2dec, print, safe_get, round2five, is_open_rush, is_close_rush, is_still, is_window_open, eval_cond_dict, Average, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff
from v2realbot.utils.directive_utils import get_conditions_from_configuration
from v2realbot.common.model import SLHistory
from datetime import datetime, timedelta
from v2realbot.config import KW
from uuid import uuid4
import random
import json
from numpy import inf
#from icecream import install, ic
#from rich import print
from threading import Event
from msgpack import packb, unpackb
import asyncio
import os
from traceback import format_exc

print(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
""""
Využívá: StrategyClassicSL

Klasická obousměrná multibuysignal strategie se stoplos.
Používá pouze market order, hlídá profit a stoploss.

Ve dvou fázích: 1) search and create prescriptions 2) evaluate prescriptions

list(prescribedTrade)

prescribedTrade:
- validfrom
- status .READY, ACTIVE, finished)
- direction (long/short)
- entry price: 
- stoploss: (fixed, trailing)

Hlavní loop:
- indikátory

- if empty positions (avgp=0):
    - no prescribed trades

    - any prescribed trade?
        - eval input
    
    - eval eligible entries (do buy/sell)

- if positions (avgp <>0)
    - eval exit (standard, forced by eod)
    - if not exit - eval optimalizations

"""

def next(data, state: StrategyState):
    print(10*"*","NEXT START",10*"*")
    # important vars state.avgp, state.positions, state.vars, data

    # region Common Subfunction   
    def populate_cbar_rsi_indicator():
        #CBAR RSI indicator
        options = safe_get(state.vars.indicators, 'crsi', None)
        if options is None:
            state.ilog(lvl=1,e="No options for crsi in stratvars")
            return

        try:
            crsi_length = int(safe_get(options, 'crsi_length', 14))
            source = state.cbar_indicators.tick_price #[-rsi_length:] #state.bars.vwap
            crsi_res = rsi(source, crsi_length)
            crsi_value = crsi_res[-1]
            if str(crsi_value) == "nan":
                crsi_value = 0
            state.cbar_indicators.CRSI[-1]=crsi_value
            #state.ilog(lvl=0,e=f"RSI {rsi_length=} {rsi_value=} {rsi_dont_buy=} {rsi_buy_signal=}", rsi_indicator=state.indicators.RSI14[-5:])
        except Exception as e:
            state.ilog(lvl=1,e=f"CRSI {crsi_length=} necháváme 0", message=str(e)+format_exc())
            #state.indicators.RSI14[-1]=0

    def value_or_indicator(value):
    #preklad direktivy podle typu, pokud je int anebo float - je to primo hodnota
    #pokud je str, jde o indikator a dotahujeme posledni hodnotu z nej
        if isinstance(value, (int, float)):
            return value
        elif isinstance(value, str):
            try:
                #pokud existuje MA bereme MA jinak standard
                ret = get_source_or_MA(indicator=value)[-1]
                state.ilog(lvl=0,e=f"Pro porovnani bereme posledni hodnotu {ret} z indikatoru {value}")
            except Exception as e   :
                ret = 0
                state.ilog(lvl=1,e=f"Neexistuje indikator s nazvem {value} vracime 0" + str(e) + format_exc())
            return ret

    #funkce vytvori podminky (bud pro AND/OR) z pracovniho dict
    def evaluate_directive_conditions(work_dict, cond_type):
        cond = {}
        cond[cond_type] = {}
        for indname, directive, value in work_dict[cond_type]:
            #direktivy zobecnime ve tvaru prefix_ACTION
            # ACTIONS = is_above, is_below, is_falling, is_rising, crossed_up, crossed_down, is_pivot_a, is_pivot_v
            
            #OBECNE DIREKTIVY - REUSOVATELNE
            if directive.endswith("above"):
                cond[cond_type][directive+"_"+indname+"_"+str(value)] = get_source_or_MA(indname)[-1] > value_or_indicator(value)
            elif directive.endswith("below"):
                cond[cond_type][directive+"_"+indname+"_"+str(value)] = get_source_or_MA(indname)[-1] < value_or_indicator(value)
            elif directive.endswith("falling"):
                if directive.endswith("not_falling"):
                    cond[cond_type][directive+"_"+indname+"_"+str(value)] = not isfalling(get_source_or_MA(indname),value)
                else:
                    cond[cond_type][directive+"_"+indname+"_"+str(value)] = isfalling(get_source_or_MA(indname),value)
            elif directive.endswith("rising"):
                if directive.endswith("not_rising"):
                    cond[cond_type][directive+"_"+indname+"_"+str(value)] = not isrising(get_source_or_MA(indname),value)
                else:
                    cond[cond_type][directive+"_"+indname+"_"+str(value)] = isrising(get_source_or_MA(indname),value)
            elif directive.endswith("crossed_down"):
                cond[cond_type][directive+"_"+indname+"_"+str(value)] = buy_if_crossed_down(indname, value_or_indicator(value))
            elif directive.endswith("crossed_up"):
                cond[cond_type][directive+"_"+indname+"_"+str(value)] = buy_if_crossed_up(indname, value_or_indicator(value))
            #nefunguje moc dobre
            elif directive.endswith("crossed"):
                cond[cond_type][directive+"_"+indname+"_"+str(value)] = buy_if_crossed_down(indname, value_or_indicator(value)) or buy_if_crossed_up(indname, value_or_indicator(value))
            elif directive.endswith("pivot_a"):
                cond[cond_type][directive+"_"+indname+"_"+str(value)] = is_pivot(source=get_source_or_MA(indname), leg_number=value, type="A")
            elif directive.endswith("pivot_v"):
                cond[cond_type][directive+"_"+indname+"_"+str(value)] = is_pivot(source=get_source_or_MA(indname), leg_number=value, type="V")
            elif directive.endswith("still_for"):
                #for 2 decimals
                cond[cond_type][directive+"_"+indname+"_"+str(value)] = is_still(get_source_or_MA(indname),value, 2)

            #PRIPADNE DALSI SPECIFICKE ZDE
            # elif directive == "buy_if_necospecifckeho":
            #     pass

        return eval_cond_dict(cond)


    #tato funkce vytvori dictionary typu podminek (OR/AND) 
    # z indikatoru, ktere obsahuji direktivami daneho typu(buy_if, dont_buy_when)
    # v tuplu (nazevind,direktiva,hodnota)
    # do OR jsou dane i bez prefixu
    # {'AND': [('nazev indikatoru', 'nazev direktivy', 'hodnotadirektivy')], 'OR': []}
    #POZOR TOTO JE STARY FORMAT - podminky jsou uvnitr sekce indikatoru
    #v INITU uz mame novy format uvnitr sekce signal v podsekci conditions
    # def get_work_dict_with_directive(starts_with: str):
    #     reslist = dict(AND=[], OR=[])

    #     for indname, indsettings in state.vars.indicators.items():
    #         for option,value in indsettings.items():
    #                 if option.startswith(starts_with):
    #                     reslist["OR"].append((indname, option, value))
    #                 if option == "AND":
    #                     #vsechny buy direktivy, ktere jsou pod AND
    #                     for key, val in value.items():
    #                         if key.startswith(starts_with):
    #                             reslist["AND"].append((indname, key, val))
    #                 if option == "OR" :
    #                     #vsechny buy direktivy, ktere jsou pod OR
    #                     for key, val in value.items():
    #                         if key.startswith(starts_with):
    #                             reslist["OR"].append((indname, key, val))
    #     return reslist     

    def get_source_or_MA(indicator):
        #pokud ma, pouzije MAcko, pokud ne tak standardni indikator
        try:
            return state.indicators[indicator+"MA"]
        except KeyError:
            return state.indicators[indicator]
    # #vrati true pokud dany indikator krosnul obema smery
    # def buy_if_crossed(indicator, value):
    #     res = crossed(threshold=value, list=get_source_or_MA(indicator))
    #     state.ilog(lvl=0,e=f"buy_if_crossed {indicator} {value} {res}")
    #     return res

    #vrati true pokud dany indikator prekrocil threshold dolu
    def buy_if_crossed_down(indicator, value):
        res = crossed_down(threshold=value, list=get_source_or_MA(indicator))
        state.ilog(lvl=0,e=f"signal_if_crossed_down {indicator} {value} {res}")
        return res

    #vrati true pokud dany indikator prekrocil threshold nahoru
    def buy_if_crossed_up(indicator, value):
        res = crossed_up(threshold=value, list=get_source_or_MA(indicator))
        state.ilog(lvl=0,e=f"signal_if_crossed_up {indicator} {value} {res}")
        return res    

    def populate_cbar_tick_price_indicator():
        try:
            #pokud v potvrzovacím baru nebyly zmeny, nechavam puvodni hodnoty
            # if tick_delta_volume == 0:
            #     state.indicators.tick_price[-1] = state.indicators.tick_price[-2]
            #     state.indicators.tick_volume[-1] = state.indicators.tick_volume[-2]
            # else:

            #tick_price = round2five(data['close'])
            tick_price = data['close']
            tick_delta_volume = data['volume'] - state.vars.last_tick_volume

            #docasne dame pryc volume deltu a davame absolutni cislo
            state.cbar_indicators.tick_price[-1] = tick_price
            state.cbar_indicators.tick_volume[-1] = tick_delta_volume
        except:
            pass

        state.ilog(lvl=0,e=f"TICK PRICE {tick_price} VOLUME {tick_delta_volume} {conf_bar=}", prev_price=state.vars.last_tick_price, prev_volume=state.vars.last_tick_volume)

        state.vars.last_tick_price = tick_price
        state.vars.last_tick_volume = data['volume']

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

    def populate_dynamic_indicators():
        #pro vsechny indikatory, ktere maji ve svych stratvars TYPE, poustime populaci daneho typu indikaotru
        for indname, indsettings in state.vars.indicators.items():
            for option,value in indsettings.items():
                if option == "type":
                    populate_dynamic_indicator_hub(type=value, name=indname)

    def populate_dynamic_indicator_hub(type, name):
        if type == "slope":
            populate_dynamic_slope_indicator(name = name)
        #slope variant with continuous Left Point
        elif type == "slopeLP":
            populate_dynamic_slopeLP_indicator(name = name)
        elif type == "RSI":
            populate_dynamic_RSI_indicator(name = name)
        elif type == "EMA":
            populate_dynamic_ema_indicator(name = name)
        elif type == "NATR":
            populate_dynamic_natr_indicator(name = name)
        elif type == "custom":
            populate_dynamic_custom_indicator(name = name)
        else:
            return


    #WIP -
    def populate_dynamic_custom_indicator(name):
        ind_type = "custom"
        options = safe_get(state.vars.indicators, name, None)
        if options is None:
            state.ilog(lvl=1,e=f"No options for {name} in stratvars")
            return       
        
        if safe_get(options, "type", False) is False or safe_get(options, "type", False) != ind_type:
            state.ilog(lvl=1,e="Type error")
            return
        
        #poustet kazdy tick nebo jenom na confirmed baru (on_confirmed_only = true)
        subtype = safe_get(options, 'subtype', False)
        if subtype is False:
            state.ilog(lvl=1,e=f"No subtype for {name} in stratvars")
            return
        
        #if MA is required
        MA_length = safe_get(options, "MA_length", None)

        def is_time_to_run():
            # on_confirmed_only = true (def. False)
            # start_at_bar_index = 2 (def. None)
            # start_at_time = "9:31" (def. None)
            # repeat_every_Nbar =  N (def.None) (opakovat každý N bar, 1 - každý bar, 2 - každý 2., 0 - pouze jednou)
            # repeat_every_Nmin =  N (def. None) opakovat každých N minut

            on_confirmed_only = safe_get(options, 'on_confirmed_only', False)
            start_at_bar_index = safe_get(options, 'start_at_bar_index', None)
            start_at_time = safe_get(options, 'start_at_time', None) # "9:30"
            repeat_every_Nbar = safe_get(options, 'repeat_every_Nbar', None)
            repeat_every_Nmin = safe_get(options, 'repeat_every_Nmin', None)

            #stavové promenne v ramci indikatoru last_run_time a last_run_index - pro repeat_every.. direktivy
            last_run_time = safe_get(options, 'last_run_time', None)
            last_run_index = safe_get(options, 'last_run_index', None)

            #confirmed
            cond = on_confirmed_only is False or (on_confirmed_only is True and data['confirmed']==1)
            if cond is False:
                return cond, "not confirmed"

            #start_at_time - v rámci optimalizace presunout do INIT parametru indikátorů, které se naplní v initu a celou dobu se nemění
            if start_at_time is not None:
                dt_now = datetime.fromtimestamp(data["updated"]).astimezone(zoneNY)
                # Parse the maxTime string into a datetime object with the same date as timeA
                req_start_time = datetime.strptime(start_at_time, "%H:%M").replace(
                    year=dt_now.year, month=dt_now.month, day=dt_now.day)

                # Compare the time components (hours and minutes) of timeA and maxTime
                if dt_now.time() > req_start_time.time():
                    state.ilog(lvl=0,e=f"IND {name} {subtype} START FROM TIME - PASSED: now:{dt_now.time()} reqtime:{req_start_time.time()}")
                else:
                    state.ilog(lvl=0,e=f"IND {name} {subtype} START FROM TIME - NOT YET: now:{dt_now.time()} reqtime:{req_start_time.time()}")
                    cond = False

            if cond is False:
                return cond, "start_at_time not yet"

            #start_on_bar = 0
            if start_at_bar_index is not None:
                cond = start_at_bar_index < data["index"]
                if cond:
                    state.ilog(lvl=0,e=f"IND {name} {subtype} START FROM BAR - PASSED: now:{data['index']} reqbar:{start_at_bar_index}")
                else:
                    state.ilog(lvl=0,e=f"IND {name} {subtype} START FROM BAR  - NOT YET: now:{data['index']} reqbar:{start_at_bar_index}")
        
            if cond is False:
                return cond, "start_at_bar_index not yet"

            #pokud 0 - opakujeme jednou, pokud 1 tak opakujeme vzdy, jinak dle poctu
            if repeat_every_Nbar is not None:
                #jiz bezelo - delame dalsi checky, pokud nebezelo, poustime jako true
                if last_run_index is not None:
                    required_bar_to_run = last_run_index + repeat_every_Nbar
                    if repeat_every_Nbar == 0:
                        state.ilog(lvl=0,e=f"IND {name} {subtype} RUN ONCE ALREADY at:{last_run_index} at:{last_run_time}", repeat_every_Nbar=repeat_every_Nbar, last_run_index=last_run_index)
                        cond = False 
                    elif repeat_every_Nbar == 1:
                        pass
                    elif data["index"] < required_bar_to_run:
                        state.ilog(lvl=0,e=f"IND {name} {subtype} REPEAT EVERY N BAR WAITING: req:{required_bar_to_run} now:{data['index']}", repeat_every_Nbar=repeat_every_Nbar, last_run_index=last_run_index)
                        cond = False
                  
            if cond is False:
                return cond, "repeat_every_Nbar not yet"

            #pokud nepozadovano, pak poustime
            if repeat_every_Nmin is not None:
                #porovnavame jen pokud uz bezelo
                if last_run_time is not None:
                    required_time_to_run = last_run_time + timedelta(minutes=repeat_every_Nmin)
                    datetime_now = datetime.fromtimestamp(data["updated"]).astimezone(zoneNY)
                    if datetime_now < required_time_to_run:
                        state.ilog(lvl=0,e=f"IND {name} {subtype} REPEAT EVERY {repeat_every_Nmin}MINS WAITING", last_run_time=last_run_time, required_time_to_run=required_time_to_run, datetime_now=datetime_now)
                        cond = False

            if cond is False:
                return cond, "repeat_every_Nmin not yet"

            return cond, "ok"

        #testing custom indicator CODE
        #TODO customer params bud implicitne **params nebo jako dict
        # return 0, new_val or -2, "err msg"
        def opengap(params):
            funcName = "opengap"
            param1 = safe_get(params, "param1")
            param2 = safe_get(params, "param2")
            state.ilog(lvl=0,e=f"INSIDE {funcName} {param1=} {param2=}", **params)
            last_close = 28.45
            today_open = 29.45
            val = pct_diff(last_close, today_open)
            return 0, val
            #random.randint(10, 20)

        #TODO error handling obecne v indicatorech
        # def average(params):
        #     funcName = "average"
        #     lookback = int(safe_get(params, "lookback",1))
        #     source = safe_get(params, "source", None)
        #     if source is None:
        #         state.ilog(lvl=1,e=f"INSIDE {funcName} source required 0", **params)
        #         return 0,0
            
        #     if source in ["open","high","low","close","vwap","hlcc4"]:
        #         source_series = state.bars[source]
        #     else:
        #         source_series = state.indicators[source]

        #     state.ilog(lvl=0,e=f"INSIDE {funcName}", source_series=source_series, **params)

        #     delka_pole = len(source_series)
        #     if delka_pole < lookback:
        #         lookback = delka_pole

        #     return 0, Average(source_series[-lookback:])

        #abs/rel divergence of two indicators
        def divergence(params):
            funcName = "indicatorDivergence"
            source1 = safe_get(params, "source1", None)
            if source1 in ["open","high","low","close","vwap","hlcc4"]:
                source1_series = state.bars[source1]
            else:
                source1_series = state.indicators[source1]
            source2 = safe_get(params, "source2", None)
            if source2 in ["open","high","low","close","vwap","hlcc4"]:
                source2_series = state.bars[source2]
            else:
                source2_series = state.indicators[source2]
            mode = safe_get(params, "type")
            state.ilog(lvl=0,e=f"INSIDE {funcName} {source1=} {source2=} {mode=}", **params)
            val = 0
            if mode == "abs":
                val =  round(abs(float(source1_series[-1]) - float(source2_series[-1])),4)
            elif mode == "absn":
                val =  round((abs(float(source1_series[-1]) - float(source2_series[-1])))/float(source1_series[-1]),4)
            elif mode == "rel":
                val =  round(float(source1_series[-1]) - float(source2_series[-1]),4)
            elif mode == "reln":
                val =  round((float(source1_series[-1]) - float(source2_series[-1]))/float(source1_series[-1]),4)
            elif mode == "pctabs":
                val = pct_diff(num1=float(source1_series[-1]),num2=float(source2_series[-1]), absolute=True)
            elif mode == "pct":
                val = pct_diff(num1=float(source1_series[-1]),num2=float(source2_series[-1]))
            return 0, val
        
        #rate of change - last value of source indicator vs lookback value of lookback_priceline indicator
        def slope(params):
            funcName = "slope"
            source = safe_get(params, "source", None)
            if source in ["open","high","low","close","vwap","hlcc4"]:
                source_series = state.bars[source]
            else:
                source_series = state.indicators[source]
                
            lookback = safe_get(params, "lookback", 5)
            lookback_priceline = safe_get(params, "lookback_priceline", None)
            if lookback_priceline is None:
                lookback_series = source_series
            elif lookback_priceline in  ["open","high","low","close","vwap","hlcc4"]:
                lookback_series = state.bars[lookback_priceline]
            else:
                lookback_series = state.indicators[lookback_priceline]

            try:
                lookbackprice = lookback_series[-lookback-1]
                lookbacktime = state.bars.updated[-lookback-1]
            except IndexError:
                max_delka = len(lookback_series)
                lookbackprice =lookback_series[-max_delka]
                lookbacktime = state.bars.updated[-max_delka]

            #výpočet úhlu - a jeho normalizace
            currval = source_series[-1]
            slope = ((currval - lookbackprice)/abs(lookbackprice))*100
            #slope = round(slope, 4)

            state.ilog(lvl=1,e=f"INSIDE {funcName} {slope} {source=} {lookback=}", currval_source=currval, lookbackprice=lookbackprice, lookbacktime=lookbacktime, **params)
            return 0, slope

        should_run, msg = is_time_to_run()

        if should_run:
            #TODO get custom params
            custom_params = safe_get(options, "cp", None)
            #vyplnime last_run_time a last_run_index
            state.vars.indicators[name]["last_run_time"] = datetime.fromtimestamp(data["updated"]).astimezone(zoneNY)
            state.vars.indicators[name]["last_run_index"] = data["index"]

            # - volame custom funkci pro ziskani hodnoty indikatoru
            #        - tu ulozime jako novou hodnotu indikatoru a prepocteme MAcka pokud je pozadovane
            # - pokud cas neni, nechavame puvodni, vcetna pripadneho MAcka
            #pozor jako defaultní hodnotu dává engine 0 - je to ok?
            try:
                custom_function = eval(subtype)
                res_code, new_val = custom_function(custom_params)
                if res_code == 0:
                    state.indicators[name][-1]=new_val
                    state.ilog(lvl=1,e=f"IND {name} {subtype} VAL FROM FUNCTION: {new_val}", lastruntime=state.vars.indicators[name]["last_run_time"], lastrunindex=state.vars.indicators[name]["last_run_index"])
                    #prepocitame MA if required
                    if MA_length is not None:
                        src = state.indicators[name][-MA_length:]
                        MA_res = ema(src, MA_length)
                        MA_value = round(MA_res[-1],7)
                        state.indicators[name+"MA"][-1]=MA_value
                        state.ilog(lvl=0,e=f"IND {name}MA {subtype} {MA_value}")

                else:
                    raise ValueError(f"IND  ERROR {name} {subtype}Funkce {custom_function} vratila {res_code} {new_val}.")
                
            except Exception as e:
                if len(state.indicators[name]) >= 2:
                    state.indicators[name][-1]=state.indicators[name][-2]
                if MA_length is not None and len(state.indicators[name+"MA"])>=2:
                    state.indicators[name+"MA"][-1]=state.indicators[name+"MA"][-2]
                state.ilog(lvl=1,e=f"IND ERROR {name} {subtype} necháváme původní", message=str(e)+format_exc())
        
        else:
            state.ilog(lvl=0,e=f"IND {name} {subtype} COND NOT READY: {msg}")

            #not time to run
            if len(state.indicators[name]) >= 2:
                state.indicators[name][-1]=state.indicators[name][-2]

            if MA_length is not None and len(state.indicators[name+"MA"])>=2:
                state.indicators[name+"MA"][-1]=state.indicators[name+"MA"][-2]

            state.ilog(lvl=0,e=f"IND {name} {subtype} NOT TIME TO RUN - value(and MA) still original")            
    
    #EMA INDICATOR
    # type = EMA, source = [close, vwap, hlcc4], length = [14], on_confirmed_only = [true, false]
    def populate_dynamic_ema_indicator(name):
        ind_type = "EMA"
        options = safe_get(state.vars.indicators, name, None)
        if options is None:
            state.ilog(lvl=1,e=f"No options for {name} in stratvars")
            return       
        
        if safe_get(options, "type", False) is False or safe_get(options, "type", False) != ind_type:
            state.ilog(lvl=1,e="Type error")
            return
        
        #poustet kazdy tick nebo jenom na confirmed baru (on_confirmed_only = true)
        on_confirmed_only = safe_get(options, 'on_confirmed_only', False)
        req_source = safe_get(options, 'source', 'vwap')
        if req_source not in ["close", "vwap","hlcc4"]:
            state.ilog(lvl=1,e=f"Unknown source error {req_source} for {name}")
            return
        ema_length = int(safe_get(options, "length",14))
        if on_confirmed_only is False or (on_confirmed_only is True and data['confirmed']==1):
            try:
                source = state.bars[req_source][-ema_length:]
                #if len(source) > ema_length:
                ema_value = ema(source, ema_length)
                val = round(ema_value[-1],4)
                state.indicators[name][-1]= val
                #state.indicators[name][-1]= round2five(val)
                state.ilog(lvl=0,e=f"IND {name} EMA {val} {ema_length=}")
                #else:
                #    state.ilog(lvl=0,e=f"IND {name} EMA necháváme 0", message="not enough source data", source=source, ema_length=ema_length)
            except Exception as e:
                state.ilog(lvl=1,e=f"IND ERROR {name} EMA necháváme 0", message=str(e)+format_exc())

    #NATR INDICATOR
    # type = NATR, ĺength = [14], on_confirmed_only = [true, false]
    def populate_dynamic_natr_indicator(name):
        ind_type = "NATR"
        options = safe_get(state.vars.indicators, name, None)
        if options is None:
            state.ilog(lvl=1,e=f"No options for {name} in stratvars")
            return       
        
        #poustet kazdy tick nebo jenom na confirmed baru (on_confirmed_only = true)
        on_confirmed_only = safe_get(options, 'on_confirmed_only', False)
        natr_length = int(safe_get(options, "length",5))
        if on_confirmed_only is False or (on_confirmed_only is True and data['confirmed']==1):
            try:
                source_high = state.bars["high"][-natr_length:]
                source_low = state.bars["low"][-natr_length:]
                source_close = state.bars["close"][-natr_length:]
                #if len(source) > ema_length:
                natr_value = natr(source_high, source_low, source_close, natr_length)
                val = round(natr_value[-1],4)
                state.indicators[name][-1]= val
                #state.indicators[name][-1]= round2five(val)
                state.ilog(lvl=0,e=f"IND {name} NATR {val} {natr_length=}")
                #else:
                #    state.ilog(lvl=0,e=f"IND {name} EMA necháváme 0", message="not enough source data", source=source, ema_length=ema_length)
            except Exception as e:
                state.ilog(lvl=0,e=f"IND ERROR {name} NATR necháváme 0", message=str(e)+format_exc())

    #RSI INDICATOR
    # type = RSI, source = [close, vwap, hlcc4], rsi_length = [14], MA_length = int (optional), on_confirmed_only = [true, false]
    # pokud existuje MA, vytvarime i stejnojnojmenny MAcko
    def populate_dynamic_RSI_indicator(name):
        ind_type = "RSI"
        options = safe_get(state.vars.indicators, name, None)
        if options is None:
            state.ilog(lvl=1,e=f"No options for {name} in stratvars")
            return       
        
        if safe_get(options, "type", False) is False or safe_get(options, "type", False) != ind_type:
            state.ilog(lvl=1,e="Type error")
            return
        
        #poustet kazdy tick nebo jenom na confirmed baru (on_confirmed_only = true)
        on_confirmed_only = safe_get(options, 'on_confirmed_only', False)
        req_source = safe_get(options, 'source', 'vwap')
        if req_source not in ["close", "vwap","hlcc4"]:
            state.ilog(lvl=1,e=f"Unknown source error {req_source} for {name}")
            return
        rsi_length = int(safe_get(options, "RSI_length",14))
        rsi_MA_length = safe_get(options, "MA_length", None)

        if on_confirmed_only is False or (on_confirmed_only is True and data['confirmed']==1):
            try:
                source = state.bars[req_source]
                #cekame na dostatek dat
                if len(source) > rsi_length:
                    rsi_res = rsi(source, rsi_length)
                    rsi_value = round(rsi_res[-1],4)
                    state.indicators[name][-1]=rsi_value
                    state.ilog(lvl=0,e=f"IND {name} RSI {rsi_value}")

                    if rsi_MA_length is not None:
                        src = state.indicators[name][-rsi_MA_length:]
                        rsi_MA_res = ema(src, rsi_MA_length)
                        rsi_MA_value = round(rsi_MA_res[-1],4)
                        state.indicators[name+"MA"][-1]=rsi_MA_value
                        state.ilog(lvl=0,e=f"IND {name} RSIMA {rsi_MA_value}")

                else:
                    state.ilog(lvl=0,e=f"IND {name} RSI necháváme 0", message="not enough source data", source=source, rsi_length=rsi_length)
            except Exception as e:
                state.ilog(lvl=1,e=f"IND ERROR {name} RSI necháváme 0", message=str(e)+format_exc())

    #SLOPE LP
    def populate_dynamic_slopeLP_indicator(name):
        ind_type = "slopeLP"
        options = safe_get(state.vars.indicators, name, None)
        if options is None:
            state.ilog(lvl=1,e=f"No options for {name} in stratvars")
            return
        
        if safe_get(options, "type", False) is False or safe_get(options, "type", False) != ind_type:
            state.ilog(lvl=1,e="Type error")
            return
        
        #poustet kazdy tick nebo jenom na confirmed baru (on_confirmed_only = true)
        on_confirmed_only = safe_get(options, 'on_confirmed_only', False)

        #pocet baru po kterých se levy bod z BUY prepne opet na standadni vypocet (prumer)
        #kdyz se dlouho neprodává a cena nejde dolu, tak aby se nezastavilo nakupovani
        back_to_standard_after = int(safe_get(options, 'back_to_standard_after', 0))

        #slopeLP INDIKATOR
        #levy bod je nejdrive standardne automaticky vypočtený podle hodnoty lookbacku (např. -8, offset 4)
        #při nákupu se BUY POINT se stává levým bodem (až do doby kdy není lookbackprice nižší, pak pokračuje lookbackprice)
        #při prodeji se SELL POINT se stává novým levým bodem (až do doby kdy není lookbackprice vyšší, pak pokračuje lookbackprice)
        #zatím implementovat prvni část (mimo části ..až do doby) - tu pak dodelat podle vysledku, pripadne ji neimplementovat vubec a misto toho 
        #udelat slope RESET pri dosazeni urciteho pozitivniho nebo negativni slopu

        #zkusime nejdriv: levy bod automat, po nakupu je levy bod cena nakupu

        #VYSTUPY:    state.indicators[name], 
        #            state.indicators[nameMA]
        #            statický indikátor (angle) - stejneho jmena pro vizualizaci uhlu

        if on_confirmed_only is False or (on_confirmed_only is True and data['confirmed']==1):
            try:
                #slow_slope = 99
                slope_lookback = safe_get(options, 'slope_lookback', 100)
                minimum_slope =  safe_get(options, 'minimum_slope', 25)
                maximum_slope = safe_get(options, "maximum_slope",0.9)
                lookback_offset = safe_get(options, 'lookback_offset', 25)
                
                #typ leveho bodu [lastbuy - cena posledniho nakupu, baropen - cena otevreni baru]
                leftpoint = safe_get(options, 'leftpoint', "lastbuy")

                #lookback has to be even
                if lookback_offset % 2 != 0:
                    lookback_offset += 1

                if leftpoint == "lastbuy":
                    if len(state.bars.close) > (slope_lookback + lookback_offset):
                        #test prumer nejvyssi a nejnizsi hodnoty 
                        # if name == "slope":

                        #levy bod bude vzdy vzdaleny o slope_lookback
                        #ten bude prumerem hodnot lookback_offset a to tak ze polovina offsetu z kazde strany
                        array_od = slope_lookback + int(lookback_offset/2)
                        array_do = slope_lookback - int(lookback_offset/2)
                        lookbackprice_array = state.bars.vwap[-array_od:-array_do]
                        #cas nastavujeme vzdy podle nastaveni (zatim)
                        lookbacktime = state.bars.time[-slope_lookback]

                        #pokud mame aktivni pozice, nastavime lookbackprice a time podle posledniho tradu
                        #pokud se ale dlouho nenakupuje (uplynulo od posledniho nakupu vic nez back_to_standard_after baru), tak se vracime k prumeru
                        if state.avgp > 0 and state.bars.index[-1] < int(state.vars.last_buy_index)+back_to_standard_after:
                            lb_index = -1 - (state.bars.index[-1] - int(state.vars.last_buy_index))
                            lookbackprice = state.bars.vwap[lb_index]
                            state.ilog(lvl=0,e=f"IND {name} slope {leftpoint}- LEFT POINT OVERRIDE bereme ajko cenu lastbuy {lookbackprice=} {lookbacktime=} {lb_index=}")
                        else:
                            #dame na porovnani jen prumer
                            lookbackprice = round(sum(lookbackprice_array)/lookback_offset,3)
                                #lookbackprice = round((min(lookbackprice_array)+max(lookbackprice_array))/2,3)
                            # else:
                            #     #puvodni lookback a od te doby dozadu offset
                            #     array_od = slope_lookback + lookback_offset
                            #     array_do = slope_lookback
                            #     lookbackprice_array = state.bars.vwap[-array_od:-array_do]
                            #     #obycejný prumer hodnot
                            #     lookbackprice = round(sum(lookbackprice_array)/lookback_offset,3)
                            
                            lookbacktime = state.bars.time[-slope_lookback]
                            state.ilog(lvl=0,e=f"IND {name} slope {leftpoint} - LEFT POINT STANDARD {lookbackprice=} {lookbacktime=}")
                    else:
                        #kdyz neni  dostatek hodnot, pouzivame jako levy bod open hodnotu close[0]
                        lookbackprice = state.bars.close[0]
                        lookbacktime = state.bars.time[0]
                        state.ilog(lvl=0,e=f"IND {name} slope - not enough data bereme left bod open", slope_lookback=slope_lookback)
                elif leftpoint == "baropen":
                    lookbackprice = state.bars.open[-1]
                    lookbacktime = state.bars.time[-1]
                    state.ilog(lvl=0,e=f"IND {name} slope {leftpoint}- bereme cenu bar OPENu ", lookbackprice=lookbackprice, lookbacktime=lookbacktime)
                else:
                    state.ilog(lvl=0,e=f"IND {name} UNKNOW LEFT POINT TYPE {leftpoint=}")

                #výpočet úhlu - a jeho normalizace
                slope = ((state.bars.close[-1] - lookbackprice)/lookbackprice)*100
                slope = round(slope, 4)
                state.indicators[name][-1]=slope

                #angle ze slope
                state.statinds[name] = dict(time=state.bars.updated[-1], price=state.bars.close[-1], lookbacktime=lookbacktime, lookbackprice=lookbackprice, minimum_slope=minimum_slope, maximum_slope=maximum_slope)

                #slope MA vyrovna vykyvy ve slope
                slope_MA_length = safe_get(options, 'MA_length', None)
                slopeMA = None
                last_slopesMA = None
                #pokud je nastavena MA_length tak vytvarime i MAcko dane delky na tento slope
                if slope_MA_length is not None:
                    source = state.indicators[name][-slope_MA_length:]
                    slopeMAseries = ema(source, slope_MA_length) #state.bars.vwap
                    slopeMA = round(slopeMAseries[-1],5)
                    state.indicators[name+"MA"][-1]=slopeMA
                    last_slopesMA = state.indicators[name+"MA"][-10:]

                state.ilog(lvl=0,e=f"{name=} {slope=} {slopeMA=}", msg=f"{lookbackprice=}", lookbackoffset=lookback_offset, minimum_slope=minimum_slope, last_slopes=state.indicators[name][-10:], last_slopesMA=last_slopesMA)
                #dale pracujeme s timto MAckovanym slope
                #slope = slopeMA         

            except Exception as e:
                print(f"Exception in {name} slope Indicator section", str(e))
                state.ilog(lvl=1,e=f"EXCEPTION in {name}", msg="Exception in slope Indicator section" + str(e) + format_exc())

    def populate_dynamic_slope_indicator(name):
        options = safe_get(state.vars.indicators, name, None)
        if options is None:
            state.ilog(lvl=1,e="No options for slow slope in stratvars")
            return
        
        if safe_get(options, "type", False) is False or safe_get(options, "type", False) != "slope":
            state.ilog(lvl=1,e="Type error")
            return
        
        #poustet kazdy tick nebo jenom na confirmed baru (on_confirmed_only = true)
        on_confirmed_only = safe_get(options, 'on_confirmed_only', False)

        #SLOW SLOPE INDICATOR
        #úhel stoupání a klesání vyjádřený mezi -1 až 1
        #pravý bod přímky je aktuální cena, levý je průměr X(lookback offset) starších hodnot od slope_lookback.
        #VYSTUPY:    state.indicators[name], 
        #            state.indicators[nameMA]
        #            statický indikátor (angle) - stejneho jmena pro vizualizaci uhlu

        if on_confirmed_only is False or (on_confirmed_only is True and data['confirmed']==1):
            try:
                slope_lookback = safe_get(options, 'slope_lookback', 100)
                lookback_priceline = safe_get(options, 'lookback_priceline', None)
                lookback_offset = safe_get(options, 'lookback_offset', 25)
                minimum_slope =  safe_get(options, 'minimum_slope', 25)
                maximum_slope = safe_get(options, "maximum_slope",0.9)

                #jako levy body pouzivame lookback_priceline INDIKATOR vzdaleny slope_lookback barů
                if lookback_priceline is not None:
                        try:
                            lookbackprice = state.indicators[lookback_priceline][-slope_lookback-1]
                            lookbacktime = state.bars.updated[-slope_lookback-1]
                        except IndexError:
                            max_delka = len(state.indicators[lookback_priceline])
                            lookbackprice = state.indicators[lookback_priceline][-max_delka]
                            lookbacktime = state.bars.updated[-max_delka]

                else:
                #NEMAME LOOKBACK PRICLINE - pouzivame stary způsob výpočtu, toto pozdeji decomissionovat
                    #lookback has to be even
                    if lookback_offset % 2 != 0:
                        lookback_offset += 1

                    #TBD pripdadne /2
                    if len(state.bars.close) > (slope_lookback + lookback_offset):
                        #test prumer nejvyssi a nejnizsi hodnoty 
                        # if name == "slope":

                        #levy bod bude vzdy vzdaleny o slope_lookback
                        #ten bude prumerem hodnot lookback_offset a to tak ze polovina offsetu z kazde strany
                        array_od = slope_lookback + int(lookback_offset/2)
                        array_do = slope_lookback - int(lookback_offset/2)
                        lookbackprice_array = state.bars.vwap[-array_od:-array_do]

                            #dame na porovnani jen prumer
                        lookbackprice = round(sum(lookbackprice_array)/lookback_offset,3)
                            #lookbackprice = round((min(lookbackprice_array)+max(lookbackprice_array))/2,3)
                        # else:
                        #     #puvodni lookback a od te doby dozadu offset
                        #     array_od = slope_lookback + lookback_offset
                        #     array_do = slope_lookback
                        #     lookbackprice_array = state.bars.vwap[-array_od:-array_do]
                        #     #obycejný prumer hodnot
                        #     lookbackprice = round(sum(lookbackprice_array)/lookback_offset,3)
                        
                        lookbacktime = state.bars.time[-slope_lookback]
                    else:
                        #kdyz neni  dostatek hodnot, pouzivame jako levy bod open hodnotu close[0]
                        #lookbackprice = state.bars.vwap[0]
                        
                        #dalsi vyarianta-- lookback je pole z toho všeho co mame
                        #lookbackprice = Average(state.bars.vwap)

                        

                        #pokud neni dostatek, bereme vzdy prvni petinu z dostupnych barů
                        # a z ní uděláme průměr
                        cnt = len(state.bars.close)
                        if cnt>5:
                            sliced_to = int(cnt/5)
                            lookbackprice= Average(state.bars.vwap[:sliced_to])
                            lookbacktime = state.bars.time[int(sliced_to/2)]
                        else:
                            lookbackprice = Average(state.bars.vwap)
                            lookbacktime = state.bars.time[0]
                        
                        state.ilog(lvl=1,e=f"IND {name} slope - not enough data bereme left bod open", slope_lookback=slope_lookback, lookbackprice=lookbackprice)

                #výpočet úhlu - a jeho normalizace
                slope = ((state.bars.close[-1] - lookbackprice)/lookbackprice)*100
                slope = round(slope, 4)
                state.indicators[name][-1]=slope

                #angle je ze slope, ale pojmenovavame ho podle MA
                state.statinds[name] = dict(time=state.bars.time[-1], price=state.bars.close[-1], lookbacktime=lookbacktime, lookbackprice=lookbackprice, minimum_slope=minimum_slope, maximum_slope=maximum_slope)

                #slope MA vyrovna vykyvy ve slope
                slope_MA_length = safe_get(options, 'MA_length', None)
                slopeMA = None
                last_slopesMA = None
                #pokud je nastavena MA_length tak vytvarime i MAcko dane delky na tento slope
                if slope_MA_length is not None:
                    source = state.indicators[name][-slope_MA_length:]
                    slopeMAseries = ema(source, slope_MA_length) #state.bars.vwap
                    slopeMA = round(slopeMAseries[-1],4)
                    state.indicators[name+"MA"][-1]=slopeMA
                    last_slopesMA = state.indicators[name+"MA"][-10:]

                lb_priceline_string = "from "+lookback_priceline if lookback_priceline is not None else ""

                state.ilog(lvl=1,e=f"IND {name} {lb_priceline_string} {slope=} {slopeMA=}", msg=f"{lookbackprice=} {lookbacktime=}", lookback_priceline=lookback_priceline, lookbackprice=lookbackprice, lookbacktime=lookbacktime, slope_lookback=slope_lookback, lookbackoffset=lookback_offset, minimum_slope=minimum_slope, last_slopes=state.indicators[name][-10:], last_slopesMA=last_slopesMA)
                #dale pracujeme s timto MAckovanym slope
                #slope = slopeMA         

            except Exception as e:
                print(f"Exception in {name} slope Indicator section", str(e))
                state.ilog(lvl=1,e=f"EXCEPTION in {name}", msg="Exception in slope Indicator section" + str(e) + format_exc())

    def process_delta():
        #PROCESs DELTAS - to function
        last_update_delta = round((float(data['updated']) - state.vars.last_update_time),6) if state.vars.last_update_time != 0 else 0
        state.vars.last_update_time = float(data['updated'])

        if len(state.vars.last_50_deltas) >=50:
            state.vars.last_50_deltas.pop(0)
        state.vars.last_50_deltas.append(last_update_delta)
        avg_delta = Average(state.vars.last_50_deltas)

        state.ilog(lvl=1,e=f"-----{data['index']}-{conf_bar}--delta:{last_update_delta}---AVGdelta:{avg_delta}", data=data)

    conf_bar = data['confirmed']
    process_delta()
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
        populate_cbar_tick_price_indicator()
        #TBD nize predelat na typizovane RSI (a to jak na urovni CBAR tak confirmed)
        populate_cbar_rsi_indicator()

    #populate indicators, that have type in stratvars.indicators
    populate_dynamic_indicators()
    # endregion

    # region Subfunction

    def dontexit_protection_met(direction: TradeDirection):
        if direction == TradeDirection.LONG:
            smer = "long"
        else:
            smer = "short"

        mother_signal = state.vars.activeTrade.generated_by

        if mother_signal is not None:
            #TESTUJEME DONT_EXIT_
            cond_dict = state.vars.conditions[KW.dont_exit][mother_signal][smer]
            #OR 
            result, conditions_met = evaluate_directive_conditions(cond_dict, "OR")
            state.ilog(lvl=1,e=f"DONT_EXIT {mother_signal} {smer} =OR= {result}", **conditions_met, cond_dict=cond_dict)
            if result:
                return True
            
            #OR neprosly testujeme AND
            result, conditions_met = evaluate_directive_conditions(cond_dict, "AND")
            state.ilog(lvl=1,e=f"DONT_EXIT {mother_signal}  {smer} =AND= {result}", **conditions_met, cond_dict=cond_dict)
            if result:
                return True
            
        cond_dict = state.vars.conditions[KW.dont_exit]["common"][smer]            
        #OR 
        result, conditions_met = evaluate_directive_conditions(cond_dict, "OR")
        state.ilog(lvl=1,e=f"DONT_EXIT common {smer} =OR= {result}", **conditions_met, cond_dict=cond_dict)
        if result:
            return True
        
        #OR neprosly testujeme AND
        result, conditions_met = evaluate_directive_conditions(cond_dict, "AND")
        state.ilog(lvl=1,e=f"DONT_EXIT common {smer} =AND= {result}", **conditions_met, cond_dict=cond_dict)
        return result

    def normalize_tick(tick: float, price: float = None, return_two_decimals: bool = False):
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

    #funkce pro direktivy, ktere muzou byt overridnute v signal sekci
    #tato funkce vyhleda signal sekci aktivniho tradu a pokusi se danou direktivu vyhledat tam,
    #pokud nenajde tak vrati default, ktery byl poskytnut
    def get_override_for_active_trade(directive_name: str, default_value: str):
        val = default_value
        override = "NO"
        mother_signal = state.vars.activeTrade.generated_by

        if mother_signal is not None:
            override = "YES "+mother_signal
            val = safe_get(state.vars.signals[mother_signal], directive_name, default_value)

        state.ilog(lvl=0,e=f"{directive_name} OVERRIDE {override} NEWVAL:{val} ORIGINAL:{default_value} {mother_signal}", mother_signal=mother_signal,default_value=default_value)
        return val

    def get_default_sl_value(direction: TradeDirection):

        if direction == TradeDirection.LONG:
            smer = "long"
        else:
            smer = "short"
        
        #TODO zda signal, ktery activeTrade vygeneroval, nema vlastni nastaveni + fallback na general

        options = safe_get(state.vars, 'exit', None)

        if options is None:
            state.ilog(lvl=1,e="No options for exit in stratvars. Fallback.")
            return 0.01
        directive_name = 'SL_defval_'+str(smer)
        val = get_override_for_active_trade(directive_name=directive_name, default_value=safe_get(options, directive_name, 0.01))
        return val

    def get_profit_target_price():
        directive_name = "profit"
        def_profit = get_override_for_active_trade(directive_name=directive_name, default_value=safe_get(state.vars, directive_name, 0.50))

        normalized_def_profit = normalize_tick(float(def_profit))

        state.ilog(lvl=0,e=f"PROFIT {def_profit=} {normalized_def_profit=}")

        return price2dec(float(state.avgp)+normalized_def_profit,3) if int(state.positions) > 0 else price2dec(float(state.avgp)-normalized_def_profit,3)
        
    def get_max_profit_price():
        directive_name = "max_profit"
        max_profit = get_override_for_active_trade(directive_name=directive_name, default_value=safe_get(state.vars, directive_name, 0.35))

        normalized_max_profit = normalize_tick(float(max_profit))

        state.ilog(lvl=0,e=f"MAX PROFIT {max_profit=} {normalized_max_profit=}")

        return price2dec(float(state.avgp)+normalized_max_profit,3) if int(state.positions) > 0 else price2dec(float(state.avgp)-normalized_max_profit,3)    

    #otestuje keyword podminky (napr. reverse_if, nebo exitadd_if)
    def keyword_conditions_met(direction: TradeDirection, keyword: KW):
            action = str(keyword).upper()
            if direction == TradeDirection.LONG:
                smer = "long"
            else:
                smer = "short"

            directive_name = "exit_cond_only_on_confirmed"
            exit_cond_only_on_confirmed = get_override_for_active_trade(directive_name=directive_name, default_value=safe_get(state.vars, directive_name, False))

            if exit_cond_only_on_confirmed and data['confirmed'] == 0:
                state.ilog(lvl=0,e=f"{action} CHECK COND ONLY ON CONFIRMED BAR")
                return False

            #TOTO zatim u REVERSU neresime
            # #POKUD je nastaven MIN PROFIT, zkontrolujeme ho a az pripadne pustime CONDITIONY
            # directive_name = "exit_cond_min_profit"
            # exit_cond_min_profit = get_override_for_active_trade(directive_name=directive_name, default_value=safe_get(state.vars, directive_name, None))

            # #máme nastavený exit_cond_min_profit
            # # zjistíme, zda jsme v daném profit a případně nepustíme dál
            # # , zjistíme aktuální cenu a přičteme k avgp tento profit a podle toho pustime dal

            # if exit_cond_min_profit is not None:
            #     exit_cond_min_profit_normalized = normalize_tick(float(exit_cond_min_profit))
            #     exit_cond_goal_price = price2dec(float(state.avgp)+exit_cond_min_profit_normalized,3) if int(state.positions) > 0 else price2dec(float(state.avgp)-exit_cond_min_profit_normalized,3) 
            #     curr_price = float(data["close"])
            #     state.ilog(lvl=0,e=f"EXIT COND min profit {exit_cond_goal_price=} {exit_cond_min_profit=} {exit_cond_min_profit_normalized=} {curr_price=}")
            #     if (int(state.positions) < 0 and curr_price<=exit_cond_goal_price) or (int(state.positions) > 0 and curr_price>=exit_cond_goal_price):
            #         state.ilog(lvl=0,e=f"EXIT COND min profit PASS - POKRACUJEME")
            #     else:
            #         state.ilog(lvl=0,e=f"EXIT COND min profit NOT PASS")
            #         return False

            #TOTO ZATIM NEMA VYZNAM
            # options = safe_get(state.vars, 'exit_conditions', None)
            # if options is None:
            #     state.ilog(lvl=0,e="No options for exit conditions in stratvars")
            #     return False
            
            # disable_exit_proteciton_when = dict(AND=dict(), OR=dict())

            # #preconditions
            # disable_exit_proteciton_when['disabled_in_config'] = safe_get(options, 'enabled', False) is False
            # #too good to be true (maximum profit)
            # #disable_sell_proteciton_when['tgtbt_reached'] = safe_get(options, 'tgtbt', False) is False
            # disable_exit_proteciton_when['disable_if_positions_above'] = int(safe_get(options, 'disable_if_positions_above', 0)) < abs(int(state.positions))

            # #testing preconditions
            # result, conditions_met = eval_cond_dict(disable_exit_proteciton_when)
            # if result:
            #     state.ilog(lvl=0,e=f"EXIT_CONDITION for{smer} DISABLED by {conditions_met}", **conditions_met)
            #     return False
            
            #bereme bud exit condition signalu, ktery activeTrade vygeneroval+ fallback na general
            state.ilog(lvl=0,e=f"{action} CONDITIONS ENTRY {smer}", conditions=state.vars.conditions[KW.reverse])

            mother_signal = state.vars.activeTrade.generated_by

            if mother_signal is not None:
                cond_dict = state.vars.conditions[keyword][mother_signal][smer]
                result, conditions_met = evaluate_directive_conditions(cond_dict, "OR")
                state.ilog(lvl=1,e=f"{action} CONDITIONS of {mother_signal} =OR= {result}", **conditions_met, cond_dict=cond_dict)
                if result:
                    return True
                
                #OR neprosly testujeme AND
                result, conditions_met = evaluate_directive_conditions(cond_dict, "AND")
                state.ilog(lvl=1,e=f"{action} CONDITIONS of {mother_signal}  =AND= {result}", **conditions_met, cond_dict=cond_dict)
                if result:
                    return True


            #pokud nemame mother signal nebo exit nevratil nic, fallback na common
            cond_dict = state.vars.conditions[keyword]["common"][smer]
            result, conditions_met = evaluate_directive_conditions(cond_dict, "OR")
            state.ilog(lvl=1,e=f"{action} CONDITIONS of COMMON =OR= {result}", **conditions_met, cond_dict=cond_dict)
            if result:
                return True
            
            #OR neprosly testujeme AND
            result, conditions_met = evaluate_directive_conditions(cond_dict, "AND")
            state.ilog(lvl=0,e=f"{action} CONDITIONS of COMMON =AND= {result}", **conditions_met, cond_dict=cond_dict)
            if result:
                return True

    #DECOMISSIONOVANI  - nahrazeno obacnou keyword_conditions_met
    # def reverse_conditions_met(direction: TradeDirection):
    #         if direction == TradeDirection.LONG:
    #             smer = "long"
    #         else:
    #             smer = "short"

    #         directive_name = "exit_cond_only_on_confirmed"
    #         exit_cond_only_on_confirmed = get_override_for_active_trade(directive_name=directive_name, default_value=safe_get(state.vars, directive_name, False))

    #         if exit_cond_only_on_confirmed and data['confirmed'] == 0:
    #             state.ilog(lvl=0,e="REVERSAL CHECK COND ONLY ON CONFIRMED BAR")
    #             return False

    #         #TOTO zatim u REVERSU neresime
    #         # #POKUD je nastaven MIN PROFIT, zkontrolujeme ho a az pripadne pustime CONDITIONY
    #         # directive_name = "exit_cond_min_profit"
    #         # exit_cond_min_profit = get_override_for_active_trade(directive_name=directive_name, default_value=safe_get(state.vars, directive_name, None))

    #         # #máme nastavený exit_cond_min_profit
    #         # # zjistíme, zda jsme v daném profit a případně nepustíme dál
    #         # # , zjistíme aktuální cenu a přičteme k avgp tento profit a podle toho pustime dal

    #         # if exit_cond_min_profit is not None:
    #         #     exit_cond_min_profit_normalized = normalize_tick(float(exit_cond_min_profit))
    #         #     exit_cond_goal_price = price2dec(float(state.avgp)+exit_cond_min_profit_normalized,3) if int(state.positions) > 0 else price2dec(float(state.avgp)-exit_cond_min_profit_normalized,3) 
    #         #     curr_price = float(data["close"])
    #         #     state.ilog(lvl=0,e=f"EXIT COND min profit {exit_cond_goal_price=} {exit_cond_min_profit=} {exit_cond_min_profit_normalized=} {curr_price=}")
    #         #     if (int(state.positions) < 0 and curr_price<=exit_cond_goal_price) or (int(state.positions) > 0 and curr_price>=exit_cond_goal_price):
    #         #         state.ilog(lvl=0,e=f"EXIT COND min profit PASS - POKRACUJEME")
    #         #     else:
    #         #         state.ilog(lvl=0,e=f"EXIT COND min profit NOT PASS")
    #         #         return False

    #         #TOTO ZATIM NEMA VYZNAM
    #         # options = safe_get(state.vars, 'exit_conditions', None)
    #         # if options is None:
    #         #     state.ilog(lvl=0,e="No options for exit conditions in stratvars")
    #         #     return False
            
    #         # disable_exit_proteciton_when = dict(AND=dict(), OR=dict())

    #         # #preconditions
    #         # disable_exit_proteciton_when['disabled_in_config'] = safe_get(options, 'enabled', False) is False
    #         # #too good to be true (maximum profit)
    #         # #disable_sell_proteciton_when['tgtbt_reached'] = safe_get(options, 'tgtbt', False) is False
    #         # disable_exit_proteciton_when['disable_if_positions_above'] = int(safe_get(options, 'disable_if_positions_above', 0)) < abs(int(state.positions))

    #         # #testing preconditions
    #         # result, conditions_met = eval_cond_dict(disable_exit_proteciton_when)
    #         # if result:
    #         #     state.ilog(lvl=0,e=f"EXIT_CONDITION for{smer} DISABLED by {conditions_met}", **conditions_met)
    #         #     return False
            
    #         #bereme bud exit condition signalu, ktery activeTrade vygeneroval+ fallback na general
    #         state.ilog(lvl=0,e=f"REVERSE CONDITIONS ENTRY {smer}", conditions=state.vars.conditions[KW.reverse])

    #         mother_signal = state.vars.activeTrade.generated_by

    #         if mother_signal is not None:
    #             cond_dict = state.vars.conditions[KW.reverse][state.vars.activeTrade.generated_by][smer]
    #             result, conditions_met = evaluate_directive_conditions(cond_dict, "OR")
    #             state.ilog(lvl=1,e=f"REVERSE CONDITIONS of {mother_signal} =OR= {result}", **conditions_met, cond_dict=cond_dict)
    #             if result:
    #                 return True
                
    #             #OR neprosly testujeme AND
    #             result, conditions_met = evaluate_directive_conditions(cond_dict, "AND")
    #             state.ilog(lvl=1,e=f"REVERSE CONDITIONS of {mother_signal}  =AND= {result}", **conditions_met, cond_dict=cond_dict)
    #             if result:
    #                 return True


    #         #pokud nemame mother signal nebo exit nevratil nic, fallback na common
    #         cond_dict = state.vars.conditions[KW.reverse]["common"][smer]
    #         result, conditions_met = evaluate_directive_conditions(cond_dict, "OR")
    #         state.ilog(lvl=1,e=f"REVERSE CONDITIONS of COMMON =OR= {result}", **conditions_met, cond_dict=cond_dict)
    #         if result:
    #             return True
            
    #         #OR neprosly testujeme AND
    #         result, conditions_met = evaluate_directive_conditions(cond_dict, "AND")
    #         state.ilog(lvl=0,e=f"REVERSE CONDITIONS of COMMON =AND= {result}", **conditions_met, cond_dict=cond_dict)
    #         if result:
    #             return True

    def exit_conditions_met(direction: TradeDirection):
        if direction == TradeDirection.LONG:
            smer = "long"
        else:
            smer = "short"

        directive_name = "exit_cond_only_on_confirmed"
        exit_cond_only_on_confirmed = get_override_for_active_trade(directive_name=directive_name, default_value=safe_get(state.vars, directive_name, False))

        if exit_cond_only_on_confirmed and data['confirmed'] == 0:
            state.ilog(lvl=0,e="EXIT COND ONLY ON CONFIRMED BAR")
            return False
        
        ## minimální počet barů od vstupu
        directive_name = "exit_cond_req_bars"
        exit_cond_req_bars = get_override_for_active_trade(directive_name=directive_name, default_value=safe_get(state.vars, directive_name, 1))

        if state.vars.last_in_index is not None:
            index_to_compare = int(state.vars.last_in_index)+int(exit_cond_req_bars) 
            if int(data["index"]) < index_to_compare:
                state.ilog(lvl=1,e=f"EXIT COND WAITING on required bars from IN {exit_cond_req_bars} TOO SOON", currindex=data["index"], index_to_compare=index_to_compare, last_in_index=state.vars.last_in_index)
                return False

        #POKUD je nastaven MIN PROFIT, zkontrolujeme ho a az pripadne pustime CONDITIONY
        directive_name = "exit_cond_min_profit"
        exit_cond_min_profit = get_override_for_active_trade(directive_name=directive_name, default_value=safe_get(state.vars, directive_name, None))

        #máme nastavený exit_cond_min_profit
        # zjistíme, zda jsme v daném profit a případně nepustíme dál
        # , zjistíme aktuální cenu a přičteme k avgp tento profit a podle toho pustime dal

        if exit_cond_min_profit is not None:
            exit_cond_min_profit_normalized = normalize_tick(float(exit_cond_min_profit))
            exit_cond_goal_price = price2dec(float(state.avgp)+exit_cond_min_profit_normalized,3) if int(state.positions) > 0 else price2dec(float(state.avgp)-exit_cond_min_profit_normalized,3) 
            curr_price = float(data["close"])
            state.ilog(lvl=1,e=f"EXIT COND min profit {exit_cond_goal_price=} {exit_cond_min_profit=} {exit_cond_min_profit_normalized=} {curr_price=}")
            if (int(state.positions) < 0 and curr_price<=exit_cond_goal_price) or (int(state.positions) > 0 and curr_price>=exit_cond_goal_price):
                state.ilog(lvl=1,e=f"EXIT COND min profit PASS - POKRACUJEME")
            else:
                state.ilog(lvl=1,e=f"EXIT COND min profit NOT PASS")
                return False

        #TOTO ZATIM NEMA VYZNAM
        # options = safe_get(state.vars, 'exit_conditions', None)
        # if options is None:
        #     state.ilog(lvl=0,e="No options for exit conditions in stratvars")
        #     return False
        
        # disable_exit_proteciton_when = dict(AND=dict(), OR=dict())

        # #preconditions
        # disable_exit_proteciton_when['disabled_in_config'] = safe_get(options, 'enabled', False) is False
        # #too good to be true (maximum profit)
        # #disable_sell_proteciton_when['tgtbt_reached'] = safe_get(options, 'tgtbt', False) is False
        # disable_exit_proteciton_when['disable_if_positions_above'] = int(safe_get(options, 'disable_if_positions_above', 0)) < abs(int(state.positions))

        # #testing preconditions
        # result, conditions_met = eval_cond_dict(disable_exit_proteciton_when)
        # if result:
        #     state.ilog(lvl=0,e=f"EXIT_CONDITION for{smer} DISABLED by {conditions_met}", **conditions_met)
        #     return False
        
        #bereme bud exit condition signalu, ktery activeTrade vygeneroval+ fallback na general
        state.ilog(lvl=0,e=f"EXIT CONDITIONS ENTRY {smer}", conditions=state.vars.conditions[KW.exit])

        mother_signal = state.vars.activeTrade.generated_by

        if mother_signal is not None:
            cond_dict = state.vars.conditions[KW.exit][state.vars.activeTrade.generated_by][smer]
            result, conditions_met = evaluate_directive_conditions(cond_dict, "OR")
            state.ilog(lvl=1,e=f"EXIT CONDITIONS of {mother_signal} =OR= {result}", **conditions_met, cond_dict=cond_dict)
            if result:
                return True
            
            #OR neprosly testujeme AND
            result, conditions_met = evaluate_directive_conditions(cond_dict, "AND")
            state.ilog(lvl=1,e=f"EXIT CONDITIONS of {mother_signal}  =AND= {result}", **conditions_met, cond_dict=cond_dict)
            if result:
                return True


        #pokud nemame mother signal nebo exit nevratil nic, fallback na common
        cond_dict = state.vars.conditions[KW.exit]["common"][smer]
        result, conditions_met = evaluate_directive_conditions(cond_dict, "OR")
        state.ilog(lvl=1,e=f"EXIT CONDITIONS of COMMON =OR= {result}", **conditions_met, cond_dict=cond_dict)
        if result:
            return True
        
        #OR neprosly testujeme AND
        result, conditions_met = evaluate_directive_conditions(cond_dict, "AND")
        state.ilog(lvl=1,e=f"EXIT CONDITIONS of COMMON =AND= {result}", **conditions_met, cond_dict=cond_dict)
        if result:
            return True

 
        #ZVAZIT JESTLI nesledujici puvodni pravidlo pro dontsellwhen pujdou realizovat inverzne jako exit when
        #PUVODNI NASTAVENI - IDENTIFIKOVAce rustoveho MOMENTA - pokud je momentum, tak prodávat později
        
        # #pokud je slope too high, pak prodavame jakmile slopeMA zacne klesat, napr. 4MA (TODO 3)

        # #TODO zkusit pro pevny profit, jednoduse pozdrzet prodej - dokud tick_price roste nebo se drzi tak neprodavat, pokud klesne prodat
        # #mozna mit dva mody - pri vetsi volatilite pouzivat momentum, pri mensi nebo kdyz potrebuju pryc, tak prodat hned

        #puvodni nastaveni
        #slopeMA_rising = 2
        #rsi_not_falling = 3

        # #toto docasne pryc dont_sell_when['slope_too_high'] = slope_too_high() and not isfalling(state.indicators.slopeMA,4)
        # dont_sell_when['AND']['slopeMA_rising'] = isrising(state.indicators.slopeMA,safe_get(options, 'slopeMA_rising', 2))
        # dont_sell_when['AND']['rsi_not_falling'] = not isfalling(state.indicators.RSI14,safe_get(options, 'rsi_not_falling',3))
        # #dont_sell_when['rsi_dont_buy'] = state.indicators.RSI14[-1] > safe_get(state.vars, "rsi_dont_buy_above",50)
 
        # result, conditions_met = eval_cond_dict(dont_sell_when)
        # if result:
        #     state.ilog(lvl=0,e=f"SELL_PROTECTION {conditions_met} enabled")
        # return result 

    def insert_SL_history():
    #insert stoploss history as key sl_history into runner archive extended data
        state.extData["sl_history"].append(SLHistory(id=state.vars.activeTrade.id, time=state.time, sl_val=state.vars.activeTrade.stoploss_value))

    def trail_SL_management():
    #pokud se cena posouva nasim smerem olespon o (0.05) nad (SL + 0.09val), posuneme SL o offset
    #+ varianta - skoncit breakeven

    #DIREKTIVY:
    #maximalni stoploss, fallout pro "exit_short_if" direktivy
    # SL_defval_short = 0.10
    # SL_defval_long = 0.10
    # SL_trailing_enabled_short = true
    # SL_trailing_enabled_long = true
    # #minimalni vzdalenost od aktualni SL, aby se SL posunula na 
    # SL_trailing_offset_short = 0.05
    # SL_trailing_offset_long = 0.05
    # #zda trailing zastavit na brakeeven
    # SL_trailing_stop_at_breakeven_short = true
    # SL_trailing_stop_at_breakeven_long = true
        if int(state.positions) != 0 and float(state.avgp)>0 and state.vars.pending is None:

            if int(state.positions) < 0:
                direction = TradeDirection.SHORT
                smer = "short"
            else:
                direction = TradeDirection.LONG
                smer = "long"
            
            # zatim nastaveni SL plati pro vsechny - do budoucna per signal - pridat sekci

            options = safe_get(state.vars, 'exit', None)
            if options is None:
                state.ilog(lvl=1,e="Trail SL. No options for exit conditions in stratvars.")
                return
            
            directive_name = 'SL_trailing_enabled_'+str(smer)
            sl_trailing_enabled = get_override_for_active_trade(directive_name=directive_name, default_value=safe_get(options, directive_name, False))
     

            #SL_trailing_protection_window_short
            directive_name = 'SL_trailing_protection_window_'+str(smer)
            SL_trailing_protection_window = get_override_for_active_trade(directive_name=directive_name, default_value=safe_get(options, directive_name, 0))
            index_to_compare = int(state.vars.last_in_index)+int(SL_trailing_protection_window) 
            if index_to_compare > int(data["index"]):
                state.ilog(lvl=1,e=f"SL trail PROTECTION WINDOW {SL_trailing_protection_window} - TOO SOON", currindex=data["index"], index_to_compare=index_to_compare, last_in_index=state.vars.last_in_index)
                return


            
            if sl_trailing_enabled is True:
                directive_name = 'SL_trailing_stop_at_breakeven_'+str(smer)
                stop_breakeven = get_override_for_active_trade(directive_name=directive_name, default_value=safe_get(options, directive_name, False))
                directive_name = 'SL_defval_'+str(smer)
                def_SL = get_override_for_active_trade(directive_name=directive_name, default_value=safe_get(options, directive_name, 0.01))
                directive_name = "SL_trailing_offset_"+str(smer)
                offset = get_override_for_active_trade(directive_name=directive_name, default_value=safe_get(options, directive_name, 0.01))

                #pokud je pozadovan trail jen do breakeven a uz prekroceno
                if (direction == TradeDirection.LONG and stop_breakeven and state.vars.activeTrade.stoploss_value >= float(state.avgp)) or (direction == TradeDirection.SHORT and stop_breakeven and state.vars.activeTrade.stoploss_value <= float(state.avgp)):
                    state.ilog(lvl=1,e=f"SL trail STOP at breakeven {str(smer)} SL:{state.vars.activeTrade.stoploss_value} UNCHANGED", stop_breakeven=stop_breakeven)
                    return
                
                #IDEA: Nyni posouvame SL o offset, mozna ji posunout jen o direktivu step ?

                offset_normalized = normalize_tick(offset) #to ticks and from options
                def_SL_normalized = normalize_tick(def_SL)
                if direction == TradeDirection.LONG:
                    move_SL_threshold = state.vars.activeTrade.stoploss_value + offset_normalized + def_SL_normalized
                    state.ilog(lvl=1,e=f"SL TRAIL EVAL {smer} SL:{round(state.vars.activeTrade.stoploss_value,3)} TRAILGOAL:{move_SL_threshold}", def_SL=def_SL, offset=offset, offset_normalized=offset_normalized, def_SL_normalized=def_SL_normalized)
                    if (move_SL_threshold) < data['close']:
                        state.vars.activeTrade.stoploss_value += offset_normalized
                        insert_SL_history()
                        state.ilog(lvl=1,e=f"SL TRAIL TH {smer} reached {move_SL_threshold} SL moved to {state.vars.activeTrade.stoploss_value}", offset_normalized=offset_normalized, def_SL_normalized=def_SL_normalized)
                elif direction == TradeDirection.SHORT:
                    move_SL_threshold = state.vars.activeTrade.stoploss_value - offset_normalized - def_SL_normalized
                    state.ilog(lvl=0,e=f"SL TRAIL EVAL {smer} SL:{round(state.vars.activeTrade.stoploss_value,3)} TRAILGOAL:{move_SL_threshold}", def_SL=def_SL, offset=offset, offset_normalized=offset_normalized, def_SL_normalized=def_SL_normalized)
                    if (move_SL_threshold) > data['close']:
                        state.vars.activeTrade.stoploss_value -= offset_normalized
                        insert_SL_history()
                        state.ilog(lvl=1,e=f"SL TRAIL GOAL {smer} reached {move_SL_threshold} SL moved to {state.vars.activeTrade.stoploss_value}", offset_normalized=offset_normalized, def_SL_normalized=def_SL_normalized)                            

    def close_position(direction: TradeDirection, reason: str, followup: Followup = None):
        followup_text = str(followup) if followup is not None else ""
        state.ilog(lvl=1,e=f"CLOSING TRADE {followup_text} {reason} {str(direction)}", curr_price=data["close"], trade=state.vars.activeTrade)
        if direction == TradeDirection.SHORT:
            res = state.buy(size=abs(int(state.positions)))
            if isinstance(res, int) and res < 0:
                raise Exception(f"error in required operation {reason} {res}")

        elif direction == TradeDirection.LONG:
            res = state.sell(size=state.positions)
            if isinstance(res, int) and res < 0:
                raise Exception(f"error in required operation STOPLOSS SELL {res}")
        
        else:
            raise Exception(f"unknow TradeDirection in close_position")
        
        #pri uzavreni tradu zapisujeme SL history - lepsi zorbazeni v grafu
        insert_SL_history()
        state.vars.pending = state.vars.activeTrade.id
        state.vars.activeTrade = None   
        state.vars.last_exit_index = data["index"]    
        if followup is not None:
            state.vars.requested_followup = followup

    def eval_close_position():
        curr_price = float(data['close'])
        state.ilog(lvl=0,e="Eval CLOSE", price=curr_price, pos=state.positions, avgp=state.avgp, pending=state.vars.pending, activeTrade=str(state.vars.activeTrade))

        if int(state.positions) != 0 and float(state.avgp)>0 and state.vars.pending is None:
            
            #pevny target - presunout toto do INIT a pak jen pristupovat
            goal_price = get_profit_target_price()
            max_price = get_max_profit_price()
            state.ilog(lvl=1,e=f"Goal price {goal_price} max price {max_price}")
            
            #close position handling
            #TBD pridat OPTIMALIZACI POZICE - EXIT 1/2

            #mame short pozice - (IDEA: rozlisovat na zaklade aktivniho tradu - umozni mi spoustet i pri soucasne long pozicemi)
            if int(state.positions) < 0:
                #EOD EXIT - TBD
                #FORCED EXIT PRI KONCI DNE

                #SL - execution
                if curr_price > state.vars.activeTrade.stoploss_value:

                    directive_name = 'reverse_for_SL_exit_short'
                    reverse_for_SL_exit = get_override_for_active_trade(directive_name=directive_name, default_value=safe_get(state.vars, directive_name, False))
                    followup_action = Followup.REVERSE if reverse_for_SL_exit else None
                    close_position(direction=TradeDirection.SHORT, reason="SL REACHED", followup=followup_action)
                    return
                
                #REVERSE BASED ON REVERSE CONDITIONS
                if keyword_conditions_met(direction=TradeDirection.SHORT, keyword=KW.reverse):
                        close_position(direction=TradeDirection.SHORT, reason="REVERSE COND MET", followup=Followup.REVERSE)
                        return  

                #EXIT ADD CONDITIONS MET (exit and add)
                if keyword_conditions_met(direction=TradeDirection.SHORT, keyword=KW.exitadd):
                        close_position(direction=TradeDirection.SHORT, reason="EXITADD COND MET", followup=Followup.ADD)
                        return  

                #CLOSING BASED ON EXIT CONDITIONS
                if exit_conditions_met(TradeDirection.SHORT):
                        directive_name = 'reverse_for_cond_exit_short'
                        reverse_for_cond_exit_short = get_override_for_active_trade(directive_name=directive_name, default_value=safe_get(state.vars, directive_name, False))
                        directive_name = 'add_for_cond_exit_short'
                        add_for_cond_exit_short = get_override_for_active_trade(directive_name=directive_name, default_value=safe_get(state.vars, directive_name, False))
                        if reverse_for_cond_exit_short:
                            followup_action = Followup.REVERSE
                        elif add_for_cond_exit_short: 
                            followup_action = Followup.ADD
                        else:
                            followup_action = None
                        close_position(direction=TradeDirection.SHORT, reason="EXIT COND MET", followup=followup_action)
                        return                   

                #PROFIT
                if curr_price<=goal_price:
                    #TODO cekat az slope prestane intenzivn erust, necekat az na klesani
                    #TODO mozna cekat na nejaky signal RSI
                    #TODO pripadne pokud dosahne TGTBB prodat ihned
                    max_price_signal = curr_price<=max_price
                    #OPTIMALIZACE pri stoupajícím angle
                    if max_price_signal or dontexit_protection_met(direction=TradeDirection.SHORT) is False:
                        close_position(direction=TradeDirection.SHORT, reason=f"PROFIT or MAXPROFIT REACHED {max_price_signal=}")
                        return
            #mame long
            elif int(state.positions) > 0:
                #EOD EXIT - TBD

                #SL - execution
                if curr_price < state.vars.activeTrade.stoploss_value:
                    directive_name = 'reverse_for_SL_exit_long'
                    reverse_for_SL_exit = get_override_for_active_trade(directive_name=directive_name, default_value=safe_get(state.vars, directive_name, False))
                    followup_action = Followup.REVERSE if reverse_for_SL_exit else None
                    close_position(direction=TradeDirection.LONG, reason="SL REACHED", followup=followup_action)
                    return
                

                #REVERSE BASED ON REVERSE CONDITIONS
                if keyword_conditions_met(TradeDirection.LONG, KW.reverse):
                        close_position(direction=TradeDirection.LONG, reason="REVERSE COND MET", followup=Followup.REVERSE)
                        return  

                #EXIT ADD CONDITIONS MET (exit and add)
                if keyword_conditions_met(TradeDirection.LONG, KW.exitadd):
                        close_position(direction=TradeDirection.LONG, reason="EXITADD COND MET", followup=Followup.ADD)
                        return  

                #EXIT CONDITIONS
                if exit_conditions_met(TradeDirection.LONG):
                        directive_name = 'reverse_for_cond_exit_long'
                        reverse_for_cond_exit_long = get_override_for_active_trade(directive_name=directive_name, default_value=safe_get(state.vars, directive_name, False))
                        directive_name = 'add_for_cond_exit_long'
                        add_for_cond_exit_long = get_override_for_active_trade(directive_name=directive_name, default_value=safe_get(state.vars, directive_name, False))
                        if reverse_for_cond_exit_long:
                            followup_action = Followup.REVERSE
                        elif add_for_cond_exit_long: 
                            followup_action = Followup.ADD
                        else:
                            followup_action = None
                        close_position(direction=TradeDirection.LONG, reason="EXIT CONDS MET", followup=followup_action)
                        return    

                #PROFIT
                if curr_price>=goal_price:
                    #TODO cekat az slope prestane intenzivn erust, necekat az na klesani
                    #TODO mozna cekat na nejaky signal RSI
                    #TODO pripadne pokud dosahne TGTBB prodat ihned
                    max_price_signal = curr_price>=max_price
                    #OPTIMALIZACE pri stoupajícím angle
                    if max_price_signal or dontexit_protection_met(direction=TradeDirection.LONG) is False:
                        close_position(direction=TradeDirection.LONG, reason=f"PROFIT or MAXPROFIT REACHED {max_price_signal=}")
                        return

    def execute_prescribed_trades():
        ##evaluate prescribed trade, prvni eligible presuneme do activeTrade, zmenime stav and vytvorime objednavky
        
        if state.vars.activeTrade is not None or len(state.vars.prescribedTrades) == 0:
            return
        #evaluate long (price/market)
        state.ilog(lvl=1,e="evaluating prescr trades", trades=json.loads(json.dumps(state.vars.prescribedTrades, default=json_serial)))
        for trade in state.vars.prescribedTrades:
            if trade.status == TradeStatus.READY and trade.direction == TradeDirection.LONG and (trade.entry_price is None or trade.entry_price >= data['close']):
                trade.status = TradeStatus.ACTIVATED
                trade.last_update = datetime.fromtimestamp(state.time).astimezone(zoneNY)
                state.ilog(lvl=1,e=f"evaluated LONG", trade=json.loads(json.dumps(trade, default=json_serial)), prescrTrades=json.loads(json.dumps(state.vars.prescribedTrades, default=json_serial)))
                state.vars.activeTrade = trade
                state.vars.last_buy_index = data["index"]
                state.vars.last_in_index = data["index"]
                break
        #evaluate shorts
        if not state.vars.activeTrade:
            for trade in state.vars.prescribedTrades:
                if trade.status == TradeStatus.READY and trade.direction == TradeDirection.SHORT and (trade.entry_price is None or trade.entry_price <= data['close']):
                    state.ilog(lvl=1,e=f"evaluaed SHORT", trade=json.loads(json.dumps(trade, default=json_serial)), prescTrades=json.loads(json.dumps(state.vars.prescribedTrades, default=json_serial)))
                    trade.status = TradeStatus.ACTIVATED
                    trade.last_update = datetime.fromtimestamp(state.time).astimezone(zoneNY)
                    state.vars.activeTrade = trade
                    state.vars.last_buy_index = data["index"]
                    state.vars.last_in_index = data["index"]
                    break

        #odeslani ORDER + NASTAVENI STOPLOSS (zatim hardcoded)
        if state.vars.activeTrade:
            if state.vars.activeTrade.direction == TradeDirection.LONG:
                state.ilog(lvl=1,e="odesilame LONG ORDER", trade=json.loads(json.dumps(state.vars.activeTrade, default=json_serial)))
                if state.vars.activeTrade.size is not None:
                    size = state.vars.activeTrade.size
                else:
                    size = state.vars.chunk
                res = state.buy(size=size)
                if isinstance(res, int) and res < 0:
                    raise Exception(f"error in required operation LONG {res}")
                #pokud neni nastaveno SL v prescribe, tak nastavuji default dle stratvars
                if state.vars.activeTrade.stoploss_value is None:
                    sl_defvalue = get_default_sl_value(direction=state.vars.activeTrade.direction)
                    #normalizuji dle aktualni ceny 
                    sl_defvalue_normalized = normalize_tick(sl_defvalue)
                    state.vars.activeTrade.stoploss_value = float(data['close']) - sl_defvalue_normalized
                    insert_SL_history()
                    state.ilog(lvl=1,e=f"Nastaveno SL na {sl_defvalue}, priced normalized: {sl_defvalue_normalized} price: {state.vars.activeTrade.stoploss_value }")
                state.vars.pending = state.vars.activeTrade.id
            elif state.vars.activeTrade.direction == TradeDirection.SHORT:
                state.ilog(lvl=1,e="odesilame SHORT ORDER",trade=json.loads(json.dumps(state.vars.activeTrade, default=json_serial)))
                if state.vars.activeTrade.size is not None:
                    size = state.vars.activeTrade.size
                else:
                    size = state.vars.chunk
                res = state.sell(size=size)
                if isinstance(res, int) and res < 0:
                    raise Exception(f"error in required operation SHORT {res}")
                #pokud neni nastaveno SL v prescribe, tak nastavuji default dle stratvars
                if state.vars.activeTrade.stoploss_value is None:
                    sl_defvalue = get_default_sl_value(direction=state.vars.activeTrade.direction)
                    #normalizuji dle aktualni ceny 
                    sl_defvalue_normalized = normalize_tick(sl_defvalue)
                    state.vars.activeTrade.stoploss_value = float(data['close']) + sl_defvalue_normalized
                    insert_SL_history()
                    state.ilog(lvl=1,e=f"Nastaveno SL na {sl_defvalue}, priced normalized: {sl_defvalue_normalized} price: {state.vars.activeTrade.stoploss_value }")
                state.vars.pending = state.vars.activeTrade.id
            else:
                state.ilog(lvl=1,e="unknow direction")
                state.vars.activeTrade = None

    def execute_signal_generator_plugin(name):
        if name == "asr":
            execute_asr()

    #vstupni signal pro asr
    def execute_asr():
        pass
    
    #preconditions and conditions of LONG/SHORT SIGNAL
    def go_conditions_met(signalname: str, direction: TradeDirection):
        if direction == TradeDirection.LONG:
            smer = "long"
        else:
            smer = "short"
        #preconditiony dle smer

        #SPECIFICKE DONT BUYS - direktivy zacinajici dont_buy
        #dont_buy_below = value nebo nazev indikatoru
        #dont_buy_above = value nebo hazev indikatoru

        #TESTUJEME SPECIFICKY DONT_GO - 
        #u techto ma smysl pouze OR 
        cond_dict = state.vars.conditions[KW.dont_go][signalname][smer]
        result, conditions_met = evaluate_directive_conditions(cond_dict, "OR")
        state.ilog(lvl=1,e=f"SPECIFIC PRECOND {smer} {result}", **conditions_met, cond_dict=cond_dict)
        if result:
            return False
        
        # #OR neprosly testujeme AND
        # result, conditions_met = evaluate_directive_conditions(cond_dict, "AND")
        # state.ilog(lvl=0,e=f"EXIT CONDITIONS of activeTrade {smer} =AND= {result}", **conditions_met, cond_dict=cond_dict)
        # if result:
        #     return True

        #tyto timto nahrazeny - dat do konfigurace (dont_short_when, dont_long_when)
        #dont_buy_when['rsi_too_high'] = state.indicators.RSI14[-1] > safe_get(state.vars, "rsi_dont_buy_above",50)
        #dont_buy_when['slope_too_low'] = slope_too_low()
        #dont_buy_when['slope_too_high'] = slope_too_high()
        #dont_buy_when['rsi_is_zero'] = (state.indicators.RSI14[-1] == 0)
        #dont_buy_when['reverse_position_waiting_amount_not_0'] = (state.vars.reverse_position_waiting_amount != 0)

        #u indikatoru muzoun byt tyto directivy pro generovani signaliu long/short
        # long_if_crossed_down - kdyz prekrocil dolu, VALUE: hodnota nebo nazev indikatoru
        # long_if_crossed_up - kdyz prekrocil nahoru, VALUE: hodnota nebo nazev indikatoru
        # long_if_crossed - kdyz krosne obema smery, VALUE: hodnota nebo nazev indikatoru
        # long_if_falling - kdyz je klesajici po N, VALUE: hodnota
        # long_if_rising - kdyz je rostouci po N, VALUE: hodnota
        # long_if_below - kdyz je pod prahem, VALUE: hodnota nebo nazev indikatoru
        # long_if_above - kdyz je nad prahem, VALUE: hodnota nebo nazev indikatoru
        # long_if_pivot_a - kdyz je pivot A. VALUE: delka nohou
        # long_if_pivot_v - kdyz je pivot V. VALUE: delka nohou
        
        # direktivy se mohou nachazet v podsekci AND nebo OR - daneho indikatoru (nebo na volno, pak = OR)
        # OR - staci kdyz plati jedna takova podminka a buysignal je aktivni
        # AND - musi platit vsechny podminky ze vsech indikatoru, aby byl buysignal aktivni

        #populate work dict - muze byt i jen jednou v INIT nebo 1x za cas
        #dict oindexovane podminkou (OR/AND) obsahuje vsechny buy_if direktivy v tuplu (nazevind,direktiva,hodnota
        # {'AND': [('nazev indikatoru', 'nazev direktivy', 'hodnotadirektivy')], 'OR': []}
        #work_dict_signal_if = get_work_dict_with_directive(starts_with=signalname+"_"+smer+"_if")
        
        #TESTUJEME GO SIGNAL
        cond_dict = state.vars.conditions[KW.go][signalname][smer]
        result, conditions_met = evaluate_directive_conditions(cond_dict, "OR")
        state.ilog(lvl=1,e=f"EVAL GO SIGNAL {smer} =OR= {result}", **conditions_met, cond_dict=cond_dict)
        if result:
            return True
        
        #OR neprosly testujeme AND
        result, conditions_met = evaluate_directive_conditions(cond_dict, "AND")
        state.ilog(lvl=1,e=f"EVAL GO SIGNAL {smer} =AND= {result}", **conditions_met, cond_dict=cond_dict)
        if result:
            return True
        
        return False

    #obecne precondition preds vstupem - platne jak pro condition based tak pro plugin
    def common_go_preconditions_check(signalname: str, options: dict):
        #ZAKLADNI KONTROLY ATRIBUTU s fallbackem na obecné
        #check working windows (open - close, in minutes from the start of marker)

        window_open = safe_get(options, "window_open",safe_get(state.vars, "window_open",0))
        window_close = safe_get(options, "window_close",safe_get(state.vars, "window_close",390))

        if is_window_open(datetime.fromtimestamp(data['updated']).astimezone(zoneNY), window_open, window_close) is False:
            state.ilog(lvl=1,e=f"SIGNAL {signalname} - WINDOW CLOSED", msg=f"{window_open=} {window_close=} ")
            return False           

        next_signal_offset = safe_get(options, "next_signal_offset_from_last_exit",safe_get(state.vars, "next_signal_offset_from_last_exit",0))

        if state.vars.last_exit_index is not None:
            index_to_compare = int(state.vars.last_exit_index)+int(next_signal_offset) 
            if index_to_compare > int(data["index"]):
                state.ilog(lvl=1,e=f"NEXT SIGNAL OFFSET from EXIT {next_signal_offset} waiting - TOO SOON", currindex=data["index"], index_to_compare=index_to_compare, last_exit_index=state.vars.last_exit_index)
                return False

        # if is_open_rush(datetime.fromtimestamp(data['updated']).astimezone(zoneNY), open_rush) or is_close_rush(datetime.fromtimestamp(data['updated']).astimezone(zoneNY), close_rush):
        #     state.ilog(lvl=0,e=f"SIGNAL {signalname} - WINDOW CLOSED", msg=f"{open_rush=} {close_rush=} ")
        #     return False

        #natvrdo nebo na podminku
        activated = safe_get(options, "activated", True)

        #check activation
        if activated is False:
            state.ilog(lvl=1,e=f"{signalname} not ACTIVATED")
            cond_dict = state.vars.conditions[KW.activate][signalname]
            result, conditions_met = evaluate_directive_conditions(cond_dict, "OR")
            state.ilog(lvl=1,e=f"EVAL ACTIVATION CONDITION =OR= {result}", **conditions_met, cond_dict=cond_dict)

            if result is False:            
                #OR neprosly testujeme AND
                result, conditions_met = evaluate_directive_conditions(cond_dict, "AND")
                state.ilog(lvl=1,e=f"EVAL ACTIVATION CONDITION  =AND= {result}", **conditions_met, cond_dict=cond_dict)

            if result is False:
                state.ilog(lvl=1,e=f"not ACTIVATED")
                return False
            else:
                state.ilog(lvl=1,e=f"{signalname} JUST ACTIVATED")
                state.vars.signals[signalname]["activated"] = True
        
        # OBECNE PRECONDITIONS - typu dont_do_when
        precond_check = dict(AND=dict(), OR=dict())

        # #OBECNE DONT BUYS
        if safe_get(options, "signal_only_on_confirmed",safe_get(state.vars, "signal_only_on_confirmed",True)):
            precond_check['bar_not_confirmed'] = (data['confirmed'] == 0)
        # #od posledniho vylozeni musi ubehnout N baru
        # dont_buy_when['last_buy_offset_too_soon'] =  data['index'] < (int(state.vars.lastbuyindex) + int(safe_get(state.vars, "lastbuy_offset",3)))
        # dont_buy_when['blockbuy_active'] = (state.vars.blockbuy == 1)
        # dont_buy_when['jevylozeno_active'] = (state.vars.jevylozeno == 1)

        #obecne open_rush platne pro vsechny
        #precond_check['on_confirmed_only'] = safe_get(options, 'on_confirmed_only', False) - chybi realizace podminky, pripadne dodelat na short_on_confirmed

        # #testing preconditions
        result, cond_met = eval_cond_dict(precond_check)
        if result:
            state.ilog(lvl=1,e=f"PRECOND GENERAL not met {cond_met}", message=cond_met, precond_check=precond_check)
            return False
        
        state.ilog(lvl=1,e=f"{signalname} ALL PRECOND MET")
        return True

    def execute_signal_generator(name):
        state.ilog(lvl=0,e=f"SIGNAL SEARCH for {name}", cond_go=state.vars.conditions[KW.go][name], cond_dontgo=state.vars.conditions[KW.dont_go][name], cond_activate=state.vars.conditions[KW.activate][name] )
        options = safe_get(state.vars.signals, name, None)

        if options is None:
            state.ilog(lvl=1,e="No options for {name} in stratvars")
            return
        
        if common_go_preconditions_check(signalname=name, options=options) is False:
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
                state.ilog(lvl=1,e="Custom plugin {signal_plugin} not found")
        else:
            short_enabled = safe_get(options, "short_enabled",safe_get(state.vars, "short_enabled",True))
            long_enabled = safe_get(options, "long_enabled",safe_get(state.vars, "long_enabled",True))
            #common signals based on 1) configured signals in stratvars
            #toto umoznuje jednoduchy prescribed trade bez ceny
            if short_enabled is False:
                state.ilog(lvl=1,e=f"{name} SHORT DISABLED")
            if long_enabled is False:
                state.ilog(lvl=1,e=f"{name} LONG DISABLED")
            if long_enabled and go_conditions_met(signalname=name, direction=TradeDirection.LONG):
                state.vars.prescribedTrades.append(Trade(
                                        id=uuid4(),
                                        last_update=datetime.fromtimestamp(state.time).astimezone(zoneNY),
                                        status=TradeStatus.READY,
                                        generated_by=name,
                                        direction=TradeDirection.LONG,
                                        entry_price=None,
                                        stoploss_value = None))
            elif short_enabled and go_conditions_met(signalname=name, direction=TradeDirection.SHORT):
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

    def signal_search():
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
            execute_signal_generator(signalname)

        # #vysledek je vložení Trade Prescription a to bud s cenou nebo immediate
        # pokud je s cenou ceka se na cenu, pokud immmediate tak se hned provede
        # to vse za predpokladu, ze neni aktivni trade

    def manage_active_trade():
        trade = state.vars.activeTrade
        if trade is None:
            return -1

         #SL - trailing
        trail_SL_management()

        eval_close_position()
        #SELL STOPLOSS
        #SELL PROFIT
        #OPTIMIZE ADD TO PROFIT

        #zatim dynamicky profit
    # endregion

    #MAIN LOOP
    lp = data['close']
    state.ilog(lvl=1,e="ENTRY", msg=f"LP:{lp} P:{state.positions}/{round(float(state.avgp),3)} SL:{state.vars.activeTrade.stoploss_value if state.vars.activeTrade is not None else None} profit:{round(float(state.profit),2)} Trades:{len(state.tradeList)} pend:{state.vars.pending}", activeTrade=json.loads(json.dumps(state.vars.activeTrade, default=json_serial)), prescribedTrades=json.loads(json.dumps(state.vars.prescribedTrades, default=json_serial)), pending=str(state.vars.pending))
    inds = get_last_ind_vals()
    state.ilog(lvl=1,e="Indikatory", **inds)

    #TODO dat do initu inciializaci work directory pro directivy 

    #pokud mame prazdne pozice a neceka se na nic
    if state.positions == 0 and state.vars.pending is None:

        execute_prescribed_trades()
        #pokud se neaktivoval nejaky trade, poustime signal search - ale jen jednou za bar?
        #if conf_bar == 1:
        if state.vars.pending is None:
            signal_search()
            #pro jistotu ihned zpracujeme
            execute_prescribed_trades()

    #mame aktivni trade a neceka se nani
    elif state.vars.activeTrade and state.vars.pending is None:
            manage_active_trade() #optimalize, close
               # - close means change status in prescribed Trends,update profit, delete from activeTrade


def init(state: StrategyState):
    #place to declare new vars
    print("INIT v main",state.name)

    def initialize_dynamic_indicators():
        #pro vsechny indikatory, ktere maji ve svych stratvars TYPE inicializujeme
        dict_copy = state.vars.indicators.copy()
        for indname, indsettings in dict_copy.items():
            for option,value in list(indsettings.items()):
                #inicializujeme nejenom typizovane
                #if option == "type":
                state.indicators[indname] = []
                #pokud ma MA_length incializujeme i MA variantu
                if safe_get(indsettings, 'MA_length', False):
                    state.indicators[indname+"MA"] = []
                #specifika pro slope
                if option == "type":
                    if value == "slope":
                        #inicializujeme statinds (pro uhel na FE)
                        state.statinds[indname] = dict(minimum_slope=safe_get(indsettings, 'minimum_slope', -1), maximum_slope=safe_get(indsettings, 'maximum_slope', 1))
                    if value == "custom":
                        #pro typ custom inicializujeme promenne
                        state.vars.indicators[indname]["last_run_time"] = None
                        state.vars.indicators[indname]["last_run_index"] = None


    #TODO hlavne tedy do INITu dat exit dict, ty jsou evaluovane kazdy tick
    def intialize_directive_conditions():
        #inciializace pro akce: short, long, dont_short, dont_long, activate

        state.vars.conditions = {}

        # state.vars.work_dict_dont_do = {}
        # state.vars.work_dict_signal_if = {}

        # state.vars.work_dict_dont_do_new = {}
        # state.vars.work_dict_signal_if_new = {}
        # state.vars.work_dict_signal_activate_if = {}


        #KEYWORDS_if_CONDITION = value
        # např. go_short_if_below = 10

        

        #possible KEYWORDS in directive: (AND/OR) support
        #  go_DIRECTION(go_long_if, go_short_if)
        #  dont_go_DIRECTION (dont_long_if, dont_short_if)
        #  exit_DIRECTION (exit_long_if, exit_short_if)
        #  activate (activate_if)

        #possible CONDITIONs:
        # below, above, falling, rising, crossed_up, crossed_down

        #Tyto mohou byt bud v sekci conditions a nebo v samostatne sekci common

        #pro kazdou sekci "conditions" v signals
        #si vytvorime podminkove dictionary pro kazdou akci
        #projdeme vsechny singaly


        #nejprve genereujeme ze SIGNALu
        for signalname, signalsettings in state.vars.signals.items():

            if "conditions" in signalsettings:
                section = signalsettings["conditions"]

                #directivy non direction related
                state.vars.conditions.setdefault(KW.activate,{})[signalname] = get_conditions_from_configuration(action=KW.activate+"_if", section=section)



                #direktivy direction related
                for smer in TradeDirection:
                    #IDEA navrhy condition dictionary - ty v signal sekci
                    # state.vars.conditions["nazev_evaluacni_sekce"]["nazevsignalu_smer"] = #sada podminek
                    #signal related
                    # state.vars.conditions["activate"]["trendfollow"] = #sada podminek
                    # state.vars.conditions["dont_go"]["trendfollow"]["long"] = #sada podminek
                    # state.vars.conditions["go"]["trendfollow"]["short"] = #sada podminek
                    # state.vars.conditions["exit"]["trendfollow"]["long"] = #sada podminek
                    #common
                    # state.vars.conditions["exit"]["common"]["long"] = #sada podminek
                    # state.vars.conditions["exit"]["common"]["long"] = #sada podminek

                    state.vars.conditions.setdefault(KW.dont_go,{}).setdefault(signalname,{})[smer] = get_conditions_from_configuration(action=KW.dont_go+"_" + smer +"_if", section=section)
                    state.vars.conditions.setdefault(KW.dont_exit,{}).setdefault(signalname,{})[smer] = get_conditions_from_configuration(action=KW.dont_exit+"_" + smer +"_if", section=section)
                    state.vars.conditions.setdefault(KW.go,{}).setdefault(signalname,{})[smer] = get_conditions_from_configuration(action=KW.go+"_" + smer +"_if", section=section)
                    state.vars.conditions.setdefault(KW.exit,{}).setdefault(signalname,{})[smer] = get_conditions_from_configuration(action=KW.exit+"_" + smer +"_if", section=section)
                    state.vars.conditions.setdefault(KW.reverse,{}).setdefault(signalname,{})[smer] = get_conditions_from_configuration(action=KW.reverse+"_" + smer +"_if", section=section)
                    state.vars.conditions.setdefault(KW.exitadd,{}).setdefault(signalname,{})[smer] = get_conditions_from_configuration(action=KW.exitadd+"_" + smer +"_if", section=section)
                    # state.vars.work_dict_dont_do[signalname+"_"+ smer] = get_work_dict_with_directive(starts_with=signalname+"_dont_"+ smer +"_if")
                    # state.vars.work_dict_signal_if[signalname+"_"+ smer] = get_work_dict_with_directive(starts_with=signalname+"_"+smer+"_if")

        #POTOM generujeme z obecnych sekci, napr. EXIT.EXIT_CONDITIONS, kde je fallback pro signal exity
        section = state.vars.exit["conditions"]
        for smer in TradeDirection:
            state.vars.conditions.setdefault(KW.exit,{}).setdefault("common",{})[smer] = get_conditions_from_configuration(action=KW.exit+"_" + smer +"_if", section=section)
            state.vars.conditions.setdefault(KW.dont_exit,{}).setdefault("common",{})[smer] = get_conditions_from_configuration(action=KW.dont_exit+"_" + smer +"_if", section=section)
            state.vars.conditions.setdefault(KW.reverse,{}).setdefault("common",{})[smer] = get_conditions_from_configuration(action=KW.reverse+"_" + smer +"_if", section=section)
            state.vars.conditions.setdefault(KW.exitadd,{}).setdefault("common",{})[smer] = get_conditions_from_configuration(action=KW.exitadd+"_" + smer +"_if", section=section)
    #init klice v extData pro ulozeni historie SL
    state.extData["sl_history"] = []

    #nove atributy na rizeni tradu
    #identifikuje provedenou změnu na Tradu (neděláme změny dokud nepřijde potvrzeni z notifikace)
    state.vars.pending = None
    #obsahuje aktivni Trade a jeho nastaveni
    state.vars.activeTrade = None #pending/Trade
    #obsahuje pripravene Trady ve frontě
    state.vars.prescribedTrades = []
    #flag pro reversal
    state.vars.requested_followup = None

    #TODO presunout inicializaci work_dict u podminek - sice hodnoty nepujdou zmenit, ale zlepsi se performance
    #pripadne udelat refresh kazdych x-iterací
    state.vars['sell_in_progress'] = False
    state.vars.mode = None
    state.vars.last_tick_price = 0
    state.vars.last_50_deltas = []
    state.vars.last_tick_volume = 0
    state.vars.next_new = 0
    state.vars.last_buy_index = None
    state.vars.last_exit_index = None
    state.vars.last_in_index = None
    state.vars.last_update_time = 0
    state.vars.reverse_position_waiting_amount = 0
    #INIT promenne, ktere byly zbytecne ve stratvars
    state.vars.pendingbuys={}
    state.vars.limitka = None
    state.vars.limitka_price=0
    state.vars.jevylozeno=0
    state.vars.blockbuy = 0

    #state.cbar_indicators['ivwap'] = []
    state.cbar_indicators['tick_price'] = []
    state.cbar_indicators['tick_volume'] = []
    state.cbar_indicators['CRSI'] = []
    #state.secondary_indicators['SRSI'] = []
    #state.indicators['ema'] = []
    #state.indicators['RSI14'] = []

    initialize_dynamic_indicators()
    intialize_directive_conditions()

    #TODO - predelat tuto cas, aby dynamicky inicializovala indikatory na zaklade stratvars a type
    # vsechno nize vytvorit volana funkce
    # to jestli inicializovat i MA variantu pozna podle pritomnosti MA_length 
    # # 
    # state.indicators['slope'] = []
    # state.indicators['slopeNEW'] = []
    # state.indicators['slopeNEWMA'] = []
    # state.indicators['slope10'] = []
    # state.indicators['slope10puv'] = []
    # state.indicators['slope30'] = []
    # state.indicators['slopeMA'] = []
    # state.indicators['slow_slope'] = []
    # state.indicators['slow_slopeMA'] = []
    # #static indicators - those not series based
    # state.statinds['slope'] = dict(minimum_slope=state.vars['indicators']['slope']["minimum_slope"], maximum_slope=safe_get(state.vars['indicators']['slope'], "maximum_slope",0.20))
    # #state.statinds['angle_slow'] = dict(minimum_slope=safe_get(state.vars.indicators.slow_slope, "minimum_slope",-2), maximum_slope=safe_get(state.vars.indicators.slow_slope, "maximum_slope",2))
    # state.statinds['slow_slope'] = dict(minimum_slope=state.vars['indicators']['slow_slope']["minimum_slope"], maximum_slope=state.vars['indicators']['slow_slope']["maximum_slope"])
 


def main():
    name = os.path.basename(__file__)
    se = Event()
    pe = Event()
    s = StrategyOrderLimitVykladaciNormalizedMYSELL(name = name, symbol = "BAC", account=Account.ACCOUNT1, next=next, init=init, stratvars=None, open_rush=10, close_rush=0, pe=pe, se=se, ilog_save=True)
    s.set_mode(mode = Mode.BT,
               debug = False,
               start = datetime(2023, 4, 14, 10, 42, 0, 0, tzinfo=zoneNY),
               end =   datetime(2023, 4, 14, 14, 35, 0, 0, tzinfo=zoneNY),
               cash=100000)

    #na sekundovem baru nezaokrouhlovat MAcko
    s.add_data(symbol="BAC",rectype=RecordType.BAR,timeframe=2,minsize=100,update_ltp=True,align=StartBarAlign.ROUND,mintick=0, exthours=False)
    #s.add_data(symbol="C",rectype=RecordType.BAR,timeframe=1,filters=None,update_ltp=True,align=StartBarAlign.ROUND,mintick=0)

    s.start()
    print("zastavujeme")

if __name__ == "__main__":
    main()




 