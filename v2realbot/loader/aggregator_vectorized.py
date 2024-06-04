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
from tqdm import tqdm
""""
Module used for vectorized aggregation of trades.

Includes fetch (remote/cached) methods and numba aggregator function for TIME BASED, VOLUME BASED and DOLLAR BARS

"""""

def aggregate_trades(symbol: str, trades_df: pd.DataFrame, resolution: int, type: BarType = BarType.TIME):
    """"
    Accepts dataframe with trades keyed by symbol. Preparess dataframe to 
    numpy and calls Numba optimized aggregator for given bar type. (time/volume/dollar)
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
    columns.append('updated')
    if type == BarType.TIME:
        columns.append('vwap')
        columns.append('buyvolume')
        columns.append('sellvolume')
    if type == BarType.VOLUME:
        columns.append('buyvolume')
        columns.append('sellvolume')
    ohlcv_df = pd.DataFrame(ohlcv_bars, columns=columns)
    ohlcv_df['time'] = pd.to_datetime(ohlcv_df['time'], unit='s').dt.tz_localize('UTC').dt.tz_convert(zoneNY)
    #print(ohlcv_df['updated'])
    ohlcv_df['updated'] = pd.to_datetime(ohlcv_df['updated'], unit="s").dt.tz_localize('UTC').dt.tz_convert(zoneNY)
    # Round to microseconds to maintain six decimal places
    ohlcv_df['updated'] = ohlcv_df['updated'].dt.round('us')

    ohlcv_df.set_index('time', inplace=True)
    #ohlcv_df.index = ohlcv_df.index.tz_localize('UTC').tz_convert(zoneNY)
    return ohlcv_df

# Function to ensure fractional seconds are present
def ensure_fractional_seconds(timestamp):
    if '.' not in timestamp:
        # Inserting .000000 before the timezone indicator 'Z'
        return timestamp.replace('Z', '.000000Z')
    else:
        return timestamp

def convert_dict_to_multiindex_df(tradesResponse):
    """"
    Converts dictionary from cache or from remote (raw input) to multiindex dataframe.
    with microsecond precision (from nanoseconds in the raw data)
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

        # Apply the function to ensure all timestamps have fractional seconds
        #zvazit zda toto ponechat a nebo dat jen pri urcitem erroru pri to_datetime
        #pripadne pak pridelat efektivnejsi pristup, aneb nahrazeni NaT - https://chatgpt.com/c/d2be6f87-b38f-4050-a1c6-541d100b1474
        df['timestamp'] = df['timestamp'].apply(ensure_fractional_seconds)

        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')  # Convert 't' from string to datetime before setting it as an index

        #Adjust to microsecond precision
        df.loc[df['timestamp'].notna(), 'timestamp'] = df['timestamp'].dt.floor('us')

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
    is_same_day = start.date() == end.date()
    # Determine if the requested times fall within the main session
    in_main_session = (time(9, 30) <= start.time() < time(16, 0)) and (time(9, 30) <= end.time() <= time(16, 0))
    file_path = ''
    
    if in_main_session:
        filename_start = zoneNY.localize(datetime.combine(start.date(), time(9, 30)))
        filename_end = zoneNY.localize(datetime.combine(end.date(), time(16, 0)))
        daily_file = f"{symbol}-{int(filename_start.timestamp())}-{int(filename_end.timestamp())}.cache.gz"
        file_path = f"{DATA_DIR}/tradecache/{daily_file}"
        if not force_remote and os.path.exists(file_path):
            print(f"Searching {str(start.date())} cache: " + daily_file)
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
            return pd.DataFrame() if is_empty else dict_to_df(tradesResponse, start, end, exclude_conditions, minsize) 
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            last_exception = e
            time_module.sleep(backoff_factor * (2 ** attempt) + random.uniform(0, 1))  # Adding random jitter

    print("All attempts to fetch data failed.")
    raise ConnectionError(f"Failed to fetch stock trades after {max_retries} retries. Last exception: {str(last_exception)} and {format_exc()}")


def fetch_trades_parallel(symbol, start_date, end_date, exclude_conditions = cfh.config_handler.get_val('AGG_EXCLUDED_TRADES'), minsize = 100, force_remote = False, max_workers=None):
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
    max_workers = min(10, max(2, day_count // 2)) if max_workers is None else max_workers  # Heuristic: half the days to process, but at least 1 and no more than 10

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        #for single_date in (start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)):
        for market_day in tqdm(market_open_days, desc="Processing market days"):
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
        
        for future in tqdm(futures, desc="Fetching data"):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Error fetching data for a day: {e}")

    # Batch concatenation to improve speed
    batch_size = 10
    batches = [results[i:i + batch_size] for i in range(0, len(results), batch_size)]
    final_df = pd.concat([pd.concat(batch, ignore_index=False) for batch in batches], ignore_index=False)

    return final_df

    #original version
    #return pd.concat(results, ignore_index=False)

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
                ohlcv_bars.append([bar_time, open_price, high_price, low_price, close_price, volume, trades_count, amount_per_bar, tick_time])
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
                ohlcv_bars.append([bar_time, open_price, high_price, low_price, close_price, volume, trades_count + 1, amount_per_bar, tick_time])

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
        ohlcv_bars.append([bar_time, open_price, high_price, low_price, close_price, volume, trades_count, amount_per_bar, tick_time])

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
    buy_volume = 0  # Volume of buy trades
    sell_volume = 0  # Volume of sell trades
    prev_price = ticks[0, 1]  # Initialize previous price for the first tick

    for tick in ticks:
        tick_time = tick[0]
        price = tick[1]
        tick_volume = tick[2]
        tick_day = np.floor(tick_time / 86400)  # Calculate the day of the current tick

        # Check if the new tick is from a different day, then close the current bar
        if tick_day != current_day:
            if trades_count > 0:
                ohlcv_bars.append([bar_time, open_price, high_price, low_price, close_price, volume, trades_count, tick_time, buy_volume, sell_volume])
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
            buy_volume = 0
            sell_volume = 0
            # Reset previous tick price (calulating imbalance for each day from the start)
            prev_price = price

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
                
                # Update buy and sell volumes
                if price > prev_price:
                    buy_volume += tick_volume
                elif price < prev_price:
                    sell_volume += tick_volume
                
                tick_volume = 0
            else:
                # Fill the current bar and continue with a new bar
                volume_to_add = remaining_volume
                volume += volume_to_add
                tick_volume -= volume_to_add
                trades_count += 1
                
                # Update buy and sell volumes
                if price > prev_price:
                    buy_volume += volume_to_add
                elif price < prev_price:
                    sell_volume += volume_to_add
                
                # Append the completed bar to the list
                ohlcv_bars.append([bar_time, open_price, high_price, low_price, close_price, volume, trades_count, tick_time, buy_volume, sell_volume])

                # Reset bar values for the new bar using the current tick data
                open_price = price
                high_price = price
                low_price = price
                close_price = price
                volume = 0
                trades_count = 0
                remaining_volume = volume_per_bar
                buy_volume = 0
                sell_volume = 0
                
                # Increment bar time if splitting a trade
                if tick_volume > 0: # If there's remaining volume in the trade, set bar time slightly later
                    bar_time = tick_time + 1e-6
                else:
                    bar_time = tick_time # Otherwise, set bar time to the tick time

        prev_price = price

    # Add the last bar if it contains any trades
    if trades_count > 0:
        ohlcv_bars.append([bar_time, open_price, high_price, low_price, close_price, volume, trades_count, tick_time, buy_volume, sell_volume])

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
    vwap_cum_volume_price = 0  # Cumulative volume * price
    cum_volume = 0  # Cumulative volume for VWAP
    buy_volume = 0  # Volume of buy trades
    sell_volume = 0  # Volume of sell trades
    prev_price = ticks[0, 1]  # Initialize previous price for the first tick
    prev_day = np.floor(ticks[0, 0] / 86400)  # Calculate the initial day from the first tick timestamp
    
    for tick in ticks:
        curr_time = tick[0] #updated time
        tick_time = np.floor(tick[0] / resolution) * resolution
        price = tick[1]
        tick_volume = tick[2]
        tick_day = np.floor(tick_time / 86400)  # Calculate the day of the current tick

        #if the new tick is from a new day, reset previous tick price (calculating imbalance starts over)
        if tick_day != prev_day:
            prev_price = price
            prev_day = tick_day

        # Check if the tick belongs to a new bar
        if tick_time != start_time + current_bar_index * resolution:
            if current_bar_index >= 0 and trades_count > 0:  # Save the previous bar if trades happened
                vwap = vwap_cum_volume_price / cum_volume if cum_volume > 0 else 0
                ohlcv_bars.append([start_time + current_bar_index * resolution, open_price, high_price, low_price, close_price, volume, trades_count, curr_time, vwap, buy_volume, sell_volume])
            
            # Reset bar values
            current_bar_index = int((tick_time - start_time) / resolution)
            open_price = price
            high_price = price
            low_price = price
            volume = 0
            trades_count = 0
            vwap_cum_volume_price = 0
            cum_volume = 0
            buy_volume = 0
            sell_volume = 0
        
        # Update the OHLCV values for the current bar
        high_price = max(high_price, price)
        low_price = min(low_price, price)
        close_price = price
        volume += tick_volume
        trades_count += 1
        vwap_cum_volume_price += price * tick_volume
        cum_volume += tick_volume

        # Update buy and sell volumes
        if price > prev_price:
            buy_volume += tick_volume
        elif price < prev_price:
            sell_volume += tick_volume
        
        prev_price = price

    # Save the last processed bar
    if trades_count > 0:
        vwap = vwap_cum_volume_price / cum_volume if cum_volume > 0 else 0
        ohlcv_bars.append([start_time + current_bar_index * resolution, open_price, high_price, low_price, close_price, volume, trades_count, curr_time, vwap, buy_volume, sell_volume])
    
    return np.array(ohlcv_bars)

# Example usage
if __name__ == '__main__':
    pass
    #example in agg_vect.ipynb