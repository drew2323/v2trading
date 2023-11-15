from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, print, safe_get, is_still, is_window_open, eval_cond_dict, crossed_down, crossed_up, crossed, is_pivot, json_serial, pct_diff, create_new_bars, slice_dict_lists
from v2realbot.strategy.base import StrategyState
from v2realbot.indicators.indicators import ema, natr, roc
from v2realbot.strategyblocks.indicators.helpers import get_source_series
from rich import print as printanyway
from traceback import format_exc
import numpy as np
from collections import defaultdict
from scipy.stats import linregress
from scipy.fft import fft
from v2realbot.strategyblocks.indicators.helpers import value_or_indicator

#vstupem je bud indicator nebo bar parametr
#na tomto vstupu dokaze provest zakladni statisticke funkce pro subpole X hodnot zpatky
#podporovane functions: min, max, mean
def basestats(state, params, name):
    funcName = "basestats"
    #name of indicator or 
    source = safe_get(params, "source", None)
    lookback = safe_get(params, "lookback", None)
    func = safe_get(params, "function", None)
    returns = safe_get(params, "returns", None)

    source_dict = defaultdict(list)
    source_dict[source] = get_source_series(state, source)

    self = state.indicators[name]
    if lookback is None:
        source_array = source_dict[source]

    else:
        lookback = int(value_or_indicator(state, lookback))

        try:
            source_array = source_dict[source][-lookback-1:]
            self = self[-lookback-1:]
        except IndexError:
            source_array = source_dict[source]

    if func == "min":
        val = np.amin(source_array)
    elif func == "max":
        val = np.amax(source_array)
    elif func == "mean":
        val = np.mean(source_array)
    elif func == "var":
        data = np.array(source_array)
        mean_value = np.mean(data)
        # Calculate the variance of the data
        val = np.mean((data - mean_value) ** 2)
    elif func == "angle":
        delka_pole = len(source_array)
        if delka_pole < 2:
            return 0,0

        x = np.arange(delka_pole)
        y = np.array(source_array)

        # Fit a linear polynomial to the data
        coeffs = np.polyfit(x, y, 1)

        # Calculate the angle in radians angle_rad
        val = np.arctan(coeffs[0]) * 1000

        # Convert the angle to degrees angle_deg
        #angle_deg = np.degrees(angle_rad)
        
        # Normalize the degrees between -1 and 1
        #val = 2 * (angle_deg / 180) - 1
    elif func =="stdev":
        val = np.std(source_array)
    #linregres slope
    elif func == "slope":
        if len(source_array) < 4:
            return -2, "less than 4 elmnts"
        try:
            np.seterr(all="raise")
            val, _, _, _, _ = linregress(np.arange(len(source_array)), source_array)
            val = val*1000
        except FloatingPointError:
            return -2, "FloatingPointError"
    #zatim takto, dokud nebudou podporovany indikatory s vice vystupnimi
    elif func == "intercept":
        if len(source_array) < 4:
            return -2, "less than 4 elmnts"
        try:
            np.seterr(all="raise")
            _, val, _, _, _ = linregress(np.arange(len(source_array)), source_array)
            val = round(val, 4)
        except FloatingPointError:
            return -2, "FloatingPointError"
    elif func == "fourier":
        time_series = np.array(source_array)
        n = len(time_series)

        # Compute the Fourier transform
        yf = fft(time_series)
        xf = np.linspace(0.0, 1.0/(2.0), n//2)

        dominant_frequencies = xf[np.argsort(np.abs(yf[:n//2]))[-3:]]
        state.ilog(lvl=1,e=f"IND {name}:{funcName} 3 dominant freq are {str(dominant_frequencies)}", **params)

        if returns is not None:
            #vracime druhou
            if returns == "second":
                if len(dominant_frequencies) > 1:
                    val = dominant_frequencies[-2]
                else:
                    val = 0
        else:
            #vracime most dominant
            val = float(np.max(dominant_frequencies))
            return 0, val
        
    elif func == "histogram":
        #takes only first N - items
        dt = np.array(source_array)
        #creates 4 buckets
        bins = 4
        mean_of_4th_bin = np.mean(dt[np.where(np.histogram(dt, bins)[1][3] <= dt)[0]])
        if not np.isfinite(mean_of_4th_bin):
            mean_of_4th_bin = 0
        return 0, float(mean_of_4th_bin)

    elif func == "maxima":
        if len(source_array) < 3:
            return 0, state.bars["high"]
        
        if len(self) == 0:
            self_max = 0
        else:
            #nejvyssi dosavadni maxima za lookback
            #self_max = float(np.max(self))
            #zkusim zatim takto, a dalsi indikator z toho pak bude delat lajny?
            self_max = self[-2]
        
        state.ilog(lvl=1,e=f"IND {name}:{funcName} {str(self_max)}", **params)

        # 3 .. 2 nahoru
        if source_array[-2] > source_array[-3]:
            # 2 .. 1 dolu - mame pivot
            if source_array[-2] > source_array[-1]:
                ##jsme max za obdobi
                if source_array[-2] > self_max:
                    return 0, source_array[-2]
                else:
                    return 0, self_max
            # 2 .. 1 nahoru - drzime puvodni -do otocky
            else:
                return 0, self_max

        # 3 ..2 dolu drzime max
        else:
            return 0, self_max

    else:
        return -2, "wrong function"

    return 0, val
    
