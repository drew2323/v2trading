from v2realbot.strategyblocks.indicators.custom.classes.indicatorbase import IndicatorBase

class CUSUM(IndicatorBase):
    def __init__(self, state, threshold):
        super().__init__(state)
        self.threshold = threshold
        self.cumulative_sum = 0
        self.previous_price = None

    def next(self, new_price):
        if self.previous_price is None:
            # First data point, no previous price to compare with
            self.previous_price = new_price
            return 0

        # Calculate price change
        price_change = new_price - self.previous_price
        self.previous_price = new_price

        # Update cumulative sum
        self.cumulative_sum += price_change

        if self.cumulative_sum > self.threshold:
            self.cumulative_sum = 0  # Reset
            return 1  # Buy signal
        elif self.cumulative_sum < -self.threshold:
            self.cumulative_sum = 0  # Reset
            return -1  # Sell signal

        return 0  # No signal