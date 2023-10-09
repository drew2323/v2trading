from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
from v2realbot.strategy.base import StrategyState
from v2realbot.indicators.indicators import ema, natr, roc
from v2realbot.indicators.oscillators import rsi
import numpy as np
from traceback import format_exc

def populate_dynamic_slope_indicator(data, state: StrategyState, name):
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

                    #lookbackprice_array = state.bars.vwap[-array_od:-array_do]
                    #lookbackprice = round(sum(lookbackprice_array)/lookback_offset,3)

                    #jako optimalizace pouzijeme NUMPY
                    lookbackprice = np.mean(state.bars.vwap[-array_od:-array_do])
                    # Round the lookback price to 3 decimal places
                    lookbackprice = round(lookbackprice, 3)
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
                        
                        lookbackprice = np.mean(state.bars.vwap[:sliced_to])
                        #lookbackprice= Average(state.bars.vwap[:sliced_to])
                        lookbacktime = state.bars.time[int(sliced_to/2)]
                    else:
                        lookbackprice = np.mean(state.bars.vwap)
                        #lookbackprice = Average(state.bars.vwap)
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
