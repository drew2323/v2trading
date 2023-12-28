from v2realbot.strategyblocks.indicators.custom.classes.indicatorbase import IndicatorBase
from datetime import datetime, time
from v2realbot.utils.utils import zoneNY

class DayTime(IndicatorBase):
    def __init__(self, state):
        super().__init__(state)
        #TODO toto v initu dynamicky 
        # Convert market open/close times to seconds since epoch
        self.market_open_time = self._time_to_seconds_since_epoch(time(9, 30), state)
        self.market_close_time = self._time_to_seconds_since_epoch(time(16, 0), state)
        # Total market duration in seconds
        self.total_market_duration = self.market_close_time - self.market_open_time

    def _time_to_seconds_since_epoch(self, market_time, state):
        # Convert a time object to seconds since epoch for a typical day (e.g., today)
        today = datetime.fromtimestamp(state.time).astimezone(zoneNY).date()
        market_datetime = zoneNY.localize(datetime.combine(today, market_time))
        return market_datetime.timestamp()

    def next(self, time):
        current_timestamp = time[-1]
        # Check if the current time is within market hours
        if self.market_open_time <= current_timestamp <= self.market_close_time:
            time_since_open = current_timestamp - self.market_open_time
            normalized_time = time_since_open / self.total_market_duration
            return normalized_time
        else:
            return 0