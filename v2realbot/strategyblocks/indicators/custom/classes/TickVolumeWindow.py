from collections import deque
from v2realbot.strategyblocks.indicators.custom.classes.indicatorbase import IndicatorBase


class TickVolumeWindow(IndicatorBase):
    """
    Calculates volume in the rolling time window in seconds.
    """
    def __init__(self, window_size_seconds=5, state=None):
        super().__init__(state)
        self.window_size_seconds = window_size_seconds
        self.volume = 0
        self.time_start = None

    def next(self, timestamp, volume):
        timestamp = timestamp[-1]
        volume = volume[-1]

        if self.time_start is None:
            self.time_start = timestamp

        if self.time_start + self.window_size_seconds < timestamp:
            self.volume = 0
            self.time_start = timestamp
        
        self.volume += volume

        return self.volume 