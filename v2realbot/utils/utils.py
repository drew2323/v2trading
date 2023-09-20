from msgpack.ext import Timestamp
import math
from queue import Queue
from datetime import datetime, timezone, time, timedelta, date
import pytz
#from dateutil import tz
from rich import print as richprint
import decimal
from v2realbot.enums.enums import RecordType, Mode, StartBarAlign
import pickle
import os
from v2realbot.common.model import StrategyInstance, Runner, RunArchive, RunArchiveDetail, Intervals, SLHistory
from v2realbot.common.PrescribedTradeModel import Trade, TradeDirection, TradeStatus, TradeStoplossType
from typing import List
import tomli
from v2realbot.config import DATA_DIR, QUIET_MODE,NORMALIZED_TICK_BASE_PRICE
import requests
from uuid import UUID
#from decimal import Decimal
from enum import Enum
#from v2realbot.enums.enums import Order
from v2realbot.common.model import Order as btOrder, TradeUpdate as btTradeUpdate
from alpaca.trading.models import Order, TradeUpdate
import numpy as np
import pandas as pd
from collections import deque

def pct_diff(num1: float, num2: float, decimals: int = 3, absolute: bool = False):
    if num1 == 0:
        return 0
    
    diff = num1 - num2
    if absolute:
        percentage_diff = (abs(diff) / abs(num2)) * 100
    else:
        percentage_diff = (diff / abs(num2)) * 100
    return round(percentage_diff, decimals)

def is_still(lst: list, how_many_last_items: int, precision: int):
    """
    Checks if the last N members of a list are equal within a given precision.

    Args:
    lst (list): The list of floats to check.
    how_many_last_items (int): The number of last items to compare.
    precision (int): The number of decimal places to round to for comparison.

    Returns:
    bool: True if the last N members are equal within the specified precision, False otherwise.
    """
    if len(lst) < how_many_last_items:
        raise ValueError("The list does not have enough items to compare.")

    last_items = lst[-how_many_last_items:]  # Get the last N items
    rounded_last_items = [round(item, precision) for item in last_items]
    
    # Check if all rounded items are equal
    return all(rounded_last_items[0] == item for item in rounded_last_items)


#is_pivot function to check if there is A(V) shaped pivot in the list, each leg consists of N points
#middle point is the shared one [1,2,3,2,1] - one leg is [1,2,3] second leg is [3,2,1]
def is_pivot(source: list, leg_number: int, type: str = "A"):
    if len(source) < (2 * leg_number)-1:
        print("Not enough values in the list")
        return False
    
    left_leg = source[-2*leg_number+1:-leg_number+1]
    right_leg = source[-leg_number:]
    
    if type == "A":
        if isrising(left_leg) and isfalling(right_leg):
            return True
        else:
            return False
    elif type == "V":
        if isfalling(left_leg) and isrising(right_leg):
            return True
        else:
            return False
    else:
        print("Unknown type")
        return False

def crossed_up(threshold, list):
    """check if threshold has crossed up last thresholdue in list"""
    try:
        if threshold < list[-1] and threshold > list[-2]:
            return True

        # #upraveno, ze threshold muze byt vetsi nez predpredposledni
        # if threshold < list[-1] and threshold >= list[-2] or threshold < list[-1] and threshold >= list[-3]:
        #     return True
        # else:
        #     return False
    except IndexError:
        return False
    
def crossed_down(threshold, list):
    """check if threshold has crossed down last thresholdue in list"""
    """
    Checks if a threshold has just crossed down a line represented by a list.

    Args:
    threshold (float): The threshold value to check.
    lst (list): The list representing the line.

    Returns:
    bool: True if the threshold just crossed down the line, False otherwise.
    """

    try:
        #upraveno na jednoduchou verzi
        if threshold > list[-1] and threshold < list[-2]:
            return True

        return False


        # #upraveno, ze threshold muze byt mensi nez predpredposledni
        # if threshold > list[-1] and threshold <= list[-2] or threshold > list[-1] and threshold <= list[-3]:
        #     return True
        # else:
        #     return False
    except IndexError:
        return False

def crossed(threshold, list):
    """check if threshold has crossed last thresholdue in list"""
    if crossed_down(threshold, list) or crossed_up(threshold, list):
        return True
    else:
        return False

def get_tick(price: float, normalized_ticks: float = 0.01):
    """
    Pozor existuje varianta "normalize_tick", ktera je lepsi a podporuje direktivy ve strategii:
        Normalize_ticks= true
        Normalized Tick base price = 30
    Tahle verze pracuje s globalnim nastavenim.
    Prevede normalizovany tick na tick odpovidajici vstupni cene
    vysledek je zaokoruhleny na 2 des.mista

    u cen pod 30, vrací 0.01. U cen nad 30 vrací pomerne zvetsene, 

    """
    if price<NORMALIZED_TICK_BASE_PRICE:
        return normalized_ticks
    else:
        #ratio of price vs base price
        ratio = price/NORMALIZED_TICK_BASE_PRICE
        return price2dec(ratio*normalized_ticks)

def eval_cond_dict(cond: dict) -> tuple[bool, str]:
    """
    evaluates conditions dictionary and return result and name of condition
    examples:
    buy_cond["AND"]["1and"] = True
    buy_cond["AND"]["2and"] = False
    buy_cond["OR"]["3or"] = False
    buy_cond["OR"]["4or"] = False
    buy_cond["5single"] = False
    buy_cond["5siddngle"] = False
    group eval rules. 1. single 2. AND 3. ORS
    """
    msg = {}
    ret = []
    
    ##check AND group
    if 'AND' in cond.keys() and len(cond["AND"])>0:
        msg["AND"] = {}
        for key in cond["AND"]:
            res = cond["AND"][key]
            ret.append(res)
            msg["AND"][key] = (str(res).upper() if res else str(res))
            #msg += "[AND]" + key + ":" + (str(res).upper() if res else str(res)) + " "

        if all(ret):
            return True, msg
        
    #eval OR groups 
    if "OR" in cond.keys() and len(cond["OR"])>0:
        ret = []
        msg["OR"] = {}
        for key in cond["OR"]:
            res = cond["OR"][key]
            ret.append(res)
            msg["OR"][key] = (str(res).upper() if res else str(res))
            #msg += "[OR]" + key + ":" + (str(res).upper() if res else str(res)) + " "

        if any(ret):
            return True, msg

    #pokud nemame zadne AND ani OR, tak to je single cond
    ret = []
    for key in cond:
        if key == "AND" or key == "OR":
            continue
        #je to vlastne to same jako OR
        res = cond[key]
        ret.append(res)
        msg[key] = (str(res).upper() if res else str(res))
        #msg += key + ":" + (str(res).upper() if res else str(res)) + " "

    #pokud predchozi single obsahoval True, vratime True jinak False
    return any(ret), msg

def Average(lst):
    return sum(lst) / len(lst)

def safe_get(collection, key, default=None):
    """Get values from a collection without raising errors"""

    try:
        return collection.get(key, default)
    except TypeError:
        pass

    try:
        return collection[key]
    except (IndexError, TypeError):
        pass

    return default

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
    if isinstance(obj, Enum):
        return str(obj)
    if type(obj) is Order:
        return obj.__dict__
    if type(obj) is TradeUpdate:
        return obj.__dict__
    if type(obj) is btOrder:
        return obj.__dict__
    if type(obj) is btTradeUpdate:
        return obj.__dict__
    if type(obj) is RunArchive:
        return obj.__dict__
    if type(obj) is Trade:
        return obj.__dict__
    if type(obj) is RunArchiveDetail:
        return obj.__dict__
    if type(obj) is Intervals:
        return obj.__dict__
    if type(obj) is SLHistory:
        return obj.__dict__
    
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

#zoneNY = tz.gettz('America/New_York')
zoneNY = pytz.timezone('US/Eastern')

def print(*args, **kwargs):
    if QUIET_MODE:
        pass
    else:
        ####ic(*args, **kwargs)
        richprint(*args, **kwargs)

#optimized by BARD
def price2dec(price: float, decimals: int = 2) -> float:
  """Rounds a price to a specified number of decimal places, but only if the
  price has more than that number of decimals.

  Args:
    price: The price to round.
    decimals: The number of decimals to round to.

  Returns:
    A rounded price, or the original price if the price has less than or equal
    to the specified number of decimals.
  """

  if price.is_integer():
    return price

  # Calculate the number of decimal places in the price.
  num_decimals = int(math.floor(math.log10(abs(price - math.floor(price)))))

  # If the price has more than the specified number of decimals, round it.
  if num_decimals > decimals:
    return round(price, decimals)
  else:
    return price

def price2dec_old(price: float, decimals: int = 2) -> float:
    """
    pousti maximalne 2 decimals
    pokud je trojmistne a vic pak zakrouhli na 2, jinak necha
    """
    return round(price,decimals) if count_decimals(price) > decimals else price

def count_decimals(number: float) -> int:
    """
    Count the number of decimals in a given float: 1.4335 -> 4 or 3 -> 0
    """
    return abs(decimal.Decimal(str(number)).as_tuple().exponent)

def round2five(price: float):
    """
    zatim jen na 3 mista -pripadne predelat na dynamicky
    z 23.342 - 23.340
    z 23.346 - 23.345
    """ 
    return (round(price*100*2)/2)/100

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

#optimalized by BARD
def is_window_open(dt: datetime, start: int = 0, end: int = 390):
    """"
    Returns true if time (start in minutes and end in minutes) is in working window
    """
    # Check if start and end are within bounds early to avoid unnecessary computations.
    if start < 0 or start > 389 or end < 0 or end > 389:
        return False

    # Convert the datetime object to the New York time zone.
    dt = dt.astimezone(zoneNY)

    # Get the business hours start and end times.
    business_hours_start = time(hour=9, minute=30)
    business_hours_end = time(hour=16, minute=0)

    # Check if the datetime is within business hours.
    if not business_hours_start <= dt.time() <= business_hours_end:
        return False

    # Calculate the start and end times of the working window.
    working_window_start = (datetime.combine(date.today(), business_hours_start) + timedelta(minutes=start)).time()
    working_window_end = (datetime.combine(date.today(), business_hours_start) + timedelta(minutes=end)).time()

    # Check if the datetime is within the working window.
    return working_window_start <= dt.time() <= working_window_end
#puvodni neoptimalizovana verze
#TODO market time pro dany den si dotahnout z Alpaca
def is_window_open_old(dt: datetime, start: int = 0, end: int = 390):
    """"
    Returns true if time (start in minutes and end in minutes) is in working window
    """
    if start < 0 or start > 389:
        return False
    
    if end < 0 or end > 389:
        return False   

    dt = dt.astimezone(zoneNY)
    business_hours = {
        "from": time(hour=9, minute=30),
        "to": time(hour=16, minute=0)
    }
    startime = (datetime.combine(date.today(), business_hours["from"]) + timedelta(minutes=start)).time()
    endtime = (datetime.combine(date.today(), business_hours["from"]) + timedelta(minutes=end)).time()

    #time not within business hours
    if not business_hours["from"] <= dt.time() <= business_hours["to"]:
        return False
    
    if startime <= dt.time() <= endtime:
        return True
    else:
        return False

def is_close_rush(dt: datetime, mins: int = 30):
    """"
    Returns true if time is within afternoon rush (close-mins)
    """
    dt = dt.astimezone(zoneNY)
    business_hours = {
        "from": time(hour=9, minute=30),
        "to": time(hour=16, minute=0)
    }
    rushtime = (datetime.combine(date.today(), business_hours["to"]) - timedelta(minutes=mins)).time()
    return rushtime <= dt.time() <= business_hours["to"]

def is_open_hours(dt, business_hours: dict = None):
    """"
    Returns True if market is open that time. Holidays not implemented yet.

    """
    dt = dt.astimezone(zoneNY)
    #print("Ameriko time", dt)

    if business_hours is None:
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

#vraci zda dane pole je klesajici (bud cele a nebo jen pocet poslednich)
def isfalling(pole: list, pocet: int = None):
    if pocet is None: pocet = len(pole)
    if len(pole)<pocet: return False
    pole = pole[-pocet:]
    res = all(i > j for i, j in zip(pole, pole[1:]))
    return res

#vraci zda dane pole je roustouci (bud cele a nebo jen pocet poslednich)
def isrising(pole: list, pocet: int = None):
    if pocet is None: pocet = len(pole)
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

def convert_to_numpy(data):
    if isinstance(data, list) or isinstance(data, deque):
        return np.fromiter(data, float)
    elif isinstance(data, pd.Series):
        return data.to_numpy()
    return data


def check_series(data):
    return isinstance(data, pd.Series)