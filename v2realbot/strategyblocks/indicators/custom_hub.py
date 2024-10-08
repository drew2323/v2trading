from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
from v2realbot.strategy.base import StrategyState
from datetime import datetime, timedelta
from rich import print as printanyway
from v2realbot.indicators.indicators import ema
from traceback import format_exc
import importlib
import v2realbot.strategyblocks.indicators.custom as ci
from v2realbot.strategyblocks.indicators.helpers import find_index_optimized
import numpy as np


def populate_dynamic_custom_indicator(data, state: StrategyState, name):
    ind_type = "custom"
    options = safe_get(state.vars.indicators, name, None)
    if options is None:
        state.ilog(lvl=1,e=f"No options for {name} in stratvars")
        return       
    
    if safe_get(options, "type", False) is False or safe_get(options, "type", False) != ind_type:
        state.ilog(lvl=1,e="Type error")
        return
    
    subtype = safe_get(options, 'subtype', False)
    if subtype is False:
        state.ilog(lvl=1,e=f"No subtype for {name} in stratvars")
        return
    
    #if MA is required
    MA_length = safe_get(options, "MA_length", None)

    output = safe_get(options, "output", "bar")
    match output:
        case "bar":
            indicators_dict = state.indicators
        case "tick":
            indicators_dict = state.cbar_indicators
        case _:
            state.ilog(lvl=1,e=f"Output must be bar or tick for {name} in stratvars")
            return     
       
    active = safe_get(options, 'active', True)
    if not active:
        return

    # např.  5 - znamená ulož hodnotu indikatoru 5 barů dozadu namísto posledni hodnoty - hodí se pro vytvareni targetu pro ML trening
    save_to_past = int(safe_get(options, "save_to_past", 0))
    save_to_past_unit = safe_get(options, "save_to_past_unit", "position")

    #pokud neni multioutput, davame vystup do stejnojmenne serie
    returns = safe_get(options, 'returns', [name])

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

    should_run, msg = is_time_to_run()

    if should_run:
        #TODO get custom params
        custom_params = safe_get(options, "cp", None)
        #vyplnime last_run_time a last_run_index do stratvars
        state.vars.indicators[name]["last_run_time"] = datetime.fromtimestamp(data["updated"]).astimezone(zoneNY)
        state.vars.indicators[name]["last_run_index"] = data["index"]


        #pomocna funkce (returns je pole toho , co indikator vraci a ret_val je dictionary, kde key je item z pole a val hodnota)
        def save_to_past_func(indicators_dict,name,save_to_past_unit, steps, ret_val):
            if save_to_past_unit == "position":
                for ind_name, ind_value in ret_val.items():
                    indicators_dict[ind_name][-1-steps]=ind_value
            #time
            else:
                ##find index X seconds ago
                lookback_idx = find_index_optimized(time_list=indicators_dict["time"], seconds=steps)
                for ind_name, ind_value in ret_val.items():
                    indicators_dict[ind_name][lookback_idx]=ind_value  

        # - volame custom funkci pro ziskani hodnoty indikatoru
        #        - tu ulozime jako novou hodnotu indikatoru a prepocteme MAcka pokud je pozadovane
        # - pokud cas neni, nechavame puvodni, vcetna pripadneho MAcka
        #pozor jako defaultní hodnotu dává engine 0 - je to ok?
        try:
    
            subtype = "ci."+subtype+"."+subtype
            custom_function = eval(subtype)
            res_code, ret_val = custom_function(state, custom_params, name, returns)
            if res_code == 0:
                #ret_val byl puvodne jedna hodnota
                #nyni podporujeme multi output ve format dict(indName:value, indName2:value2...)
               
                #podporujeme vystup (list, dict a single value) - vse se transformuje do dict formatu
                # pri listu zipneme s return) a vytvorime dict (v pripade mismatch sizes se matchnou jen kratsi)
                if isinstance(ret_val, list):
                    ret_val = dict(zip(returns, ret_val))
                #pokud je to neco jineho nez dict (float,int..) jde o puvodni single output udelame z toho dict s hlavnim jmenem as key
                elif not isinstance(ret_val, dict):
                    #checkneme jestli nejde o numpy typ (napr. posledni clen z numpy), prevedem na python basic typ 
                    if isinstance(ret_val, (np.ndarray, np.generic)):
                        ret_val = ret_val.item()
                    ret_val = {name: ret_val}
                #v ostatnich pripadech predpokladame jiz dict
                    
                save_to_past_func(indicators_dict,name,save_to_past_unit, save_to_past, ret_val)
                state.ilog(lvl=1,e=f"IND {name} {subtype} VAL FROM FUNCTION: {ret_val}", lastruntime=state.vars.indicators[name]["last_run_time"], lastrunindex=state.vars.indicators[name]["last_run_index"], save_to_past=save_to_past)
                #prepocitame MA if required
                #pokud je MA nastaveno, tak pocitame MAcka pro vsechny multiouputy, tzn. vytvorime novem multioutput dict (ma_val)
                if MA_length is not None:
                    ma_val = {}
                    for ind_name, ind_val in ret_val.items():
                        src = indicators_dict[ind_name][-MA_length:]
                        MA_res = ema(src, MA_length)
                        MA_value = round(MA_res[-1],7)
                        ma_val[ind_name+"MA"] = MA_value
                    
                    save_to_past_func(indicators_dict,name+"MA",save_to_past_unit, save_to_past, ma_val)
                    state.ilog(lvl=0,e=f"IND {name}MA {subtype} {ma_val}",save_to_past=save_to_past)
                
                return

            else:
                err = f"IND  ERROR {name} {subtype}Funkce {custom_function} vratila {res_code} {ret_val}."
                raise Exception(err)
            
        except Exception as e:
            use_last_values(indicators_dict, name, returns, MA_length)
            state.ilog(lvl=1,e=f"IND ERROR {name} {subtype} necháváme původní u vsech z returns", returns=str(returns), message=str(e)+format_exc())
    
    else:
        state.ilog(lvl=0,e=f"IND {name} {subtype} COND NOT READY: {msg}", returns=returns)
        #not time to run - copy last value
        use_last_values(indicators_dict, name, returns, MA_length)
        state.ilog(lvl=0,e=f"IND {name} {subtype} NOT TIME TO RUN - value(and MA) still original", returns=returns)            

#zde nechavame puvodni (pri multiinputu nastavime predchozi hodnoty u vsech vystupu v defaultnim returns)
def use_last_values(indicators_dict, name, returns, MA_length):
    def use_last_values_(indicators_dict, name, MA_length):
        if len(indicators_dict[name]) >= 2:
            indicators_dict[name][-1]=indicators_dict[name][-2]
        if MA_length is not None and len(indicators_dict[name+"MA"])>=2:
            indicators_dict[name+"MA"][-1]=indicators_dict[name+"MA"][-2]
    
    if returns is not None and len(returns)>0:
        for ind_name in returns:
            use_last_values_(indicators_dict, ind_name, MA_length)
    else:
       use_last_values_(indicators_dict, name, MA_length) 
