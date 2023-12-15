from collections import deque
#import time
from v2realbot.strategyblocks.indicators.custom.classes.indicatorbase import IndicatorBase

#WIP 
class TickBasedOIO(IndicatorBase):
    """
    POZOR NIZE JE WEIGHTED VARIANTA - zakomentovana, mozna v budoucnu vyuzit

    tick-based Order Imbalance Oscillator (OIO) focusing on the imbalance between buying and selling
    pressure in the market, calculates the difference in cumulative price changes in both directions 
    over a specified window of time. This approach assumes that larger price movements in one direction
    indicate stronger market pressure from either buyers or sellers.
    """
    def __init__(self, window_size_seconds=5, state=None):
        super().__init__(state)
        self.window_size_seconds = window_size_seconds
        self.tick_data = deque()

    def next(self, time, close):
        new_time, new_price = time[-1], close[-1]

        # Remove old data outside the time window
        while self.tick_data and new_time - self.tick_data[0][0] > self.window_size_seconds:
            self.tick_data.popleft()

        upward_pressure = 0
        downward_pressure = 0

        # Calculate price changes and pressures
        for old_time, old_price in self.tick_data:
            price_change = new_price - old_price
            if price_change > 0:
                upward_pressure += price_change
            elif price_change < 0:
                downward_pressure += abs(price_change)

        # Add new tick data
        self.tick_data.append((new_time, new_price))

        # Calculate OIO
        if upward_pressure + downward_pressure > 0:
            oio = (upward_pressure - downward_pressure) / (upward_pressure + downward_pressure)
        else:
            oio = 0  # OIO is zero if there's no pressure in either direction

        return oio

# # Example usage
# oio_indicator = TickBasedOIO(window_size_seconds=5)

# # Example tick data: (timestamp, price)
# tick_data = [(1, 100), (2, 101), (3, 102), (4, 100), (5, 99), (6, 98), (7, 97), (8, 98), (9, 99), (10, 100)]

# for data in tick_data:
#     oio_value = oio_indicator.next(data)
#     print(f"Tick-Based OIO: {oio_value:.2f}")


#WEIGHTED VARIANT

# from collections import deque
# from v2realbot.strategyblocks.indicators.custom.classes.indicatorbase import IndicatorBase

# class TickBasedOIO(IndicatorBase):
#     """
#     Tick-based Order Imbalance Oscillator (OIO) focusing on the imbalance between buying and selling
#     pressure in the market, calculates the difference in cumulative price changes in both directions 
#     over a specified window of time, optionally weighted by volume.
#     """
#     def __init__(self, window_size_seconds=5, use_volume_weighting=False, state=None):
#         super().__init__(state)
#         self.window_size_seconds = window_size_seconds
#         self.use_volume_weighting = use_volume_weighting
#         self.tick_data = deque()

#     def next(self, time, close, volume):
#         new_time, new_price, new_volume = time[-1], close[-1], volume[-1]

#         # Remove old data outside the time window
#         while self.tick_data and new_time - self.tick_data[0][0] > self.window_size_seconds:
#             self.tick_data.popleft()

#         upward_pressure = 0
#         downward_pressure = 0

#         # Calculate price changes and pressures, optionally weighted by volume
#         for old_time, old_price, old_volume in self.tick_data:
#             price_change = new_price - old_price
#             weighted_change = price_change * old_volume if self.use_volume_weighting else price_change
#             if price_change > 0:
#                 upward_pressure += weighted_change
#             elif price_change < 0:
#                 downward_pressure += abs(weighted_change)

#         # Add new tick data with volume
#         self.tick_data.append((new_time, new_price, new_volume))

#         # Calculate OIO
#         total_pressure = upward_pressure + downward_pressure
#         if total_pressure > 0:
#             oio = (upward_pressure - downward_pressure) / total_pressure
#         else:
#             oio = 0  # OIO is zero if there's no pressure in either direction

#         return oio

# Example usage
# oio_indicator_weighted = TickBasedOIO(window_size_seconds=5, use_volume_weighting=True)
# oio_indicator_unweighted = TickBasedOIO(window_size_seconds=5, use_volume_weighting=False)
# Example tick data: (timestamp, price, volume)
# tick_data = [(1, 100, 500), (2, 101, 600), ..., (10, 100, 550)]
# for data in tick_data:
#     oio_value_weighted = oio_indicator_weighted.next(*data)
#     oio_value_unweighted = oio_indicator_unweighted.next(*data)
#     print(f"Weighted Tick-Based OIO: {oio_value_weighted:.2f}, Unweighted Tick-Based OIO: {oio_value_unweighted:.2f}")
