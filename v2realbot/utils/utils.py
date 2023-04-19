from msgpack.ext import Timestamp
import math
from queue import Queue
from datetime import datetime, timezone, time, timedelta, date
import pytz
from dateutil import tz
from rich import print
import decimal
from icecream import ic
from v2realbot.enums.enums import RecordType, Mode, StartBarAlign
import pickle
import os
from v2realbot.common.model import StrategyInstance, Runner
from typing import List
import tomli
from v2realbot.config import DATA_DIR
import requests
from uuid import UUID

def send_to_telegram(message):
    apiToken = '5836666362:AAGPuzwp03tczMQTwTBiHW6VsZZ-1RCMAEE'
    chatID = '5029424778'
    apiURL = f'https://api.telegram.org/bot{apiToken}/sendMessage'

    try:
        response = requests.post(apiURL, json={'chat_id': chatID, 'text': message})
        print(response.text)
    except Exception as e:
        print(e)

#datetime to timestamp
def json_serial(obj):
    """JSON serializer for objects not serializable by default json code
    https://stackoverflow.com/questions/11875770/how-to-overcome-datetime-datetime-not-json-serializable
    """

    if isinstance(obj, (datetime, date)):
        return obj.timestamp()
    if isinstance(obj, UUID):
        return str(obj)
    raise TypeError (str(obj)+"Type %s not serializable" % type(obj))

def parse_toml_string(tomlst: str):
    try:
        tomlst = tomli.loads(tomlst)
    except tomli.TOMLDecodeError as e:
        print("Not valid TOML.", str(e))
        return (-1, None)
    return (0, dict_replace_value(tomlst,"None",None))

#class to persist
class Store:
    stratins : List[StrategyInstance]  = []
    runners: List[Runner] = []
    def __init__(self) -> None:
        self.db_file = DATA_DIR + "/strategyinstances.cache"
        if os.path.exists(self.db_file):
            with open (self.db_file, 'rb') as fp:
                self.stratins = pickle.load(fp)

    def save(self):
        with open(self.db_file, 'wb') as fp:
            pickle.dump(self.stratins, fp)

qu = Queue()

zoneNY = tz.gettz('America/New_York')

def print(*args, **kwargs):
    ic(*args, **kwargs)

def price2dec(price: float) -> float:
    """
    pousti maximalne 2 decimals
    pokud je trojmistne a vic pak zakrouhli na 2, jinak necha
    """
    return round(price,2) if count_decimals(price) > 2 else price

def count_decimals(number: float) -> int:
    """
    Count the number of decimals in a given float: 1.4335 -> 4 or 3 -> 0
    """
    return abs(decimal.Decimal(str(number)).as_tuple().exponent)

def p(var, n = None):
    if n: print(n, f'{var = }')
    else: print(f'{var = }')

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

def is_open_hours(dt):
    """"
    Returns True if market is open that time. Holidays not implemented yet.

    """
    dt = dt.astimezone(zoneNY)
    #print("Ameriko time", dt)

    business_hours = {
        # monday = 0, tuesday = 1, ... same pattern as date.weekday()
        "weekdays": [0, 1, 2, 3, 4],
        "from": time(hour=9, minute=30),
        "to": time(hour=16, minute=0)
    }

    holidays = [date(2022, 12, 24), date(2022, 2, 24)]

    return dt.weekday() in business_hours["weekdays"] \
           and dt.date() not in holidays \
           and business_hours["from"] <= dt.time() < business_hours["to"]

def isfalling(pole: list, pocet: int):
    if len(pole)<pocet: return False
    pole = pole[-pocet:]
    res = all(i > j for i, j in zip(pole, pole[1:]))
    return res

def isrising(pole: list, pocet: int):
    if len(pole)<pocet: return False
    pole = pole[-pocet:]
    res = all(i < j for i, j in zip(pole, pole[1:]))
    return res

def parse_alpaca_timestamp(value: Timestamp):
    return value.seconds + (value.nanoseconds * float(1e-9))

class ltp:
    price={}
    time={}

def trunc(f, n):
    return math.floor(f * 10 ** n) / 10 ** n

class AttributeDict(dict):
    """
    This is adds functions to the dictionary class, no other modifications. This gives dictionaries abilities like:
    print(account.BTC) -> {'available': 1, 'hold': 0}
    account.BTC = "cool"
    print(account.BTC) -> cool
    Basically you can get and set attributes with a dot instead of [] - like dict.available rather than
     dict['available']
    """

    def __init__(self, *args, **kwargs):
        super(AttributeDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

"""""
Helper to replace value in nested dictionaries. Used for TOML to replace "None" string to None type
Also used to type enums.
# See input and output below
output = dict_replace_value(input, 'string', 'something')
"""""
def dict_replace_value(d: AttributeDict, old: str, new) -> AttributeDict:
    x = {}
    for k, v in d.items():
        if isinstance(v, dict):
            v = dict_replace_value(v, old, new)
        elif isinstance(v, list):
            v = list_replace_value(v, old, new)
        elif isinstance(v, str):
            v = new if v == old else v
            if k == "rectype": v = RecordType(v)
            elif k == "align": v = StartBarAlign(v)
            elif k == "mode": v = Mode(v)
        x[k] = v
    return x


def list_replace_value(l: list, old: str, new) -> list:
    x = []
    for e in l:
        if isinstance(e, list):
            e = list_replace_value(e, old, new)
        elif isinstance(e, dict):
            e = dict_replace_value(e, old, new)
        elif isinstance(e, str):
            e = new if e == old else e
        x.append(e)
    return x

