from v2realbot.strategyblocks.indicators.custom.classes.indicatorbase import IndicatorBase
from collections import deque
import numpy as np

class SuperTrend(IndicatorBase):
    """
    Advanced implementation of the SuperTrend indicator, dynamically calculating the trend direction.
    This approach considers the previous trend when determining the new trend, making the indicator 
    more responsive to price changes. Returns [up, dn, is_trend] with is_trend being 0 (no trend), 
    1 (uptrend), or -1 (downtrend). If there aren't enough values for ATR, it returns the last close 
    for up and dn, and 0 for is_trend.
    Generated with Indicator Plugin Builder.
    Link: [https://chat.openai.com/g/g-aCKuSmbIe-indicator-plugin-builder/c/8cf9ec38-31e0-4577-8331-22919ae149ab]
    
    Zajimavá advanced verze - detaily viz link výše
    """
    def __init__(self, atr_period=14, multiplier=3, state=None):
        super().__init__(state)
        self.atr_period = atr_period
        self.multiplier = multiplier
        self.tr_queue = deque(maxlen=atr_period)
        self.final_upperband = None
        self.final_lowerband = None
        self.is_trend = 0

    def next(self, high, low, close):
        if len(close) < self.atr_period:
            return [close[-1], close[-1],close[-1], close[-1], 0]

        # True Range calculation
        current_high = high[-1]
        current_low = low[-1]
        previous_close = close[-2] if len(close) > 1 else close[-1]
        true_range = max(current_high - current_low, abs(current_high - previous_close), abs(current_low - previous_close))

        # Updating the True Range queue
        self.tr_queue.append(true_range)
        if len(self.tr_queue) < self.atr_period:
            return [close[-1], close[-1],close[-1], close[-1], 0]

        # ATR calculation
        atr = sum(self.tr_queue) / self.atr_period

        # Basic upper and lower bands
        basic_upperband = (current_high + current_low) / 2 + self.multiplier * atr
        basic_lowerband = (current_high + current_low) / 2 - self.multiplier * atr

        # Final upper and lower bands
        if self.final_upperband is None or self.final_lowerband is None:
            self.final_upperband = basic_upperband
            self.final_lowerband = basic_lowerband
        else:
            if close[-1] <= self.final_upperband:
                self.final_upperband = basic_upperband
            if close[-1] >= self.final_lowerband:
                self.final_lowerband = basic_lowerband

        # Trend determination
        if close[-1] > self.final_upperband:
            self.is_trend = 1
        elif close[-1] < self.final_lowerband:
            self.is_trend = -1

        return [basic_upperband,basic_lowerband,self.final_upperband, self.final_lowerband, self.is_trend]
