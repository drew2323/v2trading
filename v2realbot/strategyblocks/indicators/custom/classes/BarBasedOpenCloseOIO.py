from collections import deque
#import time
from v2realbot.strategyblocks.indicators.custom.classes.indicatorbase import IndicatorBase

#WIP 
class BarBasedOpenCloseOIO(IndicatorBase):
    """
    Bar Based Order Imbalance Oscillator (OIO) focusing on the imbalance between buying and selling
    pressure in the market inside each bar. Is is reset when new bar arrives.

    Accept continous cbar, stores on the level of bar.

    Průběžně počítá imbalanci předchozích cen (od open do close) v rámci daného baru.
    """
    def __init__(self, state=None):
        super().__init__(state)
        self.old_data = deque()  # Stores tuples of (price, volume)
        self.prev_index = None

    def next(self, index, close):
        index, new_price = index[-1], close[-1]

        # Remove old data when a new bar comes
        if self.prev_index is not None and self.prev_index != index:
            self.old_data.clear()

        self.prev_index = index

        upward_pressure = 0
        downward_pressure = 0

        # Calculate price changes and pressures, optionally weighted by volume
        for old_price in self.old_data:
            price_change = new_price - old_price
            if price_change > 0:
                upward_pressure += price_change
            elif price_change < 0:
                downward_pressure += abs(price_change)

        # Add new tick data with volume
        self.old_data.append(new_price)

        # Calculate OIO
        total_pressure = upward_pressure + downward_pressure
        if total_pressure > 0:
            oio = (upward_pressure - downward_pressure) / total_pressure
        else:
            oio = 0  # OIO is zero if there's no pressure in either direction

        return oio

# Example usage
# oio_indicator_weighted = BarBasedOpenCloseOIO(use_volume_weighting=True)
# oio_indicator_unweighted = BarBasedOpenCloseOIO(use_volume_weighting=False)
# Example tick data: [(index, close, volume)]
# old_data = [(1, 100, 500), (1, 101, 600), ..., (2, 102, 550), ...]
# for data in old_data:
#     oio_value_weighted = oio_indicator_weighted.next(*data)
#     oio_value_unweighted = oio_indicator_unweighted.next(*data)
#     print(f"Weighted Bar-Based OIO: {oio_value_weighted:.2f}, Unweighted Bar-Based OIO: {oio_value_unweighted:.2f}")