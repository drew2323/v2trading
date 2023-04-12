from alpaca.data.historical import CryptoHistoricalDataClient, StockHistoricalDataClient
from alpaca.data.requests import CryptoLatestTradeRequest, StockLatestTradeRequest, StockLatestBarRequest, StockTradesRequest
from alpaca.data.enums import DataFeed
from v2realbot.config import API_KEY, SECRET_KEY, MAX_BATCH_SIZE
#from v2realbot.utils.utils import zoneNY
from datetime import datetime, timezone, time, timedelta, date
import pytz
from rich import print
from pandas import to_datetime

#práce s datumy

zone_NY = pytz.timezone('America/New_York')
zoneNY=zone_NY

# parametry = {}
# symbol = ["C","BAC"]
# client = StockHistoricalDataClient(API_KEY, SECRET_KEY, raw_data=True)
# datetime_object_from = datetime(2023, 3, 16, 17, 51, 38, tzinfo=timezone.utc)
# datetime_object_to = datetime(2023, 3, 16, 17, 52, 39, tzinfo=timezone.utc)
# trades_request = StockTradesRequest(symbol_or_symbols=symbol, feed = DataFeed.SIP, start=datetime_object_from, end=datetime_object_to)

# all_trades = client.get_stock_trades(trades_request)

# print(len(all_trades))

# for i in all_trades:
#     print(all_trades[i])

# timeZ_Ny = pytz.timezone('America/New_York')
# MARKET_OPEN = time(hour=9, minute=30, second=0, tzinfo=timeZ_Ny)
# MARKET_CLOSE = time(hour=16, minute=30, second=0, tzinfo=timeZ_Ny)

# print(MARKET_OPEN)
# print(MARKET_CLOSE)



def is_open_rush(dt: datetime, mins: int = 30):
    """"
    Returns true if time is within morning rush (open+mins)
    """
    dt = dt.astimezone(zoneNY)
    business_hours = {
        "from": time(hour=9, minute=30),
        "to": time(hour=16, minute=0)
    }
    rushtime = (datetime.combine(date.today(), business_hours["from"]) + timedelta(minutes=mins)).time()
    return business_hours["from"] <= dt.time() < rushtime

def is_close_rush(dt: datetime, mins: int = 30):
    """"
    Returns true if time is within morning rush (open+mins)
    """
    dt = dt.astimezone(zoneNY)
    business_hours = {
        "from": time(hour=9, minute=30),
        "to": time(hour=16, minute=0)
    }
    rushtime = (datetime.combine(date.today(), business_hours["to"]) - timedelta(minutes=mins)).time()
    return rushtime <= dt.time() <= business_hours["to"]


now = datetime.now(tz=zone_NY)
now = datetime(2023, 3, 16, 15, 50, 00, tzinfo=zone_NY)
print(now)
print("is closing rush", is_close_rush(now, 0))



""""
TODO toto pridat do utils a pak bud do agregatoru
a nebo do spis offline_loaderu (tam je muzu filtrovat) - pripadne nejake flagy
pak pokracovat v BASE kde jsem skoncil vcera


returns if date is within market open times (no holidays implemented yet)
input is timezone aware datetime
"""
def is_open_hours(dt):

    dt = dt.astimezone(pytz.timezone('America/New_York'))
    print("ameriko time", dt)

    business_hours = {
        # monday = 0, tuesday = 1, ... same pattern as date.weekday()
        "weekdays": [0, 1, 2, 3, 4],
        "from": time(hour=9, minute=30),
        "to": time(hour=16, minute=30)
    }

    holidays = [date(2022, 12, 24), date(2022, 2, 24)]

    return dt.weekday() in business_hours["weekdays"] \
           and dt.date() not in holidays \
           and business_hours["from"] <= dt.time() < business_hours["to"]

now = datetime.now(tz=zone_NY)
now = datetime(2023, 3, 16, 15, 51, 38, tzinfo=zone_NY)
now = datetime(2023, 3, 16, 15, 51, 38, tzinfo=timezone.utc)
print(now)
print("is business hour", is_open_hours(now))


def parse_nanodate(s):
  """
  parse date, ignore nanoseconds
  sample input: 2020-12-31T16:20:00.000000123Z
  --> 123ns will be ignored
  """
  print(s[0:26]+s[len(s) - 1]+'+0000')
  return datetime.strptime(
    s[0:26]+s[len(s) - 1]+'+0000', '%Y-%m-%dT%H:%M:%S.%fZ%z')

a = "2023-03-17T12:56:37.588388864Z"
b = "2023-03-17T12:56:41.332702720Z"
c = "2023-03-17T12:56:41.3327027Z"
d = "2023-03-17T12:01:36.13168Z"


print(to_datetime(d))

print(int(datetime(2023, 3, 17, 9, 30, 0, 0, tzinfo=zone_NY).timestamp()))
print(int(datetime(2023, 3, 17, 16, 00, 0, 0, tzinfo=zone_NY).timestamp()))

# print(a)
# print(parse_nanodate(a).astimezone(tz=zone_NY))
# print(b)
# print(parse_nanodate(b))
# print(c)
# print(parse_nanodate(c))
# print(d)
# print(parse_nanodate(d))
