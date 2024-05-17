import pandas as pd
import numpy as np
from numba import jit
from alpaca.data.historical import StockHistoricalDataClient
from sqlalchemy import column
from v2realbot.config import ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY, DATA_DIR
from alpaca.data.requests import StockTradesRequest
import time as time_module
from v2realbot.utils.utils import parse_alpaca_timestamp, ltp, zoneNY, send_to_telegram, fetch_calendar_data
import pyarrow
from traceback import format_exc
from datetime import timedelta, datetime, time
from concurrent.futures import ThreadPoolExecutor
import os
import gzip
import pickle
import random
from alpaca.data.models import BarSet, QuoteSet, TradeSet
import v2realbot.utils.config_handler as cfh
from v2realbot.enums.enums import BarType
""""
Module used for vectorized aggregation of trades.

Includes fetch (remote/cached) methods and numba aggregator function for TIME BASED, VOLUME BASED and DOLLAR BARS

"""""

def aggregate_trades(symbol: str, trades_df: pd.DataFrame, resolution: int, type: BarType = BarType.TIME):
    """"
    Accepts dataframe with trades keyed by symbol. Preparess dataframe to 
    numpy and call nNumba optimized aggregator for given bar type. (time/volume/dollar)
    """""
    trades_df = trades_df.loc[symbol]
    trades_df= trades_df.reset_index()
    ticks = trades_df[['timestamp', 'price', 'size']].to_numpy()
    # Extract the timestamps column (assuming it's the first column)
    timestamps = ticks[:, 0]
    # Convert the timestamps to Unix timestamps in seconds with microsecond precision
    unix_timestamps_s = np.array([ts.timestamp() for ts in timestamps], dtype='float64')
    # Replace the original timestamps in the NumPy array with the converted Unix timestamps
    ticks[:, 0] = unix_timestamps_s
    ticks = ticks.astype(np.float64)
    #based on type, specific aggregator function is called
    match type:
        case BarType.TIME:
            ohlcv_bars = generate_time_bars_nb(ticks, resolution)
        case BarType.VOLUME:
            ohlcv_bars = generate_volume_bars_nb(ticks, resolution)
        case BarType.DOLLAR:
            ohlcv_bars = generate_dollar_bars_nb(ticks, resolution)
        case _:
            raise ValueError("Invalid bar type. Supported types are 'time', 'volume' and 'dollar'.")
    # Convert the resulting array back to a DataFrame
    columns = ['time', 'open', 'high', 'low', 'close', 'volume', 'trades']
    if type == BarType.DOLLAR:
        columns.append('amount')
    ohlcv_df = pd.DataFrame(ohlcv_bars, columns=columns)
    ohlcv_df['time'] = pd.to_datetime(ohlcv_df['time'], unit='s')
    ohlcv_df.set_index('time', inplace=True)
    ohlcv_df.index = ohlcv_df.index.tz_localize('UTC').tz_convert(zoneNY)
    return ohlcv_df

def convert_dict_to_multiindex_df(tradesResponse):
    """"
    Converts dictionary from cache or from remote (raw input) to multiindex dataframe.
    """""
    # Create a DataFrame for each key and add the key as part of the MultiIndex
    dfs = []
    for key, values in tradesResponse.items():
        df = pd.DataFrame(values)
        # Rename columns
        # Select and order columns explicitly
        #print(df)
        df = df[['t', 'x', 'p', 's', 'i', 'c','z']]
        df.rename(columns={'t': 'timestamp', 'c': 'conditions', 'p': 'price', 's': 'size', 'x': 'exchange', 'z':'tape', 'i':'id'}, inplace=True)
        df['symbol'] = key  # Add ticker as a column
        df['timestamp'] = pd.to_datetime(df['timestamp'])  # Convert 't' from string to datetime before setting it as an index
        df.set_index(['symbol', 'timestamp'], inplace=True)  # Set the multi-level index using both 'ticker' and 't'
        df = df.tz_convert(zoneNY, level='timestamp')
        dfs.append(df)

    # Concatenate all DataFrames into a single DataFrame with MultiIndex
    final_df = pd.concat(dfs)

    return final_df

def dict_to_df(tradesResponse, start, end, exclude_conditions = None, minsize = None):
    """"
    Transforms dict to Tradeset, then df and to zone aware
    Also filters to start and end if necessary (ex. 9:30 to 15:40 is required only)
   
   NOTE: prepodkladame, ze tradesResponse je dict from Raw data (cached/remote)
   """""

    df = convert_dict_to_multiindex_df(tradesResponse)

    #REQUIRED FILTERING
    #pokud je zacatek pozdeji nebo konec driv tak orizneme
    if (start.time() > time(9, 30) or end.time() < time(16, 0)):
        print(f"filtrujeme {start.time()} {end.time()}")
        # Define the time range
        # start_time = pd.Timestamp(start.time(), tz=zoneNY).time()
        # end_time = pd.Timestamp(end.time(), tz=zoneNY).time()

        # Create a mask to filter rows within the specified time range
        mask = (df.index.get_level_values('timestamp') >= start) & \
            (df.index.get_level_values('timestamp') <= end)

        # Apply the mask to the DataFrame
        df = df[mask]

    if exclude_conditions is not None:
        print(f"excluding conditions {exclude_conditions}")
        # Create a mask to exclude rows with any of the specified conditions
        mask = df['conditions'].apply(lambda x: any(cond in exclude_conditions for cond in x))

        # Filter out the rows with specified conditions
        df = df[~mask]

    if minsize is not None:
        print(f"minsize {minsize}")
        #exclude conditions
        df = df[df['size'] >= minsize]
    return df

#fetches daily stock tradess - currently only main session is supported
def fetch_daily_stock_trades_old(symbol, start, end, exclude_conditions = None, minsize = None, force_remote = False, max_retries=5, backoff_factor=1):
    """
    Attempts to fetch stock trades with exponential backoff. Raises an exception if all retries fail.

    :param symbol: The stock symbol to fetch trades for.
    :param start: The start time for the trade data.
    :param end: The end time for the trade data.
    :param max_retries: Maximum number of retries.
    :param backoff_factor: Factor to determine the next sleep time.
    :return: TradesResponse object.
    :raises: ConnectionError if all retries fail.

    We use tradecache only for main sessison request = 9:30 to 16:00
    """
    use_daily_tradecache = False
    if (start.time() >= time(9, 30) and end.time() <= time(16, 0)):
        use_daily_tradecache = True
        filename_start = zoneNY.localize(datetime.combine(start.date(), time(9, 30)))
        filename_end= zoneNY.localize(datetime.combine(end.date(), time(16, 0)))
        daily_file = "TS" + str(symbol) + '-' + str(int(filename_start.timestamp())) + '-' + str(int(filename_end.timestamp())) + '.cache.gz'
        file_path = DATA_DIR + "/tradecache/"+daily_file

    if use_daily_tradecache and not force_remote and os.path.exists(file_path):
        print("Searching cache: " + daily_file)
        with gzip.open (file_path, 'rb') as fp:
            tradesResponse = pickle.load(fp)
            print("FOUND in CACHE", daily_file)
            #response je vzdy ulozena jako raw(dict), davame zpet do TradeSetu, ktery umi i df
            return dict_to_df(tradesResponse, start, end, exclude_conditions, minsize)

    #daily file doesnt exist
    else:
        print("NOT FOUND. Fetching from remote")
        client =  StockHistoricalDataClient(ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY, raw_data=False)
        stockTradeRequest = StockTradesRequest(symbol_or_symbols=symbol, start=start, end=end)
        last_exception = None

        for attempt in range(max_retries):
            try:
                tradesResponse = client.get_stock_trades(stockTradeRequest)
                is_empty = not tradesResponse[symbol]
                print(f"Remote fetched: {is_empty=}", start, end)
                #pokud jde o dnešní den a nebyl konec trhu tak cache neukládáme, pripadne pri iex datapointu necachujeme
                if use_daily_tradecache and not is_empty:
                    if (start < datetime.now().astimezone(zoneNY) < end):
                        print("not saving trade cache, market still open today")
                    else:
                        with gzip.open(file_path, 'wb') as fp:
                            pickle.dump(tradesResponse, fp)
                            print("Saving to Trade CACHE", file_path)
                return pd.DataFrame() if is_empty else dict_to_df(tradesResponse, start, end) 
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                last_exception = e
                time_module.sleep(backoff_factor * (2 ** attempt))

        print("All attempts to fetch data failed.")
        raise ConnectionError(f"Failed to fetch stock trades after {max_retries} retries. Last exception: {str(last_exception)} and {format_exc()}")

def fetch_daily_stock_trades(symbol, start, end, exclude_conditions=None, minsize=None, force_remote=False, max_retries=5, backoff_factor=1):
    #doc for this function
    """
    Attempts to fetch stock trades either from cache or remote. When remote, it uses retry mechanism with exponential backoff.
    Also it stores the data to cache if it is not already there.
    by using force_remote - forcess using remote data always and thus refreshing cache for these dates
        Attributes:
        :param symbol: The stock symbol to fetch trades for.
        :param start: The start time for the trade data.
        :param end: The end time for the trade data.
        :exclude_conditions: list of string conditions to exclude from the data
        :minsize minimum size of trade to be included in the data
        :force_remote will always use remote data and refresh cache
        :param max_retries: Maximum number of retries.
        :param backoff_factor: Factor to determine the next sleep time.
        :return: TradesResponse object.
        :raises: ConnectionError if all retries fail.
    
    We use tradecache only for main sessison requests = 9:30 to 16:00
    Do budoucna ukládat celý den BAC-20240203.cache.gz a z toho si pak filtrovat bud main sesssionu a extended
    Ale zatim je uloženo jen main session v BAC-timestampopenu-timestampclose.cache.gz
    """
    # Determine if the requested times fall within the main session
    in_main_session = (time(9, 30) <= start.time() < time(16, 0)) and (time(9, 30) <= end.time() <= time(16, 0))
    file_path = ''
    
    if in_main_session:
        filename_start = zoneNY.localize(datetime.combine(start.date(), time(9, 30)))
        filename_end = zoneNY.localize(datetime.combine(end.date(), time(16, 0)))
        daily_file = f"{symbol}-{int(filename_start.timestamp())}-{int(filename_end.timestamp())}.cache.gz"
        file_path = f"{DATA_DIR}/tradecache/{daily_file}"
        if not force_remote and os.path.exists(file_path):
            print("Searching cache: " + daily_file)
            with gzip.open(file_path, 'rb') as fp:
                tradesResponse = pickle.load(fp)
                print("FOUND in CACHE", daily_file)
                return dict_to_df(tradesResponse, start, end, exclude_conditions, minsize)

    print("NOT FOUND. Fetching from remote")
    client = StockHistoricalDataClient(ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY, raw_data=True)
    stockTradeRequest = StockTradesRequest(symbol_or_symbols=symbol, start=start, end=end)
    last_exception = None

    for attempt in range(max_retries):
        try:
            tradesResponse = client.get_stock_trades(stockTradeRequest)
            is_empty = not tradesResponse[symbol]
            print(f"Remote fetched: {is_empty=}", start, end)
            if in_main_session and not is_empty:
                current_time = datetime.now().astimezone(zoneNY)
                if not (start < current_time < end):
                    with gzip.open(file_path, 'wb') as fp:
                        pickle.dump(tradesResponse, fp)
                        print("Saving to Trade CACHE", file_path)

                else:  # Don't save the cache if the market is still open
                    print("Not saving trade cache, market still open today")
            return pd.DataFrame() if is_empty else dict_to_df(tradesResponse, start, end) 
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            last_exception = e
            time_module.sleep(backoff_factor * (2 ** attempt) + random.uniform(0, 1))  # Adding random jitter

    print("All attempts to fetch data failed.")
    raise ConnectionError(f"Failed to fetch stock trades after {max_retries} retries. Last exception: {str(last_exception)} and {format_exc()}")


def fetch_trades_parallel(symbol, start_date, end_date, exclude_conditions = cfh.config_handler.get_val('AGG_EXCLUDED_TRADES'), minsize = 100, force_remote = False):
    """
    Fetches trades for each day between start_date and end_date during market hours (9:30-16:00) in parallel and concatenates them into a single DataFrame.

    :param symbol: Stock symbol.
    :param start_date: Start date as datetime.
    :param end_date: End date as datetime.
    :return: DataFrame containing all trades from start_date to end_date.
    """
    futures = []
    results = []
    
    market_open_days = fetch_calendar_data(start_date, end_date)
    day_count = len(market_open_days)
    print("Contains", day_count, " market days")
    max_workers = min(10, max(5, day_count // 2))  # Heuristic: half the days to process, but at least 1 and no more than 10


    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        #for single_date in (start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)):
        for market_day in market_open_days:
            #start = datetime.combine(single_date, time(9, 30))  # Market opens at 9:30 AM
            #end = datetime.combine(single_date, time(16, 0))   # Market closes at 4:00 PM
            
            interval_from = zoneNY.localize(market_day.open)
            interval_to = zoneNY.localize(market_day.close)

            #pripadne orizneme pokud je pozadovane pozdejsi zacatek a drivejsi konek
            start = start_date if interval_from < start_date else interval_from
            #start = max(start_date, interval_from)
            end = end_date if interval_to > end_date else interval_to
            #end = min(end_date, interval_to)

            future = executor.submit(fetch_daily_stock_trades, symbol, start, end, exclude_conditions, minsize, force_remote)
            futures.append(future)
        
        for future in futures:
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Error fetching data for a day: {e}")

    return pd.concat(results, ignore_index=False)

@jit(nopython=True)
def generate_dollar_bars_nb(ticks, amount_per_bar):
    """"
    Generates Dollar based bars from ticks.

    There is also simple prevention of aggregation from different days
    as described here https://chatgpt.com/c/17804fc1-a7bc-495d-8686-b8392f3640a2
    Downside: split days by UTC (which is ok for main session, but when extended hours it should be reworked by preprocessing new column identifying session)
    
    
    When trade is split into multiple bars it is counted as trade in each of the bars.
    Other option: trade count can be proportionally distributed by weight (0.2 to 1st bar, 0.8 to 2nd bar) - but this is not implemented yet
    https://chatgpt.com/c/ff4802d9-22a2-4b72-8ab7-97a91e7a515f
    """""
    ohlcv_bars = []
    remaining_amount = amount_per_bar

    # Initialize bar values based on the first tick to avoid uninitialized values
    open_price = ticks[0, 1]
    high_price = ticks[0, 1]
    low_price = ticks[0, 1]
    close_price = ticks[0, 1]
    volume = 0
    trades_count = 0
    current_day = np.floor(ticks[0, 0] / 86400)  # Calculate the initial day from the first tick timestamp
    bar_time = ticks[0, 0]  # Initialize bar time with the time of the first tick

    for tick in ticks:
        tick_time = tick[0]
        price = tick[1]
        tick_volume = tick[2]
        tick_amount = price * tick_volume
        tick_day = np.floor(tick_time / 86400)  # Calculate the day of the current tick

        # Check if the new tick is from a different day, then close the current bar
        if tick_day != current_day:
            if trades_count > 0:
                ohlcv_bars.append([bar_time, open_price, high_price, low_price, close_price, volume, trades_count, amount_per_bar])
            # Reset for the new day using the current tick data
            open_price = price
            high_price = price
            low_price = price
            close_price = price
            volume = 0
            trades_count = 0
            remaining_amount = amount_per_bar
            current_day = tick_day
            bar_time = tick_time

        # Start new bar if needed because of the dollar value
        while tick_amount > 0:
            if tick_amount < remaining_amount:
                # Add the entire tick to the current bar
                high_price = max(high_price, price)
                low_price = min(low_price, price)
                close_price = price
                volume += tick_volume
                remaining_amount -= tick_amount
                trades_count += 1
                tick_amount = 0
            else:
                # Calculate the amount of volume that fits within the remaining dollar amount
                volume_to_add = remaining_amount / price
                volume += volume_to_add  # Update the volume here before appending and resetting

                # Append the partially filled bar to the list
                ohlcv_bars.append([bar_time, open_price, high_price, low_price, close_price, volume, trades_count + 1, amount_per_bar])

                # Fill the current bar and continue with a new bar
                tick_volume -= volume_to_add
                tick_amount -= remaining_amount

                # Reset bar values for the new bar using the current tick data
                open_price = price
                high_price = price
                low_price = price
                close_price = price
                volume = 0  # Reset volume for the new bar
                trades_count = 0
                remaining_amount = amount_per_bar
                
                # Increment bar time if splitting a trade
                if tick_volume > 0: #pokud v tradu je jeste zbytek nastavujeme cas o nanosekundu vetsi
                    bar_time = tick_time + 1e-6
                else:
                    bar_time = tick_time #jinak nastavujeme cas ticku
                #bar_time = tick_time

    # Add the last bar if it contains any trades
    if trades_count > 0:
        ohlcv_bars.append([bar_time, open_price, high_price, low_price, close_price, volume, trades_count, amount_per_bar])

    return np.array(ohlcv_bars)


@jit(nopython=True)
def generate_volume_bars_nb(ticks, volume_per_bar):
    """"
    Generates Volume based bars from ticks.
    
    NOTE: UTC day split here (doesnt aggregate trades from different days)
    but realized from UTC (ok for main session) - but needs rework for extension by preprocessing ticks_df and introduction sesssion column
    
    When trade is split into multiple bars it is counted as trade in each of the bars.
    Other option: trade count can be proportionally distributed by weight (0.2 to 1st bar, 0.8 to 2nd bar) - but this is not implemented yet
    https://chatgpt.com/c/ff4802d9-22a2-4b72-8ab7-97a91e7a515f
    """""
    ohlcv_bars = []
    remaining_volume = volume_per_bar

    # Initialize bar values based on the first tick to avoid uninitialized values
    open_price = ticks[0, 1]
    high_price = ticks[0, 1]
    low_price = ticks[0, 1]
    close_price = ticks[0, 1]
    volume = 0
    trades_count = 0
    current_day = np.floor(ticks[0, 0] / 86400)  # Calculate the initial day from the first tick timestamp
    bar_time = ticks[0, 0]  # Initialize bar time with the time of the first tick

    for tick in ticks:
        tick_time = tick[0]
        price = tick[1]
        tick_volume = tick[2]
        tick_day = np.floor(tick_time / 86400)  # Calculate the day of the current tick

        # Check if the new tick is from a different day, then close the current bar
        if tick_day != current_day:
            if trades_count > 0:
                ohlcv_bars.append([bar_time, open_price, high_price, low_price, close_price, volume, trades_count])
            # Reset for the new day using the current tick data
            open_price = price
            high_price = price
            low_price = price
            close_price = price
            volume = 0
            trades_count = 0
            remaining_volume = volume_per_bar
            current_day = tick_day
            bar_time = tick_time  # Update bar time to the current tick time

        # Start new bar if needed because of the volume
        while tick_volume > 0:
            if tick_volume < remaining_volume:
                # Add the entire tick to the current bar
                high_price = max(high_price, price)
                low_price = min(low_price, price)
                close_price = price
                volume += tick_volume
                remaining_volume -= tick_volume
                trades_count += 1
                tick_volume = 0
            else:
                # Fill the current bar and continue with a new bar
                volume_to_add = remaining_volume
                volume += volume_to_add
                tick_volume -= volume_to_add
                trades_count += 1
                # Append the completed bar to the list
                ohlcv_bars.append([bar_time, open_price, high_price, low_price, close_price, volume, trades_count])

                # Reset bar values for the new bar using the current tick data
                open_price = price
                high_price = price
                low_price = price
                close_price = price
                volume = 0
                trades_count = 0
                remaining_volume = volume_per_bar
                                # Increment bar time if splitting a trade
                if tick_volume > 0: #pokud v tradu je jeste zbytek nastavujeme cas o nanosekundu vetsi
                    bar_time = tick_time + 1e-6
                else:
                    bar_time = tick_time #jinak nastavujeme cas ticku


    # Add the last bar if it contains any trades
    if trades_count > 0:
        ohlcv_bars.append([bar_time, open_price, high_price, low_price, close_price, volume, trades_count])

    return np.array(ohlcv_bars)

@jit(nopython=True)
def generate_time_bars_nb(ticks, resolution):
    # Initialize the start and end time
    start_time = np.floor(ticks[0, 0] / resolution) * resolution
    end_time = np.floor(ticks[-1, 0] / resolution) * resolution
    
    # # Calculate number of bars
    # num_bars = int((end_time - start_time) // resolution + 1)
    
    # Using a list to append data only when trades exist
    ohlcv_bars = []
    
    # Variables to track the current bar
    current_bar_index = -1
    open_price = 0
    high_price = -np.inf
    low_price = np.inf
    close_price = 0
    volume = 0
    trades_count = 0
    
    for tick in ticks:
        tick_time = np.floor(tick[0] / resolution) * resolution
        price = tick[1]
        tick_volume = tick[2]
        
        # Check if the tick belongs to a new bar
        if tick_time != start_time + current_bar_index * resolution:
            if current_bar_index >= 0 and trades_count > 0:  # Save the previous bar if trades happened
                ohlcv_bars.append([start_time + current_bar_index * resolution, open_price, high_price, low_price, close_price, volume, trades_count])
            
            # Reset bar values
            current_bar_index = int((tick_time - start_time) / resolution)
            open_price = price
            high_price = price
            low_price = price
            volume = 0
            trades_count = 0
        
        # Update the OHLCV values for the current bar
        high_price = max(high_price, price)
        low_price = min(low_price, price)
        close_price = price
        volume += tick_volume
        trades_count += 1
    
    # Save the last processed bar
    if trades_count > 0:
        ohlcv_bars.append([start_time + current_bar_index * resolution, open_price, high_price, low_price, close_price, volume, trades_count])
    
    return np.array(ohlcv_bars)

# Example usage
if __name__ == '__main__':
    pass
    #example in agg_vect.ipynb