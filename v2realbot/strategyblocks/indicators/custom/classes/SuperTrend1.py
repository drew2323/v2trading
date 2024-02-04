from v2realbot.strategyblocks.indicators.custom.classes.indicatorbase import IndicatorBase
from collections import deque

class SuperTrend1(IndicatorBase):
    """
    The SuperTrend indicator is a trend following indicator which uses ATR to calculate its values.
    It returns a list with three elements: [up, dn, is_trend].
    `is_trend` can be 1 (uptrend), -1 (downtrend), or 0 (no trend or not enough data).
    If there are not enough values for ATR, it returns close[-1] for both `up` and `dn`, and 0 for `is_trend`.
    
    Note: Code generated with Indicator Plugin Builder.
    Link: [Indicator Plugin Builder Conversation](https://openai.com/chat/)
    """

    def __init__(self, multiplier=3, period=14, state=None):
        super().__init__(state)
        self.multiplier = multiplier
        self.period = period
        self.atr_values = deque(maxlen=period)
        self.previous_supertrend = None
        self.previous_close = None
        self.previous_trend = 0

    def next(self, high, low, close):
        if len(high) < self.period or len(low) < self.period or len(close) < self.period:
            return [close[-1], close[-1], 0]

        # Calculate True Range
        tr = max(high[-1] - low[-1], abs(high[-1] - close[-2]), abs(low[-1] - close[-2]))
        self.atr_values.append(tr)

        if len(self.atr_values) < self.period:
            return [close[-1], close[-1], 0]

        # Calculate ATR
        atr = sum(self.atr_values) / self.period

        # Calculate Supertrend
        up = close[-1] - (self.multiplier * atr)
        dn = close[-1] + (self.multiplier * atr)

        if self.previous_supertrend is None:
            self.previous_supertrend = up

        trend = 0
        if close[-1] > self.previous_supertrend:
            trend = 1
            up = max(up, self.previous_supertrend)
        elif close[-1] < self.previous_supertrend:
            trend = -1
            dn = min(dn, self.previous_supertrend)

        self.previous_supertrend = up if trend == 1 else dn
        self.previous_close = close[-1]
        self.previous_trend = trend

        return [up, dn, trend]
