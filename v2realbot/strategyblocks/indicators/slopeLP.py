from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
from v2realbot.strategy.base import StrategyState
from v2realbot.indicators.indicators import ema, natr, roc
from v2realbot.indicators.oscillators import rsi
from traceback import format_exc
#SLOPE LP
def populate_dynamic_slopeLP_indicator(data, state: StrategyState, name):
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

            #REFACTOR multiaccount
            #avgp bereme z primarni accountu (state.account)
            avgp = state.account_variables[state.account].avgp          

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
                    if avgp > 0 and state.bars.index[-1] < int(state.vars.last_entry_index)+back_to_standard_after:
                        lb_index = -1 - (state.bars.index[-1] - int(state.vars.last_entry_index))
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
