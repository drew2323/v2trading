import tulipy as ti
import numpy as np
import pandas as pd
from collections import deque
import typing
from v2realbot.utils.utils import check_series, convert_to_numpy

def roc(data, lookback: int = 5, use_series=False):
    """
    The Rate of Change indicator calculates the change between the current price and the price n bars ago.
    Args:
        data: (list) A list containing the data you want to find the moving average of
        period: (int) lookback N - bars ago
    """
    data = convert_to_numpy(data)
    roc = ti.roc(data, period=lookback)
    return roc

def natr(data_high, data_low, data_close, period: int = 5):
    data_high = convert_to_numpy(data_high)
    data_low = convert_to_numpy(data_low)
    data_close = convert_to_numpy(data_close)
    natr = ti.natr(data_high, data_low, data_close, period=period)
    return natr

def atr(data_high, data_low, data_close, period: int = 5):
    data_high = convert_to_numpy(data_high)
    data_low = convert_to_numpy(data_low)
    data_close = convert_to_numpy(data_close)
    atr = ti.atr(data_high, data_low, data_close, period=period)
    return atr

def ema(data, period: int = 50, use_series=False):
    if check_series(data):
        use_series = True
    data = convert_to_numpy(data)
    ema = ti.ema(data, period=period)
    return pd.Series(ema) if use_series else ema

def sma(data, period: int = 50, use_series=False):
    """
    Finding the moving average of a dataset
    Args:
        data: (list) A list containing the data you want to find the moving average of
        period: (int) How far each average set should be
    """
    if check_series(data):
        use_series = True
    data = convert_to_numpy(data)
    sma = ti.sma(data, period=period)
    return pd.Series(sma) if use_series else sma
