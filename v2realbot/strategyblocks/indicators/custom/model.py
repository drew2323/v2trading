from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
from v2realbot.strategy.base import StrategyState
from v2realbot.indicators.indicators import ema, natr, roc
from v2realbot.strategyblocks.indicators.helpers import get_source_series
from rich import print as printanyway
from traceback import format_exc
import numpy as np
from collections import defaultdict

"""
Předpokladm, že buď používáme 1) bar+standard indikator 2) cbars indicators - zatim nepodporovano spolecne (jine time rozliseni)
"""
def model(state, params, ind_name):
    funcName = "model"
    if params is None:
        return -2, "params required"
    name = safe_get(params, "name", None)
    version = safe_get(params, "version", None)

    #TBD co s temito, kdyz se budou brat z uloženého modelu?
    #mozna jen na TRAIN?
    # seq = safe_get(params, "seq", None)
    # use_bars = safe_get(params, "use_bars", True)
    # bar_features = safe_get(params, "bar_features", None)
    # ind_features = safe_get(params, "ind_features", None)
    # if name is None or ind_features is None:
    #     return -2, "name/ind_features required"
    
    if not name in state.vars.loaded_models:
        return -2, "model not loaded"

    try:
        mdl = state.vars.loaded_models[name]

        #Optimalizovano, aby se v kazde iteraci nemusel volat len
        if state.cache.get(name, {}).get("skip_init", False) is False:
            if mdl.use_cbars is False:
                if len(state.bars["close"]) < mdl.input_sequences:
                    return 0, 0
                else:
                    state.cache[name]["skip_init"] = True
                    state.cache[name]["indicators"] = state.indicators
                    state.cache[name]["bars"] = state.bars if mdl.use_bars else {}
                    #return -2, f"too soon - not enough data for seq {seq=}"
            else:
                if len(state.cbar_indicators["time"]) < mdl.input_sequences:
                    return 0, 0
                else:
                    state.cache[name]["skip_init"] = True
                    state.cache[name]["indicators"] = state.cbar_indicators   
                    state.cache[name]["bars"] = state.bars if mdl.use_bars else {}  
        
        value = mdl.predict(state.cache[name]["bars"], state.cache[name]["indicators"])
        return 0, value
    except Exception as e:
        printanyway(str(e)+format_exc())
        return -2, str(e)+format_exc()

#presunuto do classy modelu - DECOMISSIONOVAT
# def get_model_prediction(cfg: ModelML):
#     lastNbars = slice_dict_lists(state.bars, cfg.seq, True)
#     lastNindicators =  slice_dict_lists(state.indicators, cfg.seq, False)
#     combined_live_data = cfg.column_stack_source(lastNbars, lastNindicators)

#     combined_live_data = cfg.scalerX.transform(combined_live_data)
#     combined_live_data = np.array(combined_live_data)
#     #converts to 3D array 
#     # 1 number of samples in the array.
#     # 2 represents the sequence length.
#     # 3 represents the number of features in the data.
#     combined_live_data = combined_live_data.reshape((1, cfg.seq, combined_live_data.shape[1]))
#     #prediction = model.predict(combined_live_data, verbose=0)
#     prediction = cfg.model(combined_live_data, training=False)

#     # Convert the prediction back to the original scale
#     return float(cfg.scalerY.inverse_transform(prediction))
