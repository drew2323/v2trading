from v2realbot.strategyblocks.indicators.custom.classes.indicatorbase import IndicatorBase
import pywt
import numpy as np

class DWT(IndicatorBase):
    def __init__(self, state=None, wavelet='db1', levels=2):
        super().__init__(state)
        self.wavelet = wavelet
        self.levels = levels

    def next(self, close):
        coeffs = pywt.wavedec(close, self.wavelet, level=self.levels)
        # Zeroing out all detail coefficients
        coeffs = [coeffs[0]] + [np.zeros_like(c) for c in coeffs[1:]]

        # Reconstruct the signal using only the approximation coefficients
        reconstructed_signal = pywt.waverec(coeffs, self.wavelet)

        # Handle length difference
        length_difference = len(close) - len(reconstructed_signal)
        if length_difference > 0:
            reconstructed_signal = np.pad(reconstructed_signal, (0, length_difference), 'constant', constant_values=(0, 0))

        self.state.indicators["MultiLevelDWT"] = reconstructed_signal.tolist()

        return float(reconstructed_signal[-1])
