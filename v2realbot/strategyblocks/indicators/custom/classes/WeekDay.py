from v2realbot.strategyblocks.indicators.custom.classes.indicatorbase import IndicatorBase
from datetime import datetime, time
from v2realbot.utils.utils import zoneNY

#do budoucna predelat na staticky indikator
class WeekDay(IndicatorBase):
    def __init__(self, state):
        super().__init__(state)
        self.weekday = datetime.fromtimestamp(state.time).astimezone(zoneNY).weekday()

    def next(self):
        return self.weekday