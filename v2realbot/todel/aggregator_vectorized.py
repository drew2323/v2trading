import pandas as pd
import numpy as np
from numba import jit
from v2realbot.utils.utils import zoneNY
from v2realbot.enums.enums import AggType

""""
Module used for vectorized aggregation of trades.

Includes fetch (remote/cached) methods and numba aggregator function for TIME BASED, VOLUME BASED and DOLLAR BARS

"""""

def aggregate_trades(symbol: str, trades_df: pd.DataFrame, resolution: int, type: AggType = AggType.OHLCV):
    """"
    Accepts dataframe with trades keyed by symbol. Preparess dataframe to 
    numpy and calls Numba optimized aggregator for given bar type. (time/volume/dollar)
    """""
    #trades_df = trades_df.loc[symbol] no symbol keyed df
    trades_df= trades_df.reset_index()
    ticks = trades_df[['t', 'p', 's']].to_numpy()
    # Extract the timestamps column (assuming it's the first column)
    timestamps = ticks[:, 0]
    # Convert the timestamps to Unix timestamps in seconds with microsecond precision
    unix_timestamps_s = np.array([ts.timestamp() for ts in timestamps], dtype='float64')
    # Replace the original timestamps in the NumPy array with the converted Unix timestamps
    ticks[:, 0] = unix_timestamps_s
    ticks = ticks.astype(np.float64)
    #based on type, specific aggregator function is called
    match type:
        case AggType.OHLCV:
            ohlcv_bars = generate_time_bars_nb(ticks, resolution)
        case AggType.OHLCV_VOL:
            ohlcv_bars = generate_volume_bars_nb(ticks, resolution)
        case AggType.OHLCV_DOL:
            ohlcv_bars = generate_dollar_bars_nb(ticks, resolution)
        case _:
            raise ValueError("Invalid AggType type. Supported types are 'time', 'volume' and 'dollar'.")
    # Convert the resulting array back to a DataFrame
    columns = ['time', 'open', 'high', 'low', 'close', 'volume', 'trades']
    if type == AggType.OHLCV_DOL:
        columns.append('amount')
    columns.append('updated')
    if type == AggType.OHLCV:
        columns.append('vwap')
        columns.append('buyvolume')
        columns.append('sellvolume')
    if type == AggType.OHLCV_VOL:
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