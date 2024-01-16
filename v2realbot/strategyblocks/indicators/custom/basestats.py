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
import pywt

#vstupem je bud indicator nebo bar parametr
#na tomto vstupu dokaze provest zakladni statisticke funkce pro subpole X hodnot zpatky
#podporovane functions: min, max, mean
def basestats(state, params, name, returns):
    funcName = "basestats"
    #name of indicator or 
    source = safe_get(params, "source", None)
    lookback = safe_get(params, "lookback", None)
    func = safe_get(params, "function", None)
    source_dict = defaultdict(list)
    source_dict[source] = get_source_series(state, source)

    try:
        self = state.indicators[name]
    except KeyError:
        self = state.cbar_indicators[name]

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
    #linregress mutlioutput 
    # slope : float, Slope of the regression line.
    # intercept : float, Intercept of the regression line.
    # rvalue : float, The Pearson correlation coefficient. The square of rvalue is equal to the coefficient of determination.
    # pvalue : float, The p-value for a hypothesis test whose null hypothesis is that the slope is zero, using Wald Test with t-distribution of the test statistic. See alternative above for alternative hypotheses.
    # stderr : float
    elif func == "linregress":
        if len(source_array) < 4:
            return -2, "less than 4 elmnts"
        try:
            val = []
            np.seterr(all="raise")
            slope, intercept, rvalue, pvalue, stderr = linregress(np.arange(len(source_array)), source_array)
            val = [slope*1000, intercept,rvalue, pvalue, stderr]
        except FloatingPointError:
            return -2, "FloatingPointError"
    #linregres slope DECOMM
    elif func == "slope":
        if len(source_array) < 4:
            return -2, "less than 4 elmnts"
        try:
            np.seterr(all="raise")
            val, _, _, _, _ = linregress(np.arange(len(source_array)), source_array)
            val = val*1000
        except FloatingPointError:
            return -2, "FloatingPointError"
    #zatim takto, dokud nebudou podporovany indikatory s vice vystupnimi - DECOMM
    elif func == "intercept":
        if len(source_array) < 4:
            return -2, "less than 4 elmnts"
        try:
            np.seterr(all="raise")
            _, val, _, _, _ = linregress(np.arange(len(source_array)), source_array)
            
            val = round(val, 4)
        except FloatingPointError:
            return -2, "FloatingPointError"
    
    #work with different wavelet names and change max_scale 
    #https://chat.openai.com/c/44b917d7-43df-4d80-be2f-01a5ee92158b
    elif func == "wavelet":
        def extract_wavelet_features(time_series, wavelet_name='morl', max_scale=64):
            scales = np.arange(1, max_scale + 1)
            coefficients, frequencies = pywt.cwt(time_series, scales, wavelet_name)

            # Extract features - for instance, mean and variance of coefficients at each scale
            mean_coeffs = np.mean(coefficients, axis=1)[-1]  # Last value of mean coefficients
            var_coeffs = np.var(coefficients, axis=1)[-1]    # Last value of variance of coefficients
            # Energy distribution for the latest segment
            energy = np.sum(coefficients**2, axis=1)[-1]

            # Entropy for the latest segment
            entropy = -np.sum((coefficients**2) * np.log(coefficients**2), axis=1)[-1]

            # Dominant and mean frequency for the latest segment
            dominant_frequency = frequencies[np.argmax(energy)]
            mean_frequency = 0 # np.average(frequencies, weights=energy)

            return [energy, entropy, dominant_frequency, mean_frequency,mean_coeffs, var_coeffs]
        
        time_series = np.array(source_array)  
        
        wavelet_name = "morl"       
        max_scale = 64
        features = extract_wavelet_features(time_series)
        return 0, features

    #better fourier for frequency bins as suggested here https://chat.openai.com/c/44b917d7-43df-4d80-be2f-01a5ee92158b
    elif func == "fourier":
        def compute_fft_features(time_series, num_bins):
            n = len(time_series)
            yf = fft(time_series)
            
            # Frequency values for FFT output
            xf = np.linspace(0.0, 1.0/(2.0), n//2)

            # Compute power spectrum
            power_spectrum = np.abs(yf[:n//2])**2

            # Define frequency bins
            max_freq = 1.0 / 2.0
            bin_edges = np.linspace(0, max_freq, num_bins + 1)
            
            # Initialize feature array
            features = np.zeros(num_bins)

            # Compute power in each bin
            for i in range(num_bins):
                # Find indices of frequencies in this bin
                indices = np.where((xf >= bin_edges[i]) & (xf < bin_edges[i+1]))[0]
                features[i] = np.sum(power_spectrum[indices])
            
            return features

        # Example usage
        time_series = np.array(source_array)  # Replace with your data
        num_bins = 20  # Example: 10 frequency bins
        features = compute_fft_features(time_series, num_bins)
        return 0, features.tolist()

    #returns X frequencies 
    elif func == "fourier_old":
        time_series = np.array(source_array)
        n = len(time_series)

        # Compute the Fourier transform
        yf = fft(time_series)
        xf = np.linspace(0.0, 1.0/(2.0), n//2)

        #three most dominant frequencies
        dominant_frequencies = xf[np.argsort(np.abs(yf[:n//2]))[-3:]]
        state.ilog(lvl=1,e=f"IND {name}:{funcName} 3 dominant freq are {str(dominant_frequencies)}", **params)
        #rt = dict(zip(returns, dominant_frequencies.tolist()))
        return 0, dominant_frequencies.tolist()


        # if returns is not None:
        #     #vracime druhou
        #     if returns == "second":
        #         if len(dominant_frequencies) > 1:
        #             val = dominant_frequencies[-2]
        #         else:
        #             val = 0
        # else:
        #     #vracime most dominant
        #     val = float(np.max(dominant_frequencies))
        #     return 0, val
        
    #returns histogram bins https://chat.openai.com/share/034f8742-b091-4859-8c3e-570edb9c1006
    # pocet vyskytu v danem binu
    elif func == "histogram":

        # Convert to numpy array
        dt = np.array(source_array)

        # Create 4 bins
        bins = np.histogram_bin_edges(dt, bins=4)

        # Assign elements to bins
        bin_indices = np.digitize(dt, bins)

        # Calculate mean for each bin
        means = [dt[bin_indices == i].mean() if dt[bin_indices == i].size > 0 else 0 for i in range(1, len(bins))]
        return 0, dict(zip(returns, means))

        # #takes only first N - items
        # dt = np.array(source_array)
        # #creates 4 buckets
        # bins = 4
        # mean_of_4th_bin = np.mean(dt[np.where(np.histogram(dt, bins)[1][3] <= dt)[0]])
        # if not np.isfinite(mean_of_4th_bin):
        #     mean_of_4th_bin = 0
        # return 0, float(mean_of_4th_bin)

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
    
