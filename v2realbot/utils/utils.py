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
from v2realbot.common.model import StrategyInstance, Runner, RunArchive, RunArchiveDetail, Intervals, SLHistory, InstantIndicator
from v2realbot.common.PrescribedTradeModel import Trade, TradeDirection, TradeStatus, TradeStoplossType
from typing import List
import tomli
from v2realbot.config import DATA_DIR, ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY
import requests
from uuid import UUID
#from decimal import Decimal
from enum import Enum
#from v2realbot.enums.enums import Order
from v2realbot.common.model import Order as btOrder, TradeUpdate as btTradeUpdate
from alpaca.trading.models import Order, TradeUpdate, Calendar
import numpy as np
import pandas as pd
from collections import deque
import socket
import numpy as np
from alpaca.trading.requests import GetCalendarRequest
from alpaca.trading.client import TradingClient
import time as timepkg
from traceback import format_exc
import re
import tempfile
import shutil
from filelock import FileLock
import v2realbot.utils.config_handler as cfh
import pandas_market_calendars as mcal

def validate_and_format_time(time_string):
    """
    Validates if the given time string is in the format HH:MM or H:MM. 
    If valid, returns the standardized time string in HH:MM format.

    Args:
        time_string (str): The time string to validate.

    Returns:
        str or None: Standardized time string in HH:MM format if valid, 
                     None otherwise.
    """
    # Regular expression for matching the time format H:MM or HH:MM
    time_pattern = re.compile(r'^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$')

    # Checking if the time string matches the pattern
    if time_pattern.match(time_string):
        # Standardize the time format to HH:MM
        standardized_time = datetime.strptime(time_string, '%H:%M').strftime('%H:%M')
        return standardized_time
    else:
        return None

def fetch_calendar_data(start: datetime, end: datetime) -> List[Calendar]:
    """
    Fetches the trading schedule for the NYSE (New York Stock Exchange) between the specified start and end dates.
    Args:
        start (datetime): The start date for the trading schedule.
        end (datetime): The end date for the trading schedule.
    Returns:
        List[Calendar]: A list of Calendar objects containing the trading dates and market open/close times. 
                        Returns an empty list if no trading days are found within the specified range.
    """ 
    nyse = mcal.get_calendar('NYSE')
    schedule = nyse.schedule(start_date=start, end_date=end, tz='America/New_York')
    if not schedule.empty: 
        schedule = (schedule.reset_index()
                        .rename(columns={"index": "date", "market_open": "open", "market_close": "close"})
                        .assign(date=lambda day: day['date'].dt.date.astype(str),
                                open=lambda day: day['open'].dt.strftime('%H:%M'), 
                                close=lambda day: day['close'].dt.strftime('%H:%M'))
                        .to_dict(orient="records"))
        cal_dates = [Calendar(**record) for record in schedule]
        return cal_dates
    else:
        cal_dates=[]
        return cal_dates

#Alpaca Calendar wrapper with retry
def fetch_calendar_data_from_alpaca(start, end, max_retries=5, backoff_factor=1):
    """
    Attempts to fetch calendar data with exponential backoff. Raises an exception if all retries fail.

    TODO sem pridat local caching mechanism

    :param client: Alpaca API client instance.
    :param start: The start date for the calendar data.
    :param end: The end date for the calendar data.
    :param max_retries: Maximum number of retries.
    :param backoff_factor: Factor to determine the next sleep time.
    :return: Calendar data.
    :raises: ConnectionError if all retries fail.
    """
    # Ensure start and end are of type datetime.date
    if isinstance(start, datetime):
        start = start.date()
    if isinstance(end, datetime):
        end = end.date()

    # Verify that start and end are datetime.date objects after conversion
    if not all([isinstance(start, date), isinstance(end, date)]):
        raise ValueError("start and end must be datetime.date objects")
    
    clientTrading = TradingClient(ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY, raw_data=False)
    calendar_request = GetCalendarRequest(start=start, end=end)
    last_exception = None

    for attempt in range(max_retries):
        try:
            cal_dates = clientTrading.get_calendar(calendar_request)
            richprint("Calendar data fetch successful", start, end)
            return cal_dates
        except Exception as e:
            richprint(f"Attempt {attempt + 1} failed: {e}")
            last_exception = e
            timepkg.sleep(backoff_factor * (2 ** attempt))

    richprint("****All attempts to fetch calendar data failed.****")
    send_to_telegram(f"FETCH_CALENDER_DATA_FAILED. {str(last_exception)} and {format_exc()} BACKEST STOPPED" )
    raise ConnectionError(f"Failed to fetch calendar data after {max_retries} retries. Last exception: {str(last_exception)} and {format_exc()}")

def concatenate_weekdays(weekday_filter):
    # Mapping of weekdays where 0 is Monday and 6 is Sunday
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    # Convert the integers in weekday_filter to their corresponding weekday strings
    weekday_strings = [weekdays[day] for day in weekday_filter]

    # Concatenate the weekday strings
    return ','.join(weekday_strings)

def filter_timeseries_by_timestamp(timeseries, timestamp):
    """
    Filter a timeseries dictionary, returning a new dictionary with entries
    where the time value is greater than the provided timestamp.

    Parameters:
    - timeseries (dict): The original timeseries dictionary.
    - timestamp (float): The timestamp to filter the timeseries by.

    Returns:
    - dict: A new timeseries dictionary filtered based on the provided timestamp.
    """
    # Find indices where time values are greater than the provided timestamp
    indices = [i for i, time in enumerate(timeseries['time']) if time > timestamp]

    # Create a new dictionary with values filtered by the indices
    filtered_timeseries = {key: [value[i] for i in indices] for key, value in timeseries.items()}

    return filtered_timeseries

def slice_dict_lists(d, last_item, to_tmstp = False, time_to_datetime = False):
  """Slices every list in the dictionary to the last last_item items.
  
  Args:
    d: A dictionary.
    last_item: The number of items to keep at the end of each list.
    to_tmstp: For "time" elements change it from datetime to timestamp from datetime if required.
    time_to_datetime: For "time" elements change it from timestamp to datetime UTC if required.
  Returns:
    A new dictionary with the sliced lists.

    datetime.fromtimestamp(data['updated']).astimezone(zoneUTC)
  """
  sliced_d = {}
  for key in d.keys():
    if key == "time" and to_tmstp:
        sliced_d[key] = [datetime.timestamp(t) for t in d[key][-last_item:]]
    elif key == "time" and time_to_datetime:
        sliced_d[key] = [datetime.fromtimestamp(t).astimezone(zoneUTC) for t in d[key][-last_item:]]
    else:
        sliced_d[key] = d[key][-last_item:]
  return sliced_d


#   keys_set = set(keys)
#   sliced_d = {}
#   for key, value in d.items():
#     if key in keys_set and isinstance(value, list):
#       if key == "time" and to_tmstp:
#         sliced_d[key] = [datetime.timestamp(t) for t in value[-last_item:]]
#       else:      
#         sliced_d[key] = value[-last_item:]
#   return sliced_d

#WIP
def create_new_bars(bars, new_resolution):
  """WIP - Creates new bars dictionary in the new resolution.

  Args:
    bars: A dictionary representing ohlcv bars.
    new_resolution: A new resolution in seconds.

  Returns:
    A dictionary representing ohlcv bars in the new resolution.
  """

  # Check that the new resolution is a multiple of the old resolution.
  if new_resolution % bars['resolution'][0] != 0:
    raise ValueError('New resolution must be a multiple of the old resolution.')

  # Calculate the number of bars in the new resolution.
  new_bar_count = int(len(bars['time']) / (new_resolution / bars['resolution'][0]))

  # Create a new dictionary to store the new bars.
  new_bars = {'high': np.empty(new_bar_count),
                'low': np.empty(new_bar_count),
                'volume': np.empty(new_bar_count),
                'close': np.empty(new_bar_count),
                'open': np.empty(new_bar_count),
                'time': np.empty(new_bar_count),
                'resolution': [new_resolution]}

  # Calculate the start and end time of each new bar.
  new_bar_start_times = np.arange(0, new_bar_count) * new_resolution
  new_bar_end_times = new_bar_start_times + new_resolution

  # Find all the old bars that are within each new bar.
  old_bar_indices_in_new_bars = np.searchsorted(bars['time'], new_bar_start_times, side='right') - 1

  # Calculate the high, low, volume, and close of each new bar.
  new_bar_highs = np.amax(bars['high'][old_bar_indices_in_new_bars:], axis=1)
  new_bar_lows = np.amin(bars['low'][old_bar_indices_in_new_bars:], axis=1)
  new_bar_volumes = np.sum(bars['volume'][old_bar_indices_in_new_bars:], axis=1)
  new_bar_closes = bars['close'][old_bar_indices_in_new_bars[:,-1]]

  # Add the new bars to the new dictionary.
  new_bars['high'] = new_bar_highs
  new_bars['low'] = new_bar_lows
  new_bars['volume'] = new_bar_volumes
  new_bars['close'] = new_bar_closes
  new_bars['open'] = new_bar_closes[:-1]
  new_bars['time'] = new_bar_start_times

  return new_bars

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
        if isrisingc(left_leg) and isfallingc(right_leg):
            return True
        else:
            return False
    elif type == "V":
        if isfallingc(left_leg) and isrisingc(right_leg):
            return True
        else:
            return False
    else:
        print("Unknown type")
        return False
    
#upravene a rozsirene o potencialne vetsi confrm body
#puvodni verze odpovida confirm_points = 1
#https://chat.openai.com/c/0e614d96-6af4-40db-a6ec-a8c57ce481b8
# def crossed_up(threshold, list, confirm_points=2):
#     """
#     Check if the threshold has crossed up in the last few values in price_list.
#     A crossover is confirmed if the threshold is below the earlier prices and then crosses above in the later prices.
#     The number of confirmation points can be specified; the default is 2.
#     """
#     try:
#         if len(list) < confirm_points * 2:
#             # Not enough data to confirm crossover
#             return False

#         # Split the list into two parts for comparison
#         earlier_prices = list[-confirm_points*2:-confirm_points]
#         later_prices = list[-confirm_points:]

#         # Check if threshold was below earlier prices and then crossed above
#         was_below = all(threshold < price for price in earlier_prices)
#         now_above = all(threshold >= price for price in later_prices)

#         return was_below and now_above

#     except IndexError:
#         # In case of an IndexError, return False
#         return False

#recent cross up of two arrays (price1 crossed up price2), fallback to standard
#inputs are numpy arrays
# def crossed_up_numpy(price1, price2):
#     if price1.size < 2 or price2.size < 2:
#         return False  # Not enough data

#     # Calculate slopes for the last two points
#     x = np.array([price1.size - 2, price1.size - 1])
#     slope1, intercept1 = np.polyfit(x, price1[-2:], 1)
#     slope2, intercept2 = np.polyfit(x, price2[-2:], 1)

#     # Check if lines are almost parallel
#     if np.isclose(slope1, slope2):
#         return False

#     # Calculate intersection point
#     x_intersect = (intercept2 - intercept1) / (slope1 - slope2)
#     y_intersect = slope1 * x_intersect + intercept1

#     # Check if the intersection occurred between the last two points
#     if x[0] < x_intersect <= x[1]:
#         # Check if line1 crossed up line2
#         return price1[-1] > price2[-1] and price1[-2] <= price2[-2]
    
#     return False

#same but more efficient approach
def crossed_up_numpy(price1, price2):
    if price1.size < 2 or price2.size < 2:
        return False  # Not enough data

    # Indices for the last two points
    x1, x2 = price1.size - 2, price1.size - 1

    # Direct calculation of slopes and intercepts
    slope1 = (price1[-1] - price1[-2]) / (x2 - x1)
    intercept1 = price1[-1] - slope1 * x2
    slope2 = (price2[-1] - price2[-2]) / (x2 - x1)
    intercept2 = price2[-1] - slope2 * x2

    # Check if lines are almost parallel
    if np.isclose(slope1, slope2):
        return False

    # Calculate intersection point (x-coordinate only)
    if slope1 != slope2:  # Avoid division by zero
        x_intersect = (intercept2 - intercept1) / (slope1 - slope2)

        # Check if the intersection occurred between the last two points
        if x1 < x_intersect <= x2:
            # Check if line1 crossed up line2
            return price1[-1] > price2[-1] and price1[-2] <= price2[-2]
    
    return False


#recent cross up of two arrays (price1 crossed up price2), fallback to standard
#inputs are numpy arrays
# def crossed_down_numpy(price1, price2):
#     if price1.size < 2 or price2.size < 2:
#         return False  # Not enough data

#     # Calculate slopes for the last two points
#     x = np.array([price1.size - 2, price1.size - 1])
#     slope1, intercept1 = np.polyfit(x, price1[-2:], 1)
#     slope2, intercept2 = np.polyfit(x, price2[-2:], 1)

#     # Check if lines are almost parallel
#     if np.isclose(slope1, slope2):
#         return False

#     # Calculate intersection point
#     x_intersect = (intercept2 - intercept1) / (slope1 - slope2)
#     y_intersect = slope1 * x_intersect + intercept1

#     # Check if the intersection occurred between the last two points
#     if x[0] < x_intersect <= x[1]:
#         # Check if line1 crossed down line2
#         return price1[-1] < price2[-1] and price1[-2] >= price2[-2]
    
#     return False

#more efficient yet same, price1 - faster, price2 - slower
def crossed_down_numpy(price1, price2):
    if price1.size < 2 or price2.size < 2:
        return False  # Not enough data

    # Indices for the last two points
    x1, x2 = price1.size - 2, price1.size - 1

    # Direct calculation of slopes and intercepts
    slope1 = (price1[-1] - price1[-2]) / (x2 - x1)
    intercept1 = price1[-1] - slope1 * x2
    slope2 = (price2[-1] - price2[-2]) / (x2 - x1)
    intercept2 = price2[-1] - slope2 * x2

    # Check if lines are almost parallel
    if np.isclose(slope1, slope2):
        return False

    # Calculate intersection point (x-coordinate only)
    if slope1 != slope2:  # Avoid division by zero
        x_intersect = (intercept2 - intercept1) / (slope1 - slope2)

        # Check if the intersection occurred between the last two points
        if x1 < x_intersect <= x2:
            # Check if line1 crossed down line2
            return price1[-1] < price2[-1] and price1[-2] >= price2[-2]
    
    return False

#obalka pro crossup listu a thresholdu nebo listu a druheho listu
#value  - svcalar or list, primary_line - usually faster
def crossed_up(value, primary_line):
    if isinstance(value, list):
        return crossed_up_numpy(np.array(primary_line), np.array(value))
    else:
        return crossed_up_threshold(threshold=value, list=primary_line)    

#obalka pro crossdown listu a thresholdu nebo listu a druheho listu
#value  - svcalar or list, primary_line - usually faster
def crossed_down(value, primary_line):
    if isinstance(value, list):
        return crossed_down_numpy(np.array(primary_line), np.array(value))
    else:
        return crossed_down_threshold(threshold=value, list=primary_line)    

def crossed_up_threshold(threshold, list):
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
    
def crossed_down_threshold(threshold, list):
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
    if price<cfh.config_handler.get_val('NORMALIZED_TICK_BASE_PRICE'):
        return normalized_ticks
    else:
        #ratio of price vs base price
        ratio = price/cfh.config_handler.get_val('NORMALIZED_TICK_BASE_PRICE')
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

#OPTIMIZED by CHATGPT
def safe_get(collection, key, default=None):
    """Get values from a collection without raising errors"""
    # Check if the collection supports the .get method (like dict)
    if hasattr(collection, 'get'):
        return collection.get(key, default)

    # Check if the key is within the bounds for list-like collections
    if isinstance(collection, (list, tuple)) and 0 <= key < len(collection):
        return collection[key]

    return default

# def safe_get(collection, key, default=None):
#     """Get values from a collection without raising errors"""

#     try:
#         return collection.get(key, default)
#     except TypeError:
#         pass

#     try:
#         return collection[key]
#     except (IndexError, TypeError):
#         pass

#     return default

def send_to_telegram(message):
    apiToken = '5836666362:AAGPuzwp03tczMQTwTBiHW6VsZZ-1RCMAEE'
    chatID = '5029424778'
    apiURL = f'https://api.telegram.org/bot{apiToken}/sendMessage'

    message = socket.gethostname() + " " + message
    try:
        response = requests.post(apiURL, json={'chat_id': chatID, 'text': message})
        print(response.text)
    except Exception as e:
        print(e)

def transform_data(data, transform_function):
    """
    Recursively transform the data in a dictionary, list of dictionaries, or nested dictionaries 
    using a specified transformation function.

    This function applies the transformation function to each value in the data structure. 
    It handles nested dictionaries and lists of dictionaries.

    Parameters:
    data (dict or list): The dictionary, list of dictionaries, or nested dictionary to be transformed.
    transform_function (function): The function to be applied to each value in the data. This function 
                                   should accept a single value and return a transformed value.

    Returns:
    dict or list: The transformed dictionary, list of dictionaries, or nested dictionary with each value 
                  processed by the transform_function.

    Raises:
    TypeError: If the transform_function cannot process a value, the original value is kept.
    """
    if isinstance(data, dict):
        return {key: transform_data(value, transform_function) for key, value in data.items()}
    elif isinstance(data, list):
        return [transform_data(element, transform_function) for element in data]
    else:
        try:
            return transform_function(data)
        except TypeError:
            return data

#OPTIMIZED BY BARD
def json_serial(obj):
    """JSON serializer for objects not serializable by default json code
    https://stackoverflow.com/questions/11875770/how-to-overcome-datetime-datetime-not-json-serializable
    """

    type_map = {
        pd.Timestamp: lambda obj: obj.timestamp(),
        datetime: lambda obj: obj.timestamp(),
        UUID: lambda obj: str(obj),
        Enum: lambda obj: str(obj),
        np.int32: lambda obj: int(obj),
        np.int64: lambda obj: int(obj),
        np.float64: lambda obj: float(obj),
        Order: lambda obj: obj.__dict__,
        TradeUpdate: lambda obj: obj.__dict__,
        btOrder: lambda obj: obj.__dict__,
        btTradeUpdate: lambda obj: obj.__dict__,
        RunArchive: lambda obj: obj.__dict__,
        Trade: lambda obj: obj.__dict__,
        RunArchiveDetail: lambda obj: obj.__dict__,
        Intervals: lambda obj: obj.__dict__,
        SLHistory: lambda obj: obj.__dict__,
        InstantIndicator: lambda obj: obj.__dict__,
        StrategyInstance: lambda obj: obj.__dict__,
    }

    serializer = type_map.get(type(obj))
    if serializer is not None:
        return serializer(obj)
    
    raise TypeError(str(obj) + "Type %s not serializable" % type(obj))


#datetime to timestamp
def json_serial_old(obj):
    """JSON serializer for objects not serializable by default json code
    https://stackoverflow.com/questions/11875770/how-to-overcome-datetime-datetime-not-json-serializable
    """

    if isinstance(obj, (datetime, date)):
        return obj.timestamp()
    if isinstance(obj, UUID) or isinstance(obj, Enum) or isinstance(obj, np.int64):
        return str(obj)
    if type(obj) in [Order, TradeUpdate, btOrder, btTradeUpdate, RunArchive, Trade, RunArchiveDetail, Intervals, SLHistory, InstantIndicator]:
        return obj.__dict__
    
    raise TypeError (str(obj)+"Type %s not serializable" % type(obj))

def parse_toml_string(tomlst: str):
    try:
        tomlst = tomli.loads(tomlst)
    except tomli.TOMLDecodeError as e:
        msg = f"Not valid TOML: " + str(e)
        richprint(msg)
        return (-1, msg)
    return (0, dict_replace_value(tomlst,"None",None))

#class to persist

# A FileLock is used to prevent concurrent access to the cache file.
# The __init__ method reads the existing cache file within the lock to ensure it's not being written to simultaneously by another process.
# The save method writes to a temporary file first and then atomically moves it to the desired file location. This prevents the issue of partial file writes in case the process is interrupted during the write.
#Zatim temporary fix, aby nezapisoval jiny process
#predtim nez bude implementovano ukladani do db
#pro ostatni processy je dostupne rest api get stratin
class Store:
    stratins: List[StrategyInstance] = []
    runners: List[Runner] = []
    
    def __init__(self) -> None:
        self.lock = FileLock(DATA_DIR + "/strategyinstances.lock")
        self.db_file = DATA_DIR + "/strategyinstances.cache"
        if os.path.exists(self.db_file):
            with self.lock, open(self.db_file, 'rb') as fp:
                self.stratins = pickle.load(fp)

    def save(self):
        with self.lock:
            temp_fd, temp_path = tempfile.mkstemp(dir=DATA_DIR)
            with os.fdopen(temp_fd, 'wb') as temp_file:
                pickle.dump(self.stratins, temp_file)
            shutil.move(temp_path, self.db_file)

qu = Queue()

#zoneNY = tz.gettz('America/New_York')
zoneNY = pytz.timezone('US/Eastern')
zoneUTC = pytz.utc
zonePRG = pytz.timezone('Europe/Amsterdam')

def print(*args, **kwargs):
    if cfh.config_handler.get_val('QUIET_MODE'):
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


#TODO v budoucnu predelat - v initu nacist jednou market open cas a ten pouzivat vsude
#kde je treba (ted je tady natvrdo 9.30)
def minutes_since_market_open(datetime_aware: datetime):
    """
    Calculate the number of minutes elapsed from 9:30 AM to the given timezone-aware datetime of the same day.
    This version is optimized for speed and should be used when calling in a loop.

    :param datetime_aware: A timezone-aware datetime object representing the time to compare.
    :return: The number of minutes since today's 9:30 AM.
    """
    # Ensure the input datetime is timezone-aware
    if datetime_aware.tzinfo is None or datetime_aware.tzinfo.utcoffset(datetime_aware) is None:
        raise ValueError("The input datetime must be timezone-aware.")

    # Calculate minutes since midnight for both times
    minutes_since_midnight = datetime_aware.hour * 60 + datetime_aware.minute
    morning_minutes = 9 * 60 + 30

    # Calculate the difference
    delta_minutes = minutes_since_midnight - morning_minutes

    return delta_minutes if delta_minutes >= 0 else 0

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

#vraci zda dane pole je klesajici (bud cele a nebo jen pocet poslednich) - no same values
def isfallingc(pole: list, pocet: int = None):
    if pocet is None: pocet = len(pole)
    if len(pole)<pocet: return False
    pole = pole[-pocet:]
    res = all(i > j for i, j in zip(pole, pole[1:]))
    return res

#optimized by gpt and same values are considered as one
def isfalling(pole: list, pocet: int = None):
    if pocet is None:
        pocet = len(pole)
    if len(pole) < pocet:
        return False

    # Prepare the list - all same consecutive values in the list are considered as one value.
    new_pole = [pole[0]]
    for i in range(1, len(pole)):
        if pole[i] != pole[i - 1]:
            new_pole.append(pole[i])

    if len(new_pole) < pocet:
        return False
    
    new_pole = new_pole[-pocet:]
    #print(new_pole)


    # Perform the current calculation on this list.
    res = all(i > j for i, j in zip(new_pole, new_pole[1:]))
    return res

#vraci zda dane pole je roustouci (bud cele a nebo jen pocet poslednich) - no same values
def isrisingc(pole: list, pocet: int = None):
    if pocet is None: pocet = len(pole)
    if len(pole)<pocet: return False
    pole = pole[-pocet:]
    res = all(i < j for i, j in zip(pole, pole[1:]))
    return res

#optimized by gpt and same values are considered as one
def isrising(pole: list, pocet: int = None):
    if pocet is None:
        pocet = len(pole)
    if len(pole) < pocet:
        return False

    # Prepare the list - all same consecutive values in the list are considered as one value.
    new_pole = [pole[0]]
    for i in range(1, len(pole)):
        if pole[i] != pole[i - 1]:
            new_pole.append(pole[i])

    if len(new_pole) < pocet:
        return False
    
    new_pole = new_pole[-pocet:]
    #print(new_pole)

    # Perform the current calculation on this list.
    res = all(i < j for i, j in zip(new_pole, new_pole[1:]))
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