from collections import deque
from v2realbot.strategyblocks.indicators.custom.classes.indicatorbase import IndicatorBase


class TickCount(IndicatorBase):
    """
    Calculates the count of ticks within a rolling time window in seconds.
    """
    def __init__(self, window_size_seconds=5, state=None):
        super().__init__(state)
        self.window_size_seconds = window_size_seconds
        self.tick_times = deque()
        self.tick_count = 0

    def next(self, timestamp):
        timestamp = timestamp[-1]
        # Remove old timestamps outside the time window
        while self.tick_times and timestamp - self.tick_times[0] > self.window_size_seconds:
            self.tick_times.popleft()
            self.tick_count -= 1

        # Add new timestamp
        self.tick_times.append(timestamp)
        self.tick_count += 1

        return self.tick_count