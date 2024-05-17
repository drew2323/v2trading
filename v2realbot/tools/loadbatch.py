import matplotlib
import matplotlib.dates as mdates
#matplotlib.use('Agg')  # Set the Matplotlib backend to 'Agg'
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from datetime import datetime
from typing import List
from enum import Enum
import numpy as np
import v2realbot.controller.services as cs
from rich import print as richprint
from v2realbot.common.model import AnalyzerInputs
from v2realbot.common.PrescribedTradeModel import TradeDirection, TradeStatus, Trade, TradeStoplossType
from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, safe_get#, print
from pathlib import Path
from v2realbot.config import WEB_API_KEY, DATA_DIR, MEDIA_DIRECTORY
from v2realbot.enums.enums import RecordType, StartBarAlign, Mode, Account, OrderSide
from io import BytesIO
from v2realbot.utils.historicals import get_historical_bars
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from collections import defaultdict
from scipy.stats import zscore
from io import BytesIO
from typing import Tuple, Optional, List
from v2realbot.common.PrescribedTradeModel import TradeDirection, TradeStatus, Trade, TradeStoplossType
from collections import Counter
import vectorbtpro as vbt

    # Function to add 23 seconds to the last datetime (if it exists and is the same day)
def adjust_datetime_iteratively(df, resolution):
    adjusted_times = []
    for i, current_time in enumerate(df.index):
        if i == 0:
            # The first entry is unchanged
            adjusted_times.append(current_time)
            continue
        
        previous_time = adjusted_times[-1]
        # Check if it's the same day
        if previous_time.date() == current_time.date():
            # Add resolution to the previous datetime
            adjusted_time = previous_time + pd.Timedelta(seconds=resolution)
        else:
            # Different day, leave it as is
            adjusted_time = current_time
        
        adjusted_times.append(adjusted_time)
    
    # Update DataFrame index
    df.index = pd.DatetimeIndex(adjusted_times)
    return df

def convert_to_dataframe(ohlcv):
    """
    Convert a dictionary containing OHLCV data into a pandas DataFrame.
    
    Parameters:
        ohlcv (dict): Dictionary containing OHLCV data.
                      It should have keys 'time', 'open', 'high', 'low', 'close', 'volume', 'updated'.
                      'time' should be a list of float timestamps.
                      'updated' should be a list of Python datetimes in UTC time zone.
    
    Returns:
        pd.DataFrame: DataFrame containing the OHLCV data with the index converted to East coast US time.
    """

    #pokud existuje key index, tak menime na custom_index, aby nedelal neplechu v pd
    try:
        if ohlcv.get('index', False):
            ohlcv['custom_index'] = ohlcv.pop('index')
    except Exception as e:
        pass

    #keys that should not go uppercase letter first 
    keys_not_to_upper = ["time", "updated"]

    # Update keys not in the exclusion list
    for key in list(ohlcv.keys()):  # Iterate over a copy of the keys
        if key not in keys_not_to_upper:
            ohlcv[key.title()] = ohlcv.pop(key) 

    # Create DataFrame from the dictionary
    df = pd.DataFrame(ohlcv)
    
    # Convert 'time' to datetime and set as index
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    df.set_index('time', inplace=True)
    # Convert index to East coast US time zone
    df.index = df.index.tz_convert('US/Eastern')
    if 'updated' in df.columns:
        df['updated'] = pd.to_datetime(df['updated'], unit='s', utc=True)
        df['updated'] = df['updated'].dt.tz_convert('US/Eastern')
    
    return df

def print(v, *args, **kwargs):
    if v:
        richprint(*args, **kwargs)

def load_batch(runner_ids: List = None, batch_id: str = None, space_resolution_evenly = False, main_session_only = True, merge_ind2bars = True, bars_columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Vwap'], indicators_columns = [], verbose = False) -> Tuple[int, dict]:
    """Load batches (all runners from single batch) into pandas dataframes

    Args:
        runner_ids (List, optional): A list of runner identifiers (e.g., stock tickers). Defaults to None.
        batch_id (str, optional): The ID of a specific batch to retrieve. Defaults to None.
        merge_ind2bars (bool, optional): merge indicator into bars dataframe. Defaults to True.
        bars_columns (list, optional):  List of columns to keep in bars df. Defaults to ['Open', 'High', 'Low', 'Close', 'Volume', 'Vwap'].
        indicators_columns (list, optional): List of columns to keep in indicators df. Defaults to an empty list.
        space_resoution_evenly: If True then, it alters index so it is spaced evenly in given resolution in ['resooution']
    Returns:
        Tuple[int, dict]: A tuple containing:
            * An integer potentially representing a status code or data count.
            * A dictionary with keys bars, indicators and cbar_indicators - with pandas dataframe
    """

    if runner_ids is None and batch_id is None:
        return -2, f"runner_id or batch_id must be present", 0

    if batch_id is not None:
        res, runner_ids =cs.get_archived_runnerslist_byBatchID(batch_id)

        if res != 0:
            print(f"no batch {batch_id} found")
            return -1, f"no batch {batch_id} found", 0

    #DATA PREPARATION
    bars = None
    indicators = None
    cnt = 0
    dfs = dict(bars=[], indicators=[],cbar_indicators=[])
    resolution = None
    for id in runner_ids:
        cnt += 1
        #get runner detail
        res, sada =cs.get_archived_runner_details_byID(id)
        if res != 0:
            print(f"no runner {id} found")
            return -1, f"no runner {id} found", 0
        
        if resolution is None:
            resolution  = sada["bars"]["resolution"][0]
            print(verbose, f"Resolution : {resolution}")

        #add daily bars limited to required columns, we keep updated as its mapping column to indicators
        bars = convert_to_dataframe(sada["bars"])[bars_columns + ["updated"]]
        #bars = bars.loc[:, bars_columns]

        indicators = convert_to_dataframe(sada["indicators"][0])[indicators_columns]

        #join indicators to bars dataframe
        if merge_ind2bars:
            #merge, time v indicators odpovida udpated v bars
            bars = bars.reset_index()
            bars = pd.merge(bars, indicators, left_on="updated", right_on="time", how="left")
            bars = bars.set_index("time")
        else:
            dfs["indicators"].append(indicators)

        #drop updated as mapping column
        #bars = bars.drop("updated", axis=1)
        dfs["bars"].append(bars)

        #indicators = sada["indicators"][0]
        #cbar_indicators = sada["indicators"][1]
    #merge all days into single df
    for key in dfs:
        if len(dfs[key])>0:
            concat_df = pd.concat(dfs[key], axis=0)
            concat_df = concat_df.between_time('9:30', '16:00') if main_session_only else concat_df

            # Count the number of duplicates (excluding the first occurrence)
            num_duplicates = concat_df.index.duplicated().sum()

            if num_duplicates > 0:
                print(verbose, f"NOTE: DUPLICATES {num_duplicates}/{len(concat_df)} in {key}. REMOVING.")
                concat_df = concat_df[~concat_df.index.duplicated()]

                num_duplicates = concat_df.index.duplicated().sum()
                print(verbose, f"Now there are {num_duplicates}/{len(concat_df)}")

            if space_resolution_evenly and key != "cbar_indicators":
                # Apply rounding to the datetime index according to resolution (in seconds)
                concat_df = adjust_datetime_iteratively(concat_df, resolution)

            dfs[key] = concat_df
    return 0, dfs

if __name__ == "__main__":
    res, df = load_batch(batch_id="e44a5075", space_resolution_evenly=True, indicators_columns=["Rsi14"], main_session_only=False)
    if res < 0:
        print("Error" + str(res) + str(df))
    print(df)
    df = df["bars"]
    print(df.info(), df.head())
    #filter columns
    #columns_to_keep = ['Open', 'High', 'Low', 'Close', 'Volume', 'Vwap']
    #df = df.loc[:, columns_to_keep]
    #df = df.rename(columns={'index': 'custom_index'})
    print(df.info(), df.head(), df.describe())
    #filter times
    #df = df.between_time('9:30', '16:00')
    print(df.info())
    # Set the frequency to 23 seconds
    #df.index.freq = pd.tseries.offsets.Second(23)
    # Check the frequency of the index

    # Resample and aggregate the data
    # resampled_df = df.resample('23S').agg({
    #         'open': 'first',
    #         'high': 'max',
    #         'low': 'min',
    #         'close': 'last',
    #         'volume': 'sum'
    #     })

    #df.index.freq = pd.infer_freq(df.index)
    #print(df.index.freq)


    # Set the frequency of the index explicitly - if it exists like 1T etc, if doesnt exists then custom_frequency will be used
    #df.index.freq = pd.date_range(start=df.index[0], periods=len(df), freq='23S')

    print(df.info())

    vbt.settings.set_theme("dark")
    vbt.settings['plotting']['layout']['width'] = 1280
    vbt.settings.plotting.auto_rangebreaks = True

    #naloadujeme do vbt symbol as column
    bar_data = vbt.Data.from_data({"BAC": df}, tz_convert="US/Eastern")
    print(bar_data)
    print(bar_data.close)
    
    print(bar_data.data["BAC"]["Rsi14"])
    bar_data.data["BAC"]["Rsi14"].vbt.plot().show()
    print(bar_data["Rsi14"])
    
    
    #ohlcv plot (sublot 2x1)
    bar_data.data["BAC"].vbt.ohlcv.plot().show()

    #create two subplots 3x1 (ohlcv + RSI)
    # fig = vbt.make_subplots(rows=3, cols=1)
    # bar_data.data["BAC"].vbt.ohlcv.plot(add_trace_kwargs=dict(row=1, col=1),fig=fig)
    # bar_data.data["BAC"]["Rsi14"].vbt.plot(add_trace_kwargs=dict(row=3, col=1),fig=fig)
    # fig.show()

    #create subplots with alternate Y axis - RSI overlay
    fig1 = vbt.make_subplots(specs=[[{"secondary_y": True}]])
    bar_data.data["BAC"]["Close"].vbt.plot(add_trace_kwargs=dict(secondary_y=False),fig=fig1)
    bar_data.data["BAC"].vbt.plot(add_trace_kwargs=dict(secondary_y=True),fig=fig1)
    fig1.show()

    puv_df = bar_data.data["BAC"]

    bar_data23s = bar_data[["Open", "High", "Low", "Close", "Volume"]]
    print(bar_data23s)
    #resample by vbt
    bar_data46s = bar_data23s.get().resample("46s").agg({
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
        "Volume": "sum"
    })

    print(bar_data46s)
    res_data = bar_data46s.data["BAC"]
    #bar_data23s.data["BAC"].ptable()
    #bar_data23s = bar_data.resample("23S")
    print(bar_data46s)
    print(bar_data46s.close)
    vbt.settings.plotting.auto_rangebreaks = True
    bar_data46s.data["BAC"].vbt.ohlcv.plot().show()

    #TARGET DAYS - only one day or range
    # Target Date
    #target_date = pd.to_datetime('2023-10-12', tz='US/Eastern')

    # Date Range
    start_date = pd.to_datetime('2024-03-12')
    #end_date = pd.to_datetime('2023-10-14')

    new_data = bar_data.transform(lambda df: df[df.index.date == start_date.date()])
    #range filtered_data = data[(data.index >= start_date) & (data.index <= end_date)

    print(new_data)
    new_data.data["BAC"].vbt.ohlcv.plot().show()


    # Filtering RANGE or DAY
    # filtered_data = data[(data.index >= start_date) & (data.index <= end_date)]g
    # filtered_data = data[data.index.date == target_date.date()]



    #custom aggregagation
    # ohlcv_agg = pd.DataFrame({
    #     'Open': df.resample('1T')['Open'].first(),
    #     'High': df.resample('1T')['High'].max(),
    #     'Low': df.resample('1T')['Low'].min(),
    #     'Close': df.resample('1T')['Close'].last(),
    #     'Volume': df.resample('1T')['Volume'].sum()
    # })

    #Define a custom frequency with a timedelta of 23 seconds
    # custom_frequency = pd.tseries.offsets.DateOffset(seconds=23)

    # # Create a new DataFrame with the desired frequency
    # new_index = pd.date_range(start=df.index[0], end=df.index[-1], freq=custom_frequency)
    # new_df = pd.DataFrame(index=new_index)

    # # Reindex the DataFrame
    # df = df.reindex(new_df.index)

    # # Now you can check the frequency of the index
    # print(df.index.freq)


