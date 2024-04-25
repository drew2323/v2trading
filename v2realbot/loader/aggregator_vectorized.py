import pandas as pd
import numpy as np
from numba import jit
from alpaca.data.historical import StockHistoricalDataClient
from v2realbot.config import ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY, DATA_DIR
from alpaca.data.requests import StockTradesRequest
import time
from datetime import datetime
from v2realbot.utils.utils import parse_alpaca_timestamp, ltp, zoneNY, send_to_telegram, fetch_calendar_data
import pyarrow

""""
WIP - for later use

"""""

def fetch_stock_trades(symbol, start, end, max_retries=5, backoff_factor=1):
    """
    Attempts to fetch stock trades with exponential backoff. Raises an exception if all retries fail.

    :param symbol: The stock symbol to fetch trades for.
    :param start: The start time for the trade data.
    :param end: The end time for the trade data.
    :param max_retries: Maximum number of retries.
    :param backoff_factor: Factor to determine the next sleep time.
    :return: TradesResponse object.
    :raises: ConnectionError if all retries fail.
    """
    client =  StockHistoricalDataClient(ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY)
    stockTradeRequest = StockTradesRequest(symbol_or_symbols=symbol, start=start, end=end)
    last_exception = None

    for attempt in range(max_retries):
        try:
            tradesResponse = client.get_stock_trades(stockTradeRequest)
            print("Remote Fetch DAY DATA Complete", start, end)
            return tradesResponse
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            last_exception = e
            time.sleep(backoff_factor * (2 ** attempt))

    print("All attempts to fetch data failed.")
    raise ConnectionError(f"Failed to fetch stock trades after {max_retries} retries. Last exception: {str(last_exception)} and {format_exc()}")


@jit(nopython=True)
def ohlcv_bars(ticks, start_time, end_time, resolution):
    """
    Generate OHLCV bars from tick data, skipping intervals without trading activity.
    
    Parameters:
    - ticks: numpy array with columns [timestamp, price, size]
    - start_time: the start timestamp for bars (Unix timestamp)
    - end_time: the end timestamp for bars (Unix timestamp)
    - resolution: time resolution in seconds
    
    Returns:
    - OHLCV bars as a numpy array
    """
    num_bars = (end_time - start_time) // resolution + 1
    bar_list = []

    for i in range(num_bars):
        bar_start_time = start_time + i * resolution
        bar_end_time = bar_start_time + resolution
        bar_ticks = ticks[(ticks[:, 0] >= bar_start_time) & (ticks[:, 0] < bar_end_time)]
        
        if bar_ticks.shape[0] == 0:
            continue  # Skip this bar as there are no ticks

        # Calculate OHLCV values
        open_price = bar_ticks[0, 1]  # open
        high_price = np.max(bar_ticks[:, 1])  # high
        low_price = np.min(bar_ticks[:, 1])  # low
        close_price = bar_ticks[-1, 1]  # close
        volume = np.sum(bar_ticks[:, 2])  # volume
        bar_time = bar_start_time  # timestamp for the bar

        bar_list.append([open_price, high_price, low_price, close_price, volume, bar_time])

    # Convert list to numpy array
    if bar_list:
        ohlcv = np.array(bar_list)
    else:
        ohlcv = np.empty((0, 6))  # return an empty array if no bars were created

    return ohlcv

# Example usage
if __name__ == '__main__':
    # symbol = ["BAC"]
    # #datetime in zoneNY 
    # day_start = datetime(2024, 4, 22, 9, 30, 0)
    # day_stop = datetime(2024, 4, 22, 16, 00, 0)

    # day_start = zoneNY.localize(day_start)
    # day_stop = zoneNY.localize(day_stop)

    # tradesResponse = fetch_stock_trades(symbol, day_start, day_stop)

    # df = tradesResponse.df
    # df.to_parquet('trades_bac.parquet', engine='pyarrow')

    df=pd.read_parquet('trades_bac.parquet',engine='pyarrow')
    print(df)

    #df = pd.read_csv('tick_data.csv')  # DF with tick data
# Assuming 'df' is your DataFrame with columns 'time', 'price', 'size', 'condition'
    exclude_conditions = ['ConditionA', 'ConditionB']  # Conditions to exclude
    df_filtered = df[~df['condition'].isin(exclude_conditions)]
    # Define your start and end times based on your trading session, ensure these are Unix timestamps
    start_time = pd.to_datetime('2023-01-01 09:30:00').timestamp()
    end_time = pd.to_datetime('2023-01-01 16:00:00').timestamp()
    ticks = df[['time', 'price', 'size']].to_numpy()
    ticks[:, 0] = pd.to_datetime(ticks[:, 0]).astype('int64') // 1_000_000_000  # Convert to Unix timestamp
    resolution_seconds = 1  # 1 second resolution
    ohlcv_data = ohlcv_bars(ticks, start_time, end_time, resolution_seconds)

    # Converting the result back to DataFrame for better usability
    ohlcv_df = pd.DataFrame(ohlcv_data, columns=['Open', 'High', 'Low', 'Close', 'Volume', 'Time'])
    ohlcv_df['Time'] = pd.to_datetime(ohlcv_df['Time'], unit='s')  # Convert timestamps back to datetime
