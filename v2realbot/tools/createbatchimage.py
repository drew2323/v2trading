import argparse
#import v2realbot.reporting.metricstoolsimage as mt
import matplotlib
import matplotlib.dates as mdates
matplotlib.use('Agg')  # Set the Matplotlib backend to 'Agg'
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from datetime import datetime
from typing import List
from enum import Enum
import numpy as np
import v2realbot.controller.services as cs
#from rich import print
from v2realbot.common.PrescribedTradeModel import TradeDirection, TradeStatus, Trade, TradeStoplossType
from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, safe_get
from pathlib import Path
from v2realbot.config import WEB_API_KEY, DATA_DIR, MEDIA_DIRECTORY
from v2realbot.enums.enums import RecordType, StartBarAlign, Mode, Account, OrderSide
from io import BytesIO
from v2realbot.utils.historicals import get_historical_bars
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
import mlroom.utils.ext_services as es
from v2realbot.common.db import pool, execute_with_retry, row_to_runarchive, row_to_runarchiveview
from v2realbot.utils.utils import ltp, isrising, isfalling,trunc,AttributeDict
import tqdm

# start_date = datetime(2020, 1, 1, 0, 0, 0, 0, zoneNY)
# end_date = datetime(2024, 1, 2, 0, 0, 0, 0, zoneNY)
# bars= get_historical_bars("BLK", start_date, end_date, TimeFrame.Hour)
# print("bars for given period",bars)

#upload image to the remote server scp 4bea3a54.png david@142.132.188.109:/home/david/media/basic/ 

#zkopirovany a upravena funkce, ktera umi vybrat cilovy server
def generate_trading_report_image(runner_ids: list = None, batch_id: str = None, stream: bool = False, server: str = None):
    
    #TODO dopracovat drawdown a minimalni a maximalni profity nikoliv cumulovane, zamyslet se
    #TODO list of runner_ids
    #TODO pridelat na vytvoreni runnera a batche, samostatne REST API + na remove archrunnera
    
    if runner_ids is None and batch_id is None:
        return -2, f"runner_id or batch_id must be present"

    if batch_id is not None:
        res, runner_ids = es.get_archived_runners_list_by_batch_id(batch_id, server)
        if res != 0:
            print(f"no batch {batch_id} found")
            return -1, f"no batch {batch_id} found"
        
    trades = []
    symbol = None
    mode = None
    sada_list = []
    for id in tqdm.tqdm(runner_ids):
        #get runner
        res, sada =es.get_archived_runner_header_by_id(id, server)
        if res != 0:
            print(f"no runner {id} found")
            return -1, f"no runner {id} found"
        
        #sada = AttributeDict(**sada)

        print("archrunner")
        print(sada)

        sada["started"]=datetime.fromisoformat(sada['started'])  if sada['started'] else None
        sada["stopped"]=datetime.fromisoformat(sada['stopped']) if sada['stopped'] else None
        sada["bt_from"]=datetime.fromisoformat(sada['bt_from']) if sada['bt_from'] else None
        sada["bt_to"]=datetime.fromisoformat(sada['bt_to']) if sada['bt_to'] else None

        sada_list.append(sada)
    
        symbol = sada["symbol"]
        mode = sada["mode"]
        # Parse trades

        trades_dicts =  sada["metrics"]["prescr_trades"]

        for trade_dict in trades_dicts:
            trade_dict['last_update'] = datetime.fromtimestamp(trade_dict.get('last_update')).astimezone(zoneNY) if trade_dict['last_update'] is not None else None
            trade_dict['entry_time'] = datetime.fromtimestamp(trade_dict.get('entry_time')).astimezone(zoneNY) if trade_dict['entry_time'] is not None else None
            trade_dict['exit_time'] = datetime.fromtimestamp(trade_dict.get('exit_time')).astimezone(zoneNY) if trade_dict['exit_time'] is not None else None
            trades.append(Trade(**trade_dict))

        #print(trades)

    #get from to dates
    #calculate start a end z min a max dni - jelikoz muze byt i seznam runner_ids a nejenom batch, pripadne testovaci sady
    if mode in [Mode.BT,Mode.PREP]:
        start_date = min(runner["bt_from"] for runner in sada_list)
        end_date = max(runner["bt_to"] for runner in sada_list)
    else:
        start_date = min(runner["started"] for runner in sada_list)
        end_date = max(runner["stopped"] for runner in sada_list) 

    #hour bars for backtested period
    print(start_date,end_date)
    bars= get_historical_bars(symbol, start_date, end_date, TimeFrame.Hour)
    print("bars for given period",bars)
    """Bars a dictionary with the following keys:
        * high: A list of high prices
        * low: A list of low prices
        * volume: A list of volumes
        * close: A list of close prices
        * hlcc4: A list of HLCC4 indicators
        * open: A list of open prices
        * time: A list of times in UTC (ISO 8601 format)
        * trades: A list of number of trades
        * resolution: A list of resolutions (all set to 'D')
        * confirmed: A list of booleans (all set to True)
        * vwap: A list of VWAP indicator
        * updated: A list of booleans (all set to True)
        * index: A list of integers (from 0 to the length of the list of daily bars)
    """

    # Filter to only use trades with status 'CLOSED'
    closed_trades = [trade for trade in trades if trade.status == TradeStatus.CLOSED]

    if len(closed_trades) == 0:
        return -1, "image generation no closed trades"
    
    # Data extraction for the plots
    exit_times = [trade.exit_time for trade in closed_trades if trade.exit_time is not None]
    ##cumulative_profits = [trade.profit_sum for trade in closed_trades if trade.profit_sum is not None]

    profits = [trade.profit for trade in closed_trades if trade.profit is not None]
    cumulative_profits = np.cumsum(profits)
    wins = [trade.profit for trade in closed_trades if trade.profit > 0]
    losses = [trade.profit for trade in closed_trades if trade.profit < 0]

    wins_long = [trade.profit for trade in closed_trades if trade.profit > 0 and trade.direction == TradeDirection.LONG]
    losses_long = [trade.profit for trade in closed_trades if trade.profit < 0 and trade.direction == TradeDirection.LONG]    
    wins_short = [trade.profit for trade in closed_trades if trade.profit > 0 and trade.direction == TradeDirection.SHORT]
    losses_short = [trade.profit for trade in closed_trades if trade.profit < 0 and trade.direction == TradeDirection.SHORT]    

    directions = [trade.direction for trade in closed_trades]

    long_profits = [trade.profit for trade in closed_trades if trade.direction == TradeDirection.LONG and trade.profit is not None]
    short_profits = [trade.profit for trade in closed_trades if trade.direction == TradeDirection.SHORT and trade.profit is not None]

    # Setting up dark mode for the plots
    plt.style.use('dark_background')

    # Optionally, you can further customize colors, labels, and axes
    params = {
        'axes.titlesize': 9,
        'axes.labelsize': 8,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'axes.labelcolor': '#a9a9a9', #a1a3aa',
        'axes.facecolor': '#121722', #'#0e0e0e', #202020',  # Dark background for plot area
        'axes.grid': False,  # Turn off the grid globally
        'grid.color': 'gray',  # If the grid is on, set grid line color
        'grid.linestyle': '--',  # Grid line style        
        'grid.linewidth': 1,
        'xtick.color': '#a9a9a9',
        'ytick.color': '#a9a9a9',
        'axes.edgecolor': '#a9a9a9'
    }
    plt.rcParams.update(params)


    #Custom dark theme similar to the provided image
    # dark_finance_theme = {
    #     'background': '#1a1a1a',  # Very dark (almost black) background
    #     'text': '#eaeaea',       # Light grey text for readability
    #     'grid': '#333333',       # Dark grey grid lines
    #     'accent': '#2e91e5',     # Bright blue accent for main elements
    #     'secondary': '#e15f99',  # Secondary pink/magenta color for highlights
    #     'highlight': '#fcba03',  # Gold-like color for special highlights
    # }

    # # Apply the theme settings
    # plt.style.use('dark_background')
    # plt.rcParams.update({
    #     'figure.facecolor': dark_finance_theme['background'],
    #     'axes.facecolor': dark_finance_theme['background'],
    #     'axes.edgecolor': dark_finance_theme['text'],
    #     'axes.labelcolor': dark_finance_theme['text'],
    #     'axes.titlesize': 12,
    #     'axes.labelsize': 10,
    #     'xtick.color': dark_finance_theme['text'],
    #     'xtick.labelsize': 8,
    #     'ytick.color': dark_finance_theme['text'],
    #     'ytick.labelsize': 8,
    #     'grid.color': dark_finance_theme['grid'],
    #     'grid.linestyle': '-',
    #     'grid.linewidth': 0.6,
    #     'legend.facecolor': dark_finance_theme['background'],
    #     'legend.edgecolor': dark_finance_theme['background'],
    #     'legend.fontsize': 10,
    #     'text.color': dark_finance_theme['text'],
    #     'lines.color': dark_finance_theme['accent'],
    #     'patch.edgecolor': dark_finance_theme['accent'],
    # })

    if len(closed_trades) > 100:
        fig, axs = plt.subplots(3, 4, figsize=(15, 10))        
    else:
        # Create a combined figure for all plots 11,7 ideal na 3,4
        fig, axs = plt.subplots(3, 4, figsize=(12, 7))

    #TITLE
    title = ""
    cnt_ids = len(runner_ids)
    if batch_id is not None:
        title = "Batch: "+str(batch_id)+ " "

    title += "Days: " + str(cnt_ids)
    if cnt_ids == 1:
        title += " ("+str(runner_ids[0])[0:14]+") "
       
        if sada["mode"] == Mode.BT:
            datum = sada["bt_from"]
        else:
            datum = sada["started"]

        title += datum.strftime("%d.%m.%Y %H:%M")


    # Add a title to the figure
    fig.suptitle(title, fontsize=15, color='white')

    # Plot 1: Overall Profit Summary Chart
    total_wins = int(sum(wins))
    total_losses = int(sum(losses))
    net_profit = int(sum(profits))
    sns.barplot(x=['Total', 'Wins','Losses'],
                y=[net_profit, total_wins, total_losses],
                ax=axs[0, 0])
    axs[0, 0].set_title('Overall Profit Summary')
    # Define the offset for placing text inside the bars
    offset = max(total_wins, abs(total_losses), net_profit) * 0.05  # 5% of the highest (or lowest) bar value

    # Function to place text annotation
    def place_annotation(ax, x, value, offset):
        va = 'top' if value >= 0 else 'bottom'
        y = value - offset if value >= 0 else value + offset
        ax.text(x, y, f'{value}', ha='center', va=va, color='black', fontsize=12)

    # Annotate the Total Wins, Losses, and Net Profit bars
    place_annotation(axs[0, 0], 0, net_profit, offset)
    place_annotation(axs[0, 0], 1, total_wins, offset)
    place_annotation(axs[0, 0], 2, total_losses, offset)

    # Plot 2: LONG - profit summary
    total_wins_long = int(sum(wins_long))
    total_losses_long = int(sum(losses_long))
    total_long = total_wins_long + total_losses_long
    sns.barplot(x=['Total', 'Wins','Losses'],
                y=[total_long, total_wins_long, total_losses_long],
                ax=axs[0, 1])
    axs[0, 1].set_title('LONG Profit Summary')
    # Define the offset for placing text inside the bars
    offset = max(total_wins_long, abs(total_losses_long)) * 0.05  # 5% of the highest (or lowest) bar value

    place_annotation(axs[0, 1], 0, total_long, offset)
    place_annotation(axs[0, 1], 1, total_wins_long, offset)
    place_annotation(axs[0, 1], 2, total_losses_long, offset)


    # Plot 3: SHORT - profit summary
    total_wins_short =int(sum(wins_short))
    total_losses_short = int(sum(losses_short))  
    total_short = total_wins_short + total_losses_short
    sns.barplot(x=['Total', 'Wins', 'Losses'],
                y=[total_short, total_wins_short,
                   total_losses_short],
                ax=axs[0, 2])
    axs[0, 2].set_title('SHORT Profit Summary')
    # Define the offset for placing text inside the bars
    offset = max(total_wins_short, abs(total_losses_short)) * 0.05  # 5% of the highest (or lowest) bar value

    place_annotation(axs[0, 2], 0, total_short, offset)
    place_annotation(axs[0, 2], 1, total_wins_short, offset)
    place_annotation(axs[0, 2], 2, total_losses_short, offset)

    # Plot 4: Trade Counts Bar Chart
    long_count = len([trade for trade in closed_trades if trade.direction == TradeDirection.LONG])
    short_count = len([trade for trade in closed_trades if trade.direction == TradeDirection.SHORT])
    sns.barplot(x=['Long Trades', 'Short Trades'], y=[long_count, short_count], ax=axs[0, 3])
    axs[0, 3].set_title('Trade Counts')
    offset = max(long_count, short_count) * 0.05  # 5% of the highest (or lowest) bar value

    place_annotation(axs[0, 3], 0, long_count, offset)
    place_annotation(axs[0, 3], 1, short_count, offset)

    #PLOT 5 - Heatman (exit time)
    # Creating a DataFrame for the heatmap
    heatmap_data_list = []
    for trade in trades:
        if trade.status == TradeStatus.CLOSED:
            day = trade.exit_time.strftime('%m-%d')  # Format date as 'MM-DD'
            #day = trade.exit_time.date()
            hour = trade.exit_time.hour
            profit = trade.profit
            heatmap_data_list.append({'Day': day, 'Hour': hour, 'Profit': profit})

    try:
        heatmap_data = pd.DataFrame(heatmap_data_list)
        heatmap_data = heatmap_data.groupby(['Day', 'Hour']).sum().reset_index()
        heatmap_pivot = heatmap_data.pivot(index='Day', columns='Hour', values='Profit')

        # Heatmap of Profits
        sns.heatmap(heatmap_pivot, cmap='viridis', ax=axs[1, 0])
        axs[1, 0].set_title('Heatmap of Profits (based on Exit time)')
        axs[1, 0].set_xlabel('Hour of Day')
        axs[1, 0].set_ylabel('Day')
    except KeyError:
             # Handle the case where there is no data
            axs[1, 0].text(0.5, 0.5, 'No data available', 
                            horizontalalignment='center', 
                            verticalalignment='center', 
                            transform=axs[1, 0].transAxes)
            axs[1, 0].set_title('Heatmap of Profits (based on Exit time)')       
    
    # Plot 6: Profit/Loss Distribution Histogram
    sns.histplot(profits, bins=30, ax=axs[1, 1], kde=True, color='skyblue')
    axs[1, 1].set_title('Profit/Loss Distribution')
    axs[1, 1].set_xlabel('Profit/Loss')
    axs[1, 1].set_ylabel('Frequency')

    # Plot 7
    #    - for 1 den: Position Size Distribution   
    #    - for more days:  Trade Duration vs. Profit/Loss
    if len(runner_ids) == 1:
        
        sizes = [trade.size for trade in closed_trades if trade.size is not None]
        if sizes:
            size_counts = {size: sizes.count(size) for size in set(sizes)}
            sns.barplot(x=list(size_counts.keys()), y=list(size_counts.values()), ax=axs[1, 2])
            axs[1, 2].set_title('Position Size Distribution')
        else:
             # Handle the case where there is no data
            axs[1, 2].text(0.5, 0.5, 'No data available', 
                            horizontalalignment='center', 
                            verticalalignment='center', 
                            transform=axs[1, 2].transAxes)
            axs[1, 2].set_title('Position Size Distribution')   
    else:
        trade_durations = []
        trade_profits = []
        #trade_volumes = []  # Assuming you have a way to measure the size/volume of each trade
        trade_types = []  # 'Long' or 'Short'

        for trade in trades:
            if trade.status == TradeStatus.CLOSED:
                duration = (trade.exit_time - trade.entry_time).total_seconds() / 60  # Duration in minutes  (3600 for hours)
                trade_durations.append(duration)
                trade_profits.append(trade.profit)
                ##trade_volumes.append(trade.size)  # or any other measure of trade size
                trade_types.append('Long' if trade.direction == TradeDirection.LONG else 'Short')

        # Trade Duration vs. Profit/Loss
        scatter_data = pd.DataFrame({
            'Duration': trade_durations,
            'Profit': trade_profits,
            #'Volume': trade_volumes,
            'Type': trade_types
        })
        #sns.scatterplot(data=scatter_data, x='Duration', y='Profit', size='Volume', hue='Type', ax=axs[1, 2])
        sns.scatterplot(data=scatter_data, x='Duration', y='Profit', hue='Type', ax=axs[1, 2])
        axs[1, 2].set_title('Trade Duration vs. Profit/Loss')
        axs[1, 2].set_xlabel('Duration (Minutes)')
        axs[1, 2].set_ylabel('Profit/Loss')


    #Plot 8 Cumulative profit - bud 1 den nebo vice dni + pridame pod to vyvoj ceny
    # Extract the closing prices and times
    closing_prices = bars.get('close',[]) if bars is not None else [] 
    #times = bars['time']  # Assuming this is a list of pandas Timestamp objects
    times = pd.to_datetime(bars['time']) if bars is not None else []  # Ensure this is a Pandas datetime series
    # # Plot the closing prices over time
    # axs[0, 4].plot(times, closing_prices, color='blue')
    # axs[0, 4].tick_params(axis='x', rotation=45)  # Rotate date labels if necessar
    # axs[0, 4].xaxis.set_major_formatter(mdates.DateFormatter('%H', tz=zoneNY))

    if len(runner_ids)== 1:
        if cumulative_profits.size > 0:
            # Plot 3: Cumulative Profit Over Time with Max Profit Point
            max_profit_time = exit_times[np.argmax(cumulative_profits)]
            max_profit = max(cumulative_profits)
            min_profit_time = exit_times[np.argmin(cumulative_profits)]
            min_profit = min(cumulative_profits)

            #Plot Cumulative Profit Over Time with Max Profit Point on the primary y-axis
            # Create a secondary y-axis for the closing prices
            ax2 = axs[1, 3].twinx()
            ax2.plot(times, closing_prices, label='Closing Price', color='orange')
            ax2.set_ylabel('Closing Price', color='orange')
            ax2.tick_params(axis='y', labelcolor='orange')
            
            # Set the limits for the x-axis to cover the full range of 'times'
            if isinstance(times, pd.DatetimeIndex):
                axs[1, 3].set_xlim(times.min(), times.max())
            sns.lineplot(x=exit_times, y=cumulative_profits, ax=axs[1, 3], color='limegreen')
            axs[1, 3].scatter(max_profit_time, max_profit, color='green', label='Max Profit')
            axs[1, 3].scatter(min_profit_time, min_profit, color='red', label='Min Profit')
            axs[1, 3].set_xlabel('Time')
            axs[1, 3].set_ylabel('Cumulative Profit', color='limegreen')
            axs[1, 3].tick_params(axis='y', labelcolor='limegreen')
            axs[1, 3].xaxis.set_major_formatter(mdates.DateFormatter('%H', tz=zoneNY))
            # Add legends to the plot
            # lines, labels = axs[1, 3].get_legend_handles_labels()
            # lines2, labels2 = ax2.get_legend_handles_labels()
            # axs[1, 3].legend(lines + lines2, labels + labels2, loc='upper left')
        else:
            # Handle the case where cumulative_profits is empty
            axs[1, 3].text(0.5, 0.5, 'No profit data available', 
                            horizontalalignment='center', 
                            verticalalignment='center', 
                            transform=axs[1, 3].transAxes)
            axs[1, 3].set_title('Cumulative Profit Over Time')
    else:
        # Calculate cumulative profit
        # Additional Plot: Cumulative Profit Over Time
        # Sort trades by exit time

        # # Set the limits for the x-axis to cover the full range of 'times'
        # axs[1, 3].set_xlim(times.min(), times.max())

        sorted_trades = sorted([trade for trade in trades if trade.status == TradeStatus.CLOSED], 
                            key=lambda x: x.exit_time)
        cumulative_profits_sorted = np.cumsum([trade.profit for trade in sorted_trades])
        exit_times_sorted = [trade.exit_time for trade in sorted_trades if trade.exit_time is not None]

        # Create a secondary y-axis for the closing prices
        ax2 = axs[1, 3].twinx()
        ax2.plot(times, closing_prices, label='Closing Price', color='orange')
        ax2.set_ylabel('Closing Price', color='orange')
        ax2.tick_params(axis='y', labelcolor='orange')

        axs[1, 3].set_xlim(times.min(), times.max())
        # Plot Cumulative Profit Over Time on the primary y-axis
        axs[1, 3].plot(exit_times_sorted, cumulative_profits_sorted, label='Cumulative Profit', color='blue')
        axs[1, 3].set_xlabel('Time')
        axs[1, 3].set_ylabel('Cumulative Profit', color='blue')
        axs[1, 3].tick_params(axis='y', labelcolor='blue')

        # Format dates on the x-axis
        axs[1, 3].xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.', tz=zoneNY))
        axs[1, 3].tick_params(axis='x', rotation=45)  # Rotate date labels if necessary

        # Set the title
        axs[1, 3].set_title('Cumulative Profit and Closing Price Over Time')

        # Add legends to the plot
        # axs[1, 3].legend(loc='upper left')
        # ax2.legend(loc='upper right')

    # Plot 9
    # - for 1 day: Daily Relative Profit Chart
    # - for more days: Heatmap of Profits (based on Entry time)
    if len(runner_ids) == 1:
        daily_rel_profits = [trade.rel_profit for trade in closed_trades if trade.rel_profit is not None]
        sns.lineplot(x=range(len(daily_rel_profits)), y=daily_rel_profits, ax=axs[2, 0])
        axs[2, 0].set_title('Daily Relative Profit')
    else:
        # Creating a DataFrame for the heatmap
        heatmap_data_list = []
        for trade in trades:
            if trade.status == TradeStatus.CLOSED:
                day = trade.entry_time.strftime('%m-%d')  # Format date as 'MM-DD'
                #day = trade.entry_time.date()
                hour = trade.entry_time.hour
                profit = trade.profit
                heatmap_data_list.append({'Day': day, 'Hour': hour, 'Profit': profit})

        heatmap_data = pd.DataFrame(heatmap_data_list)
        heatmap_data = heatmap_data.groupby(['Day', 'Hour']).sum().reset_index()
        heatmap_pivot = heatmap_data.pivot(index='Day', columns='Hour', values='Profit')

        # Heatmap of Profits
        sns.heatmap(heatmap_pivot, cmap='viridis', ax=axs[2, 0])
        axs[2, 0].set_title('Heatmap of Profits (based on Entry time)')
        axs[2, 0].set_xlabel('Hour of Day')
        axs[2, 0].set_ylabel('Day')

    # Plot 10: Profits Based on Hour of the Day (Entry)
    entry_hours = [trade.entry_time.hour for trade in closed_trades if trade.entry_time is not None]
    profits_by_hour = {}
    for hour, trade in zip(entry_hours, closed_trades):
        if hour not in profits_by_hour:
            profits_by_hour[hour] = 0
        profits_by_hour[hour] += trade.profit

    # Sorting by hour for plotting
    sorted_hours = sorted(profits_by_hour.keys())
    sorted_profits = [profits_by_hour[hour] for hour in sorted_hours]

    if sorted_profits:
        sns.barplot(x=sorted_hours, y=sorted_profits, ax=axs[2, 1])
        axs[2, 1].set_title('Profits by Hour of Day (Entry)')
        axs[2, 1].set_xlabel('Hour of Day')
        axs[2, 1].set_ylabel('Profit')
    else:
        # Handle the case where sorted_profits is empty
        axs[2, 1].text(0.5, 0.5, 'No data available', 
                        horizontalalignment='center', 
                        verticalalignment='center', 
                        transform=axs[2, 1].transAxes)
        axs[2, 1].set_title('Profits by Hour of Day (Entry)')

    # Plot 11: Profits Based on Hour of the Day - based on Exit
    exit_hours = [trade.exit_time.hour for trade in closed_trades if trade.exit_time is not None]
    profits_by_hour = {}
    for hour, trade in zip(exit_hours, closed_trades):
        if hour not in profits_by_hour:
            profits_by_hour[hour] = 0
        profits_by_hour[hour] += trade.profit

    # Sorting by hour for plotting
    sorted_hours = sorted(profits_by_hour.keys())
    sorted_profits = [profits_by_hour[hour] for hour in sorted_hours]

    if sorted_profits:
        sns.barplot(x=sorted_hours, y=sorted_profits, ax=axs[2, 2])
        axs[2, 2].set_title('Profits by Hour of Day (Exit)')
        axs[2, 2].set_xlabel('Hour of Day')
        axs[2, 2].set_ylabel('Profit')
    else:
        # Handle the case where sorted_profits is empty
        axs[2, 2].text(0.5, 0.5, 'No data available', 
                        horizontalalignment='center', 
                        verticalalignment='center', 
                        transform=axs[2, 2].transAxes)
        axs[2, 2].set_title('Profits by Hour of Day (Exit)')

    # Plot 12: Calculate profits by day of the week
    day_of_week_profits = {i: 0 for i in range(7)}  # Dictionary to store profits for each day of the week

    for trade in trades:
        if trade.status == TradeStatus.CLOSED:
            day_of_week = trade.exit_time.weekday()  # Monday is 0 and Sunday is 6
            day_of_week_profits[day_of_week] += trade.profit

    days = ['Mo', 'Tue', 'Wed', 'Thu', 'Fri']
    # Additional Plot: Strategy Performance by Day of the Week
    axs[2, 3].bar(days, [day_of_week_profits[i] for i in range(5)])
    axs[2, 3].set_title('Profit by Day of the Week')
    axs[2, 3].set_xlabel('Day of the Week')
    axs[2, 3].set_ylabel('Cumulative Profit')    

    #filename 
    file = batch_id if batch_id is not None else runner_ids[0]
    image_file_name = f"{file}.png"
    image_path = str(MEDIA_DIRECTORY / "basic" / image_file_name)

    # Adjust layout and save the combined plot as an image
    plt.tight_layout()

    if stream is False:
        plt.savefig(image_path)
        plt.close()
        return 0, None
    else:
        # Return the image as a BytesIO stream
        img_stream = BytesIO()
        plt.savefig(img_stream, format='png')
        plt.close()
        img_stream.seek(0)  # Rewind the stream to the beginning
        return 0, img_stream        

##Generates BATCH REPORT again for the given batch_id
##USAGE: python createbatchimage.py <batch_id>
#Parse the command-line arguments
#parser = argparse.ArgumentParser(description="Generate trading report image with batch ID")
# parser.add_argument("server", type=str, help="The server IP for the report")
# parser.add_argument("batch_id", type=str, help="The batch ID for the report")
# args = parser.parse_args()

# batch_id = args.batch_id
# server = args.server

# Generate the report image, using local copy, which will replace the current e0639b45  4bea3a54
res, val = generate_trading_report_image(batch_id="4bea3a54", server="142.132.188.109")

# Print the result
if res == 0:
    print("BATCH REPORT CREATED")
else:
    print(f"BATCH REPORT ERROR - {val}")


