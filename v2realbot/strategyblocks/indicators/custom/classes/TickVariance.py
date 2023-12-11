import numpy as np
from v2realbot.strategyblocks.indicators.custom.classes.indicatorbase import IndicatorBase

#usecase - pocitat variance ticku
# v ramci BARu - posilame sem index a resetujeme pri naslednem indxu
# do budoucna mo
class TickVariance(IndicatorBase):
    def __init__(self, state, window_size=1):
        """
        Initialize the TickPriceVariance class.

        :param window_size: The size of the window for calculating variance - zatim mame jeden bar, do budoucna X
        """
        super().__init__(state)
        self.window_size = window_size
        self.window_prices = []
        self.prev_index = None

    def next(self, close, index):
        close = close[-1]
        index = index[-1]
        # Add new price to the window
        self.window_prices.append(close)

        if self.prev_index is not None and self.prev_index != index:
            self.window_prices = []

        self.prev_index = index
        # Calculate the variance for the current window
        if len(self.window_prices) > 1:
            return round(float(np.var(self.window_prices)),5)
        else:
            return 0  # Variance is undefined for a single data point

