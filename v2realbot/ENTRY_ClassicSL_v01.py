import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v2realbot.strategy.base import StrategyState
from v2realbot.strategy.StrategyOrderLimitVykladaciNormalizedMYSELL import StrategyOrderLimitVykladaciNormalizedMYSELL
from v2realbot.enums.enums import RecordType, StartBarAlign, Mode, Account, OrderSide, OrderType
from v2realbot.indicators.indicators import ema
from v2realbot.indicators.oscillators import rsi
from v2realbot.common.PrescribedTradeModel import Trade, TradeDirection, TradeStatus, TradeStoplossType
from v2realbot.utils.utils import ltp, isrising, isfalling,trunc,AttributeDict, zoneNY, price2dec, print, safe_get, round2five, is_open_rush, is_close_rush, eval_cond_dict, Average, crossed_down, crossed_up, crossed, is_pivot, json_serial
from datetime import datetime
from uuid import uuid4
import json
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
            state.ilog(e="No options for crsi in stratvars")
            return

        try:
            crsi_length = int(safe_get(options, 'crsi_length', 14))
            source = state.cbar_indicators.tick_price #[-rsi_length:] #state.bars.vwap
            crsi_res = rsi(source, crsi_length)
            crsi_value = crsi_res[-1]
            if str(crsi_value) == "nan":
                crsi_value = 0
            state.cbar_indicators.CRSI[-1]=crsi_value
            #state.ilog(e=f"RSI {rsi_length=} {rsi_value=} {rsi_dont_buy=} {rsi_buy_signal=}", rsi_indicator=state.indicators.RSI14[-5:])
        except Exception as e:
            state.ilog(e=f"CRSI {crsi_length=} necháváme 0", message=str(e)+format_exc())
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
                state.ilog(e=f"Pro porovnani bereme posledni hodnotu {ret} z indikatoru {value}")
            except Exception as e   :
                ret = 0
                state.ilog(e=f"Neexistuje indikator s nazvem {value} vracime 0" + str(e) + format_exc())
            return ret

    #funkce vytvori podminky (bud pro AND/OR) z pracovniho dict
    def create_conditions_from_directives(work_dict, cond_type):
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

            #PRIPADNE DALSI SPECIFICKE ZDE
            # elif directive == "buy_if_necospecifckeho":
            #     pass

        return cond

    #tato funkce vytvori dictionary typu podminek (OR/AND) 
    # z indikatoru, ktere obsahuji direktivami daneho typu(buy_if, dont_buy_when)
    # v tuplu (nazevind,direktiva,hodnota)
    # do OR jsou dane i bez prefixu
    # {'AND': [('nazev indikatoru', 'nazev direktivy', 'hodnotadirektivy')], 'OR': []}
    def get_work_dict_with_directive(starts_with: str):
        reslist = dict(AND=[], OR=[])

        for indname, indsettings in state.vars.indicators.items():
            for option,value in indsettings.items():
                    if option.startswith(starts_with):
                        reslist["OR"].append((indname, option, value))
                    if option == "AND":
                        #vsechny buy direktivy, ktere jsou pod AND
                        for key, val in value.items():
                            if key.startswith(starts_with):
                                reslist["AND"].append((indname, key, val))
                    if option == "OR" :
                        #vsechny buy direktivy, ktere jsou pod OR
                        for key, val in value.items():
                            if key.startswith(starts_with):
                                reslist["OR"].append((indname, key, val))
        return reslist     

    def get_source_or_MA(indicator):
        #pokud ma, pouzije MAcko, pokud ne tak standardni indikator
        try:
            return state.indicators[indicator+"MA"]
        except KeyError:
            return state.indicators[indicator]
    # #vrati true pokud dany indikator krosnul obema smery
    # def buy_if_crossed(indicator, value):
    #     res = crossed(threshold=value, list=get_source_or_MA(indicator))
    #     state.ilog(e=f"buy_if_crossed {indicator} {value} {res}")
    #     return res

    #vrati true pokud dany indikator prekrocil threshold dolu
    def buy_if_crossed_down(indicator, value):
        res = crossed_down(threshold=value, list=get_source_or_MA(indicator))
        state.ilog(e=f"signal_if_crossed_down {indicator} {value} {res}")
        return res

    #vrati true pokud dany indikator prekrocil threshold nahoru
    def buy_if_crossed_up(indicator, value):
        res = crossed_up(threshold=value, list=get_source_or_MA(indicator))
        state.ilog(e=f"signal_if_crossed_up {indicator} {value} {res}")
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

        state.ilog(e=f"TICK PRICE {tick_price} VOLUME {tick_delta_volume} {conf_bar=}", prev_price=state.vars.last_tick_price, prev_volume=state.vars.last_tick_volume)

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
        else:
            return

    #EMA INDICATOR
    # type = EMA, source = [close, vwap, hlcc4], length = [14], on_confirmed_only = [true, false]
    def populate_dynamic_ema_indicator(name):
        ind_type = "EMA"
        options = safe_get(state.vars.indicators, name, None)
        if options is None:
            state.ilog(e=f"No options for {name} in stratvars")
            return       
        
        if safe_get(options, "type", False) is False or safe_get(options, "type", False) != ind_type:
            state.ilog(e="Type error")
            return
        
        #poustet kazdy tick nebo jenom na confirmed baru (on_confirmed_only = true)
        on_confirmed_only = safe_get(options, 'on_confirmed_only', False)
        req_source = safe_get(options, 'source', 'vwap')
        if req_source not in ["close", "vwap","hlcc4"]:
            state.ilog(e=f"Unknown source error {req_source} for {name}")
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
                state.ilog(e=f"IND {name} EMA {val} {ema_length=}")
                #else:
                #    state.ilog(e=f"IND {name} EMA necháváme 0", message="not enough source data", source=source, ema_length=ema_length)
            except Exception as e:
                state.ilog(e=f"IND ERROR {name} EMA necháváme 0", message=str(e)+format_exc())

    #RSI INDICATOR
    # type = RSI, source = [close, vwap, hlcc4], rsi_length = [14], MA_length = int (optional), on_confirmed_only = [true, false]
    # pokud existuje MA, vytvarime i stejnojnojmenny MAcko
    def populate_dynamic_RSI_indicator(name):
        ind_type = "RSI"
        options = safe_get(state.vars.indicators, name, None)
        if options is None:
            state.ilog(e=f"No options for {name} in stratvars")
            return       
        
        if safe_get(options, "type", False) is False or safe_get(options, "type", False) != ind_type:
            state.ilog(e="Type error")
            return
        
        #poustet kazdy tick nebo jenom na confirmed baru (on_confirmed_only = true)
        on_confirmed_only = safe_get(options, 'on_confirmed_only', False)
        req_source = safe_get(options, 'source', 'vwap')
        if req_source not in ["close", "vwap","hlcc4"]:
            state.ilog(e=f"Unknown source error {req_source} for {name}")
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
                    state.ilog(e=f"IND {name} RSI {rsi_value}")

                    if rsi_MA_length is not None:
                        src = state.indicators[name][-rsi_MA_length:]
                        rsi_MA_res = ema(src, rsi_MA_length)
                        rsi_MA_value = round(rsi_MA_res[-1],4)
                        state.indicators[name+"MA"][-1]=rsi_MA_value
                        state.ilog(e=f"IND {name} RSIMA {rsi_MA_value}")

                else:
                    state.ilog(e=f"IND {name} RSI necháváme 0", message="not enough source data", source=source, rsi_length=rsi_length)
            except Exception as e:
                state.ilog(e=f"IND ERROR {name} RSI necháváme 0", message=str(e)+format_exc())

    #SLOPE LP
    def populate_dynamic_slopeLP_indicator(name):
        ind_type = "slopeLP"
        options = safe_get(state.vars.indicators, name, None)
        if options is None:
            state.ilog(e=f"No options for {name} in stratvars")
            return
        
        if safe_get(options, "type", False) is False or safe_get(options, "type", False) != ind_type:
            state.ilog(e="Type error")
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
                        if state.avgp > 0 and state.bars.index[-1] < int(state.vars.lastbuyindex)+back_to_standard_after:
                            lb_index = -1 - (state.bars.index[-1] - int(state.vars.lastbuyindex))
                            lookbackprice = state.bars.vwap[lb_index]
                            state.ilog(e=f"IND {name} slope {leftpoint}- LEFT POINT OVERRIDE bereme ajko cenu lastbuy {lookbackprice=} {lookbacktime=} {lb_index=}")
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
                            state.ilog(e=f"IND {name} slope {leftpoint} - LEFT POINT STANDARD {lookbackprice=} {lookbacktime=}")
                    else:
                        #kdyz neni  dostatek hodnot, pouzivame jako levy bod open hodnotu close[0]
                        lookbackprice = state.bars.close[0]
                        lookbacktime = state.bars.time[0]
                        state.ilog(e=f"IND {name} slope - not enough data bereme left bod open", slope_lookback=slope_lookback)
                elif leftpoint == "baropen":
                    lookbackprice = state.bars.open[-1]
                    lookbacktime = state.bars.time[-1]
                    state.ilog(e=f"IND {name} slope {leftpoint}- bereme cenu bar OPENu ", lookbackprice=lookbackprice, lookbacktime=lookbacktime)
                else:
                    state.ilog(e=f"IND {name} UNKNOW LEFT POINT TYPE {leftpoint=}")

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

                state.ilog(e=f"{name=} {slope=} {slopeMA=}", msg=f"{lookbackprice=}", lookbackoffset=lookback_offset, minimum_slope=minimum_slope, last_slopes=state.indicators[name][-10:], last_slopesMA=last_slopesMA)
                #dale pracujeme s timto MAckovanym slope
                #slope = slopeMA         

            except Exception as e:
                print(f"Exception in {name} slope Indicator section", str(e))
                state.ilog(e=f"EXCEPTION in {name}", msg="Exception in slope Indicator section" + str(e) + format_exc())

    def populate_dynamic_slope_indicator(name):
        options = safe_get(state.vars.indicators, name, None)
        if options is None:
            state.ilog(e="No options for slow slope in stratvars")
            return
        
        if safe_get(options, "type", False) is False or safe_get(options, "type", False) != "slope":
            state.ilog(e="Type error")
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
                #slow_slope = 99
                slope_lookback = safe_get(options, 'slope_lookback', 100)
                minimum_slope =  safe_get(options, 'minimum_slope', 25)
                maximum_slope = safe_get(options, "maximum_slope",0.9)
                lookback_offset = safe_get(options, 'lookback_offset', 25)

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
                    #lookbackprice = state.bars.close[0]

                    #update -- lookback je pole z toho co mame
                    lookbackprice = Average(state.bars.vwap)
                    lookbacktime = state.bars.time[0]
                    state.ilog(e=f"IND {name} slope - not enough data bereme left bod open", slope_lookback=slope_lookback)

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

                state.ilog(e=f"{name=} {slope=} {slopeMA=}", msg=f"{lookbackprice=}", lookbackoffset=lookback_offset, minimum_slope=minimum_slope, last_slopes=state.indicators[name][-10:], last_slopesMA=last_slopesMA)
                #dale pracujeme s timto MAckovanym slope
                #slope = slopeMA         

            except Exception as e:
                print(f"Exception in {name} slope Indicator section", str(e))
                state.ilog(e=f"EXCEPTION in {name}", msg="Exception in slope Indicator section" + str(e) + format_exc())

    def process_delta():
        #PROCESs DELTAS - to function
        last_update_delta = round((float(data['updated']) - state.vars.last_update_time),6) if state.vars.last_update_time != 0 else 0
        state.vars.last_update_time = float(data['updated'])

        if len(state.vars.last_50_deltas) >=50:
            state.vars.last_50_deltas.pop(0)
        state.vars.last_50_deltas.append(last_update_delta)
        avg_delta = Average(state.vars.last_50_deltas)

        state.ilog(e=f"---{data['index']}-{conf_bar}--delta:{last_update_delta}---AVGdelta:{avg_delta}")

    conf_bar = data['confirmed']
    process_delta()
    #kroky pro CONFIRMED BAR only
    if conf_bar == 1:
        #logika pouze pro potvrzeny bar
        state.ilog(e="BAR potvrzeny")

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
    #toto upravit na take profit
    #pripadne smazat - zatim nahrazeno by exit_conditions_met()
    def sell_protection_enabled():
        options = safe_get(state.vars, 'sell_protection', None)
        if options is None:
            state.ilog(e="No options for sell protection in stratvars")
            return False
        
        disable_sell_proteciton_when = dict(AND=dict(), OR=dict())

        #preconditions
        disable_sell_proteciton_when['disabled_in_config'] = safe_get(options, 'enabled', False) is False
        #too good to be true (maximum profit)
        #disable_sell_proteciton_when['tgtbt_reached'] = safe_get(options, 'tgtbt', False) is False
        disable_sell_proteciton_when['disable_if_positions_above'] = int(safe_get(options, 'disable_if_positions_above', 0)) < state.positions

        #testing preconditions
        result, conditions_met = eval_cond_dict(disable_sell_proteciton_when)
        if result:
            state.ilog(e=f"SELL_PROTECTION DISABLED by {conditions_met}", **conditions_met)
            return False
        
        work_dict_dont_sell_if = get_work_dict_with_directive(starts_with="dont_sell_if")
        state.ilog(e=f"SELL PROTECTION work_dict", message=work_dict_dont_sell_if)

        or_cond = create_conditions_from_directives(work_dict_dont_sell_if, "OR")
        result, conditions_met = eval_cond_dict(or_cond)
        state.ilog(e=f"SELL PROTECTION =OR= {result}", **conditions_met)
        if result:
            return True
        
        #OR neprosly testujeme AND
        and_cond = create_conditions_from_directives(work_dict_dont_sell_if, "AND")
        result, conditions_met = eval_cond_dict(and_cond)
        state.ilog(e=f"SELL PROTECTION =AND= {result}", **conditions_met)
        return result    

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
        #     state.ilog(e=f"SELL_PROTECTION {conditions_met} enabled")
        # return result 

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

    def get_default_sl_value(direction: TradeDirection):
        if direction == TradeDirection.LONG:
            smer = "long"
        else:
            smer = "short"
        options = safe_get(state.vars, 'exit_conditions', None)
        if options is None:
            state.ilog(e="No options for exit conditions in stratvars. Fallback.")
            return 0.01
        val = safe_get(options, 'SL_defval_'+str(smer), 0.01)
        state.ilog(e=f"SL value for {str(smer)} is {val}", message=str(options))
        return val

    def get_profit_target_price():
        def_profit = safe_get(state.vars, "def_profit",state.vars.profit) 
        cena = float(state.avgp)
        return price2dec(cena+normalize_tick(float(state.vars.profit)),3) if int(state.positions) > 0 else price2dec(cena-normalize_tick(float(state.vars.profit)),3)
        
    def get_max_profit_price():
        max_profit = float(safe_get(state.vars, "max_profit",0.03))
        cena = float(state.avgp)
        return price2dec(cena+normalize_tick(max_profit),3) if int(state.positions) > 0 else price2dec(cena-normalize_tick(max_profit),3)    

    #TBD pripadne opet dat parsovani pole do INITu

    #TODO nejspis u exitu neporovnavat s MA i kdyz indikator ma, ale s online hodnotou ??
    def exit_conditions_met(direction: TradeDirection):
        if direction == TradeDirection.LONG:
            smer = "long"
        else:
            smer = "short"

        options = safe_get(state.vars, 'exit_conditions', None)
        if options is None:
            state.ilog(e="No options for exit conditions in stratvars")
            return False
        
        disable_exit_proteciton_when = dict(AND=dict(), OR=dict())

        #preconditions
        disable_exit_proteciton_when['disabled_in_config'] = safe_get(options, 'enabled', False) is False
        #too good to be true (maximum profit)
        #disable_sell_proteciton_when['tgtbt_reached'] = safe_get(options, 'tgtbt', False) is False
        disable_exit_proteciton_when['disable_if_positions_above'] = int(safe_get(options, 'disable_if_positions_above', 0)) < abs(int(state.positions))

        #testing preconditions
        result, conditions_met = eval_cond_dict(disable_exit_proteciton_when)
        if result:
            state.ilog(e=f"EXIT_CONDITION for{smer} DISABLED by {conditions_met}", **conditions_met)
            return False
        
        work_dict_exit_if = get_work_dict_with_directive(starts_with="exit_"+smer+"_if")
        state.ilog(e=f"EXIT CONDITION for {smer}  work_dict", message=work_dict_exit_if)

        or_cond = create_conditions_from_directives(work_dict_exit_if, "OR")
        result, conditions_met = eval_cond_dict(or_cond)
        state.ilog(e=f"EXIT CONDITIONS for {smer} =OR= {result}", **conditions_met)
        if result:
            return True
        
        #OR neprosly testujeme AND
        and_cond = create_conditions_from_directives(work_dict_exit_if, "AND")
        result, conditions_met = eval_cond_dict(and_cond)
        state.ilog(e=f"EXIT CONDITION =AND= {result}", **conditions_met)
        return result    

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
        #     state.ilog(e=f"SELL_PROTECTION {conditions_met} enabled")
        # return result 


    def trail_SL_if_required(direction: TradeDirection):
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
        if direction == TradeDirection.LONG:
            smer = "long"
        else:
            smer = "short"
        
        options = safe_get(state.vars, 'exit_conditions', None)
        if options is None:
            state.ilog(e="Trail SL. No options for exit conditions in stratvars.")
            return
        
        if safe_get(options, 'SL_trailing_enabled_'+str(smer), False) is True:
            stop_breakeven = safe_get(options, 'SL_trailing_stop_at_breakeven_'+str(smer), False)
            def_SL = safe_get(options, 'SL_defval_'+str(smer), 0.01)
            offset = safe_get(options, "SL_trailing_offset_"+str(smer), 0.01)

            #pokud je pozadovan trail jen do breakeven a uz prekroceno
            if (direction == TradeDirection.LONG and stop_breakeven and state.vars.activeTrade.stoploss_value >= float(state.avgp)) or (direction == TradeDirection.SHORT and stop_breakeven and state.vars.activeTrade.stoploss_value <= float(state.avgp)):
                state.ilog(e=f"SL trail stop at breakeven {str(smer)} SL:{state.vars.activeTrade.stoploss_value} UNCHANGED", stop_breakeven=stop_breakeven)
                return
            
            #IDEA: Nyni posouvame SL o offset, mozna ji posunout jen o direktivu step ?

            offset_normalized = normalize_tick(offset) #to ticks and from options
            def_SL_normalized = normalize_tick(def_SL)
            if direction == TradeDirection.LONG:
                move_SL_threshold = state.vars.activeTrade.stoploss_value + offset_normalized + def_SL_normalized
                state.ilog(e=f"SL trailing EVAL {smer} SL:{state.vars.activeTrade.stoploss_value} MOVETHRESHOLD:{move_SL_threshold}", def_SL=def_SL, offset=offset, offset_normalized=offset_normalized, def_SL_normalized=def_SL_normalized)
                if (move_SL_threshold) < data['close']:
                    state.vars.activeTrade.stoploss_value += offset_normalized
                    state.ilog(e=f"SL TRAIL TH {smer} reached {move_SL_threshold} SL moved to {state.vars.activeTrade.stoploss_value}", offset_normalized=offset_normalized, def_SL_normalized=def_SL_normalized)
            elif direction == TradeDirection.SHORT:
                move_SL_threshold = state.vars.activeTrade.stoploss_value - offset_normalized - def_SL_normalized
                state.ilog(e=f"SL trailing EVAL {smer} SL:{state.vars.activeTrade.stoploss_value} MOVETHRESHOLD:{move_SL_threshold}", def_SL=def_SL, offset=offset, offset_normalized=offset_normalized, def_SL_normalized=def_SL_normalized)
                if (move_SL_threshold) > data['close']:
                    state.vars.activeTrade.stoploss_value -= offset_normalized
                    state.ilog(e=f"SL TRAIL TH {smer} reached {move_SL_threshold} SL moved to {state.vars.activeTrade.stoploss_value}", offset_normalized=offset_normalized, def_SL_normalized=def_SL_normalized)                            


    def eval_close_position():
        curr_price = float(data['close'])
        state.ilog(e="Eval CLOSE", price=curr_price, pos=state.positions, avgp=state.avgp, pending=state.vars.pending, activeTrade=str(state.vars.activeTrade))
          
        if int(state.positions) != 0 and float(state.avgp)>0 and state.vars.pending is None:
            #pevny target - presunout toto do INIT a pak jen pristupovat
            goal_price = get_profit_target_price()
            max_price = get_max_profit_price()
            state.ilog(e=f"Goal price {goal_price} max price {max_price}")
            
            #close position handling

            #mame short pozice - (IDEA: rozlisovat na zaklade aktivniho tradu - umozni mi spoustet i long pozicemi)
            if int(state.positions) < 0:
                #EOD EXIT - TBD

                #SL TRAILING
                trail_SL_if_required(direction=TradeDirection.SHORT)

                #SL - execution
                if curr_price > state.vars.activeTrade.stoploss_value:
                    state.ilog(e=f"STOPLOSS reached on SHORT", curr_price=curr_price, trade=state.vars.activeTrade)
                    res = state.buy(size=abs(int(state.positions)))
                    if isinstance(res, int) and res < 0:
                        raise Exception(f"error in required operation STOPLOSS BUY {res}")
                    state.vars.pending = state.vars.activeTrade.id
                    state.vars.activeTrade = None
                    return
                
                #CLOSING BASED ON EXIT CONDITIONS
                if exit_conditions_met(TradeDirection.SHORT):
                        res = state.buy(size=abs(int(state.positions)))
                        if isinstance(res, int) and res < 0:
                            raise Exception(f"error in required operation EXIT COND BUY {res}")
                        state.vars.pending = state.vars.activeTrade.id
                        state.vars.activeTrade = None
                        state.ilog(e=f"EXIT COND MET. market BUY was sent {curr_price=}", positions=state.positions, avgp=state.avgp)
                        return                   

                #PROFIT
                if curr_price<=goal_price:
                    #TODO cekat az slope prestane intenzivn erust, necekat az na klesani
                    #TODO mozna cekat na nejaky signal RSI
                    #TODO pripadne pokud dosahne TGTBB prodat ihned
                    max_price_signal = curr_price<=max_price
                    #OPTIMALIZACE pri stoupajícím angle
                    if max_price_signal or sell_protection_enabled() is False:
                        res = state.buy(size=abs(int(state.positions)))
                        if isinstance(res, int) and res < 0:
                            raise Exception(f"error in required operation PROFIT BUY {res}")
                        state.vars.pending = state.vars.activeTrade.id
                        state.vars.activeTrade = None
                        state.ilog(e=f"PROFIT MET EXIT. market BUY was sent {curr_price=} {max_price_signal=}", positions=state.positions, avgp=state.avgp)
                        return
            #mame long
            elif int(state.positions) > 0:
                #EOD EXIT - TBD

                #SL - trailing
                trail_SL_if_required(direction=TradeDirection.LONG)

                #SL - execution
                if curr_price < state.vars.activeTrade.stoploss_value:
                    state.ilog(e=f"STOPLOSS reached on LONG", curr_price=curr_price, trade=state.vars.activeTrade)
                    res = state.sell(size=state.positions)
                    if isinstance(res, int) and res < 0:
                        raise Exception(f"error in required operation STOPLOSS SELL {res}")
                    state.vars.pending = state.vars.activeTrade.id
                    state.vars.activeTrade = None
                    return

                if exit_conditions_met(TradeDirection.LONG):
                        res = state.sell(size=abs(int(state.positions)))
                        if isinstance(res, int) and res < 0:
                            raise Exception(f"error in required operation EXIT COND SELL {res}")
                        state.vars.pending = state.vars.activeTrade.id
                        state.vars.activeTrade = None
                        state.ilog(e=f"EXIT COND MET. market SELL was sent {curr_price=}", positions=state.positions, avgp=state.avgp)
                        return    

                #PROFIT
                if curr_price>=goal_price:
                    #TODO cekat az slope prestane intenzivn erust, necekat az na klesani
                    #TODO mozna cekat na nejaky signal RSI
                    #TODO pripadne pokud dosahne TGTBB prodat ihned
                    max_price_signal = curr_price>=max_price
                    #OPTIMALIZACE pri stoupajícím angle
                    if max_price_signal or sell_protection_enabled() is False:
                        res = state.sell(size=state.positions)
                        if isinstance(res, int) and res < 0:
                            raise Exception(f"error in required operation PROFIT SELL {res}")
                        state.vars.pending = state.vars.activeTrade.id
                        state.vars.activeTrade = None
                        state.ilog(e=f"PROFIT MET EXIT. market SELL was sent {curr_price=} {max_price_signal=}", positions=state.positions, avgp=state.avgp, sellinprogress=state.vars.sell_in_progress)
                        return

    def execute_prescribed_trades():
        ##evaluate prescribed trade, prvni eligible presuneme do activeTrade, zmenime stav and vytvorime objednavky
        
        if state.vars.activeTrade is not None or len(state.vars.prescribedTrades) == 0:
            return
        #evaluate long (price/market)
        state.ilog(e="evaluating prescr trades", trades=json.loads(json.dumps(state.vars.prescribedTrades, default=json_serial)))
        for trade in state.vars.prescribedTrades:
            if trade.status == TradeStatus.READY and trade.direction == TradeDirection.LONG and (trade.entry_price is None or trade.entry_price >= data['close']):
                trade.status = TradeStatus.ACTIVATED
                trade.last_update = datetime.fromtimestamp(state.time).astimezone(zoneNY)
                state.ilog(e=f"evaluated SHORT {str(trade)}", prescrTrades=json.loads(json.dumps(state.vars.prescribedTrades, default=json_serial)))
                state.vars.activeTrade = trade
                break
        #evaluate shorts
        if not state.vars.activeTrade:
            for trade in state.vars.prescribedTrades:
                if trade.status == TradeStatus.READY and trade.direction == TradeDirection.SHORT and (trade.entry_price is None or trade.entry_price <= data['close']):
                    state.ilog(e=f"evaluaed SHORT {str(trade)}", prescTrades=json.loads(json.dumps(state.vars.prescribedTrades, default=json_serial)))
                    trade.status = TradeStatus.ACTIVATED
                    trade.last_update = datetime.fromtimestamp(state.time).astimezone(zoneNY)
                    state.vars.activeTrade = trade
                    break

        #odeslani ORDER + NASTAVENI STOPLOSS (zatim hardcoded)
        if state.vars.activeTrade:
            if state.vars.activeTrade.direction == TradeDirection.LONG:
                state.ilog(e="odesilame LONG ORDER", trade=json.loads(json.dumps(state.vars.activeTrade, default=json_serial)))
                res = state.buy(size=state.vars.chunk)
                if isinstance(res, int) and res < 0:
                    raise Exception(f"error in required operation LONG {res}")
                #pokud neni nastaveno SL v prescribe, tak nastavuji default dle stratvars
                if state.vars.activeTrade.stoploss_value is None:
                    sl_defvalue = get_default_sl_value(direction=state.vars.activeTrade.direction)
                    #normalizuji dle aktualni ceny 
                    sl_defvalue_normalized = normalize_tick(sl_defvalue)
                    state.vars.activeTrade.stoploss_value = float(data['close']) - sl_defvalue_normalized
                    state.ilog(e=f"Nastaveno SL na {sl_defvalue}, priced normalized: {sl_defvalue_normalized} price: {state.vars.activeTrade.stoploss_value }")
                state.vars.pending = state.vars.activeTrade.id
            elif state.vars.activeTrade.direction == TradeDirection.SHORT:
                state.ilog(e="odesilame SHORT ORDER",trade=json.loads(json.dumps(state.vars.activeTrade, default=json_serial)))
                res = state.sell(size=state.vars.chunk)
                if isinstance(res, int) and res < 0:
                    raise Exception(f"error in required operation SHORT {res}")
                #pokud neni nastaveno SL v prescribe, tak nastavuji default dle stratvars
                if state.vars.activeTrade.stoploss_value is None:
                    sl_defvalue = get_default_sl_value(direction=state.vars.activeTrade.direction)
                    #normalizuji dle aktualni ceny 
                    sl_defvalue_normalized = normalize_tick(sl_defvalue)
                    state.vars.activeTrade.stoploss_value = float(data['close']) + sl_defvalue_normalized
                    state.ilog(e=f"Nastaveno SL na {sl_defvalue}, priced normalized: {sl_defvalue_normalized} price: {state.vars.activeTrade.stoploss_value }")
                state.vars.pending = state.vars.activeTrade.id
            else:
                state.ilog(e="unknow direction")
                state.vars.activeTrade = None

    def execute_signal_generator_plugin(name):
        if name == "asr":
            execute_asr()

    #vstupni signal pro asr
    def execute_asr():
        pass
    
    #preconditions and conditions of BUY SIGNAL
    def conditions_met(signalname: str, direction: TradeDirection):
        if direction == TradeDirection.LONG:
            smer = "long"
        else:
            smer = "short"
        #preconditiony dle smeru
        #dont_long_when, dont_short_when
        #signal direktivy
        #nazevgeneratoru_long_if_above
        #nazevgeneratoru_short_if_above

        
        # #preconditiony zatim preskoceny
        dont_do_when = dict(AND=dict(), OR=dict())

        # #OBECNE DONT BUYS
        if safe_get(state.vars, "signal_only_on_confirmed",True):
            dont_do_when['bar_not_confirmed'] = (data['confirmed'] == 0)
        # #od posledniho vylozeni musi ubehnout N baru
        # dont_buy_when['last_buy_offset_too_soon'] =  data['index'] < (int(state.vars.lastbuyindex) + int(safe_get(state.vars, "lastbuy_offset",3)))
        # dont_buy_when['blockbuy_active'] = (state.vars.blockbuy == 1)
        # dont_buy_when['jevylozeno_active'] = (state.vars.jevylozeno == 1)
        dont_do_when['open_rush'] = is_open_rush(datetime.fromtimestamp(data['updated']).astimezone(zoneNY), safe_get(state.vars, "open_rush",0))
        dont_do_when['close_rush'] = is_close_rush(datetime.fromtimestamp(data['updated']).astimezone(zoneNY), safe_get(state.vars, "close_rush",0))
    
        # #testing preconditions
        result, cond_met = eval_cond_dict(dont_do_when)
        if result:
            state.ilog(e=f"{smer} PRECOND GENERAL not met {cond_met}", message=cond_met)
            return False

        #SPECIFICKE DONT BUYS - direktivy zacinajici dont_buy
        #dont_buy_below = value nebo nazev indikatoru
        #dont_buy_above = value nebo hazev indikatoru

        #do INITU
        #work_dict_dont_do = get_work_dict_with_directive(starts_with=signalname+"_dont_"+ smer +"_if")

        #z initu
        work_dict_dont_do = state.vars.work_dict_dont_do[signalname+"_"+ smer]
        
        state.ilog(e=f"{smer} PRECOND DONT{smer} work_dict for {signalname}", message=work_dict_dont_do)
        #u techto ma smysl pouze OR
        precond = create_conditions_from_directives(work_dict_dont_do, "OR")
        result, conditions_met = eval_cond_dict(precond)
        state.ilog(e=f"{smer} PRECOND DONT{smer} =OR= {result}", **conditions_met)
        if result:
            return False

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
        work_dict_signal_if = state.vars.work_dict_signal_if[signalname+"_"+ smer]

        state.ilog(e=f"{smer} SIGNAL work_dict {signalname}", message=work_dict_signal_if)

        buy_or_cond = create_conditions_from_directives(work_dict_signal_if, "OR")
        result, conditions_met = eval_cond_dict(buy_or_cond)
        state.ilog(e=f"{smer} SIGNAL =OR= {result}", **conditions_met)
        if result:
            return True
        
        #OR neprosly testujeme AND
        buy_and_cond = create_conditions_from_directives(work_dict_signal_if, "AND")
        result, conditions_met = eval_cond_dict(buy_and_cond)
        state.ilog(e=f"{smer} SIGNAL =AND= {result}", **conditions_met)
        return result     

    def execute_signal_generator(name):
        options = safe_get(state.vars.signals, name, None)

        if options is None:
            state.ilog(e="No options for {name} in stratvars")
            return
        
        validfrom = safe_get(options, "validfrom", 0)
        validto = safe_get(options, "validto", 0)
        recurring = safe_get(options, "reccurring", False)
        on_confirmed_only = safe_get(options, 'on_confirmed_only', False)
        plugin = safe_get(options, 'plugin', None)
        short_enabled = safe_get(state.vars, "short_enabled",True)
        long_enabled = safe_get(state.vars, "long_enabled",True)

        #pokud je plugin True, spusti se kod
        if plugin:
            execute_signal_generator_plugin(name)
        else:
            #common signals based on 1) configured signals in stratvars
            #toto umoznuje jednoduchy prescribed trade bez ceny
            if long_enabled and conditions_met(signalname=name, direction=TradeDirection.LONG):
                state.vars.prescribedTrades.append(Trade(
                                        id=uuid4(),
                                        last_update=datetime.fromtimestamp(state.time).astimezone(zoneNY),
                                        status=TradeStatus.READY,
                                        direction=TradeDirection.LONG,
                                        entry_price=None,
                                        stoploss_value = None))
            elif short_enabled and conditions_met(signalname=name, direction=TradeDirection.SHORT):
                state.vars.prescribedTrades.append(Trade(
                        id=uuid4(),
                        last_update=datetime.fromtimestamp(state.time).astimezone(zoneNY),
                        status=TradeStatus.READY,
                        direction=TradeDirection.SHORT,
                        entry_price=None,
                        stoploss_value = None))

    def signal_search():
        # SIGNAL sekce ve stratvars obsahuje signal generator (obsahujici obecne veci jako name,validfrom, validto, validfrom, recurring) + specificke
        #jako plugin

        #spoustime kazdy nakonfigurovany signal generator (signal sekce v startvars)

        #ZAMYSLET SE JAK PRACOVAT S MULTI SIGNAL SEKCEMI ve stratvars
        for signalname, signalsettings in state.vars.signals.items():
            state.ilog(e=f"reading {signalname}", message=str(signalsettings))
            execute_signal_generator(signalname)

        # #vysledek je vložení Trade Prescription a to bud s cenou nebo immediate
        # trade = Trade(validfrom=datetime.now(tz=zoneNY),
        #             status=TradeStatus.READY,
        #             direction=TradeDirection.LONG,
        #             entry_price=None,
        #             stoploss_value = None)
    
        # ##add prescribed trade to list
        # state.vars.prescribedTrades.append(trade)

    def manage_active_trade():
        trade = state.vars.activeTrade
        if trade is None:
            return -1
        
        eval_close_position()
        #SELL STOPLOSS
        #SELL PROFIT
        #OPTIMIZE ADD TO PROFIT

        #zatim dynamicky profit
    # endregion

    #MAIN LOOP
    lp = data['close']
    state.ilog(e="ENTRY", msg=f"LP:{lp} P:{state.positions}/{round(float(state.avgp),3)} SL:{state.vars.activeTrade.stoploss_value if state.vars.activeTrade is not None else None} profit:{round(float(state.profit),2)} Trades:{len(state.tradeList)}", activeTrade=json.loads(json.dumps(state.vars.activeTrade, default=json_serial)), prescribedTrades=json.loads(json.dumps(state.vars.prescribedTrades, default=json_serial)), pending=str(state.vars.pending), last_price=lp, data=data, stratvars=str(state.vars))
    inds = get_last_ind_vals()
    state.ilog(e="Indikatory", **inds)

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

    #pomocna funkce pro inicializaci
    def get_work_dict_with_directive(starts_with: str):
        reslist = dict(AND=[], OR=[])

        for indname, indsettings in state.vars.indicators.items():
            for option,value in indsettings.items():
                    if option.startswith(starts_with):
                        reslist["OR"].append((indname, option, value))
                    if option == "AND":
                        #vsechny buy direktivy, ktere jsou pod AND
                        for key, val in value.items():
                            if key.startswith(starts_with):
                                reslist["AND"].append((indname, key, val))
                    if option == "OR" :
                        #vsechny buy direktivy, ktere jsou pod OR
                        for key, val in value.items():
                            if key.startswith(starts_with):
                                reslist["OR"].append((indname, key, val))
        return reslist   

    def initialize_dynamic_indicators():
        #pro vsechny indikatory, ktere maji ve svych stratvars TYPE inicializujeme
        for indname, indsettings in state.vars.indicators.items():
            for option,value in indsettings.items():
                #inicializujeme nejenom typizovane
                #if option == "type":
                state.indicators[indname] = []
                #pokud ma MA_length incializujeme i MA variantu
                if safe_get(indsettings, 'MA_length', False):
                    state.indicators[indname+"MA"] = []
                #specifika pro slope
                if value == "slope":
                    #inicializujeme statinds (pro uhel na FE)
                    state.statinds[indname] = dict(minimum_slope=safe_get(indsettings, 'minimum_slope', -1), maximum_slope=safe_get(indsettings, 'maximum_slope', 1))

    def intialize_work_dict():
        state.vars.work_dict_dont_do = {}
        state.vars.work_dict_signal_if = {}
        for signalname, signalsettings in state.vars.signals.items():
            smer = TradeDirection.LONG
            state.vars.work_dict_dont_do[signalname+"_"+ smer] = get_work_dict_with_directive(starts_with=signalname+"_dont_"+ smer +"_if")
            state.vars.work_dict_signal_if[signalname+"_"+ smer] = get_work_dict_with_directive(starts_with=signalname+"_"+smer+"_if")
            smer = TradeDirection.SHORT
            state.vars.work_dict_dont_do[signalname+"_"+ smer] = get_work_dict_with_directive(starts_with=signalname+"_dont_"+ smer +"_if")
            state.vars.work_dict_signal_if[signalname+"_"+ smer] = get_work_dict_with_directive(starts_with=signalname+"_"+smer+"_if")

    #nove atributy na rizeni tradu

    #identifikuje provedenou změnu na Tradu (neděláme změny dokud nepřijde potvrzeni z notifikace)
    state.vars.pending = None
    #obsahuje aktivni Trade a jeho nastaveni
    state.vars.activeTrade = None #pending/Trade
    #obsahuje pripravene Trady ve frontě
    state.vars.prescribedTrades = []

    #TODO presunout inicializaci work_dict u podminek - sice hodnoty nepujdou zmenit, ale zlepsi se performance
    #pripadne udelat refresh kazdych x-iterací
    state.vars['sell_in_progress'] = False
    state.vars.mode = None
    state.vars.last_tick_price = 0
    state.vars.last_50_deltas = []
    state.vars.last_tick_volume = 0
    state.vars.next_new = 0
    state.vars.lastbuyindex = 0
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
    intialize_work_dict()

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




 