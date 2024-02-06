from v2realbot.strategyblocks.indicators.custom.classes.indicatorbase import IndicatorBase
from collections import deque
import numpy as np

class SuperTrendTV(IndicatorBase):
    """
    The SuperTrend indicator is a trend following indicator that is used to identify the direction of the price relative to its historical volatility. 
    It combines the Average True Range (ATR) with the moving average to determine trend direction and reversal points.
    This implementation was generated with Indicator Plugin Builder.
    See conversation: [Indicator Plugin Builder](https://chat.openai.com/g/g-aCKuSmbIe-indicator-plugin-builder/c/1ad650dc-05f1-4cf6-b936-772c0ea86ffa)
    inspirace https://www.tradingview.com/script/r6dAP7yi/
    """
    
    def __init__(self, atr_period=10, atr_multiplier=3.0, state=None):
        super().__init__(state)
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.highs = deque(maxlen=atr_period)
        self.lows = deque(maxlen=atr_period)
        self.closes = deque(maxlen=atr_period)
        self.up = None
        self.down = None
        self.trend = 0

    def next(self, high, low, close):
        self.highs.append(high[-1])
        self.lows.append(low[-1])
        self.closes.append(close[-1])

        if len(self.highs) < self.atr_period:
            return [close[-1], close[-1], 0]

        tr = [max(hi - lo, abs(hi - cl), abs(lo - cl))
              for hi, lo, cl in zip(self.highs, self.lows, self.closes)]
        atr = np.mean(tr[-self.atr_period:])

        src = (high[-1] + low[-1]) / 2
        up = src - (self.atr_multiplier * atr)
        dn = src + (self.atr_multiplier * atr)

        if self.up is None:
            self.up = up
            self.down = dn
        else:
            self.up = max(up, self.up) if close[-2] > self.up else up
            self.down = min(dn, self.down) if close[-2] < self.down else dn

        # Update trend for the first time if it's still at initial state
        if self.trend == 0:
            self.trend = 1 if close[-1] > self.down else -1 if close[-1] < self.up else 0
        else:
            # Update trend based on previous values if it's not at initial state
            self.trend = 1 if (self.trend == -1 and close[-1] > self.down) else -1 if (self.trend == 1 and close[-1] < self.up) else self.trend

        #previous_trend = self.trend
        #self.trend = 1 if (self.trend == -1 and close[-1] > self.down) else -1 if (self.trend == 1 and close[-1] < self.up) else self.trend

        return [self.up, self.down, self.trend]
