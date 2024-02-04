from v2realbot.strategyblocks.indicators.custom.classes.indicatorbase import IndicatorBase
from collections import deque

class SuperTrendBard(IndicatorBase):
    """
    Calculates Supertrend indicator values.
    """

    def __init__(self, period=10, multiplier=3, state=None):
        super().__init__(state)
        self.atr_period = period
        self.multiplier = multiplier
        self.highs = deque(maxlen=period)
        self.lows = deque(maxlen=period)
        self.atr = 0
        self.upbound = None  # Can set a default value if desired
        self.downbound = None  # Can set a default value if desired
        self.is_trend = None

    def next(self, high, low, close):
        high = high[-1]
        low = low[-1]
        close = close[-1]

    # Update ATR calculation
        self.highs.append(high)
        self.lows.append(low)

        # Check for sufficient data
        if len(self.highs) < self.atr_period or len(self.lows) < self.atr_period:
            return [close, close, 0]

        if len(self.highs) == self.atr_period:
            true_range = max(high - low, abs(high - self.highs[0]), abs(low - self.lows[0]))
            self.atr = (self.atr * (self.atr_period - 1) + true_range) / self.atr_period

        # Calculate Supertrend
        if self.upbound is None:
            self.upbound = close - (self.multiplier * self.atr)
            self.downbound = close + (self.multiplier * self.atr)
            self.is_trend = None  # Set initial trend state to unknown
        else:
            # Determine trend based on previous trend and current price
            if self.is_trend == 1:
                # Uptrend continuation
                self.upbound = max(self.upbound, close - (self.multiplier * self.atr))  # Adjust upbound dynamically
                self.is_trend = 1 if close > self.upbound else 0  # Recalculate trend if needed
            elif self.is_trend == -1 and close < self.downbound:
                # Downtrend continues
                self.downbound = min(self.downbound, low + (self.multiplier * self.atr))
                self.is_trend = -1
            else:
                # Recalculate trend based on current price
                self.is_trend = 1 if close > self.upbound else -1 if close < self.downbound else 0
                # Update Supertrend lines based on new trend
                if self.is_trend == 1:
                    self.upbound = max(self.upbound, close - (self.multiplier * self.atr))
                else:
                    self.downbound = min(self.downbound, low + (self.multiplier * self.atr))

        return [self.upbound, self.downbound, self.is_trend]
