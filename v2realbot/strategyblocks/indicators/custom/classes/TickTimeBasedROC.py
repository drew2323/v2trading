from collections import deque
#import time
from v2realbot.strategyblocks.indicators.custom.classes.indicatorbase import IndicatorBase

class TickTimeBasedROC(IndicatorBase):
    def __init__(self, state, window_size_seconds=5):
        """
        Initialize the TimeBasedROC class.
        :param window_size_seconds: Window size in seconds for the rate of change.
        """
        super().__init__(state)
        self.window_size_seconds = window_size_seconds
        self.tick_data = deque()  # Efficient deque for (timestamp, price)

    def next(self, time, close):
        """
        Update the ROC with a new tick time and price.
        :param new_time: Timestamp of the new tick (float with up to 6 decimals).
        :param new_price: Price of the new tick.
        :return: The updated ROC value, or None if the window is not yet full.
        """
        new_time = time[-1]
        new_price = close[-1]
        # Add new tick data
        self.tick_data.append((new_time, new_price))

        # Remove old data outside the time window efficiently
        while self.tick_data and new_time - self.tick_data[0][0] > self.window_size_seconds:
            self.tick_data.popleft()

        if len(self.tick_data) >= 2:
            # Compute ROC using the earliest and latest prices in the window
            old_time, old_price = self.tick_data[0]
            roc = ((new_price - old_price) / old_price) * 100 if old_price != 0 else 0
            return round(float(roc),5)
        else:
            return 0  # ROC is undefined until the window has enough data
