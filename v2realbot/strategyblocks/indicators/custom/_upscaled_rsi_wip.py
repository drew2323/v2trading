from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
from v2realbot.strategy.base import StrategyState
from v2realbot.indicators.indicators import ema, natr, roc
from v2realbot.strategyblocks.indicators.helpers import get_source_series
from rich import print as printanyway
from traceback import format_exc
from v2realbot.ml.ml import ModelML
import numpy as np
from collections import defaultdict

#WIP
#indicator to run on bar multiples
#např. umožní RSI na 5min
#params: resolution (bar multiples)
def upscaledrsi(state, params):
    funcName = "upscaledrsi"
    #new res in seconds
    new_resolution = safe_get(params, "resolution", None)
    old_resolution = state.bars["resolution"][-1]

    #pokud potrebuju vsechny bary, tak si je dotahnu
    new_bars = {}
    new_bars = create_new_bars(state.bars, new_resolution)
    #val = rsi(bars.)

    #pokud potrebuju jen close nebo open muzu pouzit toto
    # vezme to N-th element z pole

    #TODO resample any series
    def resample_close_prices(bars, new_resolution):
        # Check that the new resolution is a multiple of the old resolution.
        if new_resolution % bars['resolution'][-1] != 0:
            raise ValueError('New resolution must be a multiple of the old resolution.')

        # Calculate the step size for selecting every Nth element.
        step = new_resolution // bars['resolution'][-1]

        # Extract close prices at the new resolution.
        new_close_prices = bars['close'][::step]
        #optimizied - but works only for numpy arrays, prevedeni z listu na numpy is costly -  bars_array = np.array(bars)
        #new_close_prices = np.take(bars['close'], np.arange(0, len(bars['close']), step), axis=0)

        return new_close_prices
    

        ##TOTO PROJIT 
        #pokud je vstup jedna hodnota  - muzu brat close,open v danem rozliseni tzn. jen N-th hodnotu zde
        # Check that the new resolution is a multiple of the old resolution.
        if new_resolution % state.bars["resolution"][-1] != 0:
            raise ValueError('The new resolution must be a multiple of the old resolution.')

        #get the number of bars in the new resolution.
        n = new_resolution // old_resolution
        # Calculate the new resolution values.
        new_resolution_values = old_resolution_values.reshape((-1, new_resolution // len(old_resolution_values)))

        # Select the N-th values from the new resolution values.
        new_resolution_values[:, n]



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

