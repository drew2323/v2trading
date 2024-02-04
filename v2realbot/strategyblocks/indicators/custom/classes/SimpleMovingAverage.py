from v2realbot.strategyblocks.indicators.custom.classes.indicatorbase import IndicatorBase
from collections import deque

class SimpleMovingAverage(IndicatorBase):
    """
    Calculates the Simple Moving Average (SMA) of a given data list.
    The SMA is calculated over a specified window size.
    If there are insufficient data points for the full window, the behavior
    can be controlled by `return_last_if_insufficient`: if True, the last data point is returned,
    otherwise, 0 is returned.
    """
    def __init__(self, period, return_last_if_insufficient=False, state=None):
        super().__init__(state)
        self.window_size = period
        self.return_last_if_insufficient = return_last_if_insufficient
        self.data_points = deque(maxlen=period)

    def next(self, data):
        self.data_points.append(data[-1])
        if len(self.data_points) < self.window_size:
            return data[-1] if self.return_last_if_insufficient else 0
        return sum(self.data_points) / len(self.data_points)
