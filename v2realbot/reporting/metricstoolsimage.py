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
from rich import print
from v2realbot.common.PrescribedTradeModel import TradeDirection, TradeStatus, Trade, TradeStoplossType
from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, safe_get, print
from pathlib import Path
from v2realbot.config import WEB_API_KEY, DATA_DIR, MEDIA_DIRECTORY
from v2realbot.enums.enums import RecordType, StartBarAlign, Mode, Account, OrderSide
from io import BytesIO
# Assuming Trade, TradeStatus, TradeDirection, TradeStoplossType classes are defined elsewhere

def generate_trading_report_image(runner_ids: list = None, batch_id: str = None, stream: bool = False):
    
    #TODO dopracovat drawdown a minimalni a maximalni profity nikoliv cumulovane, zamyslet se
    #TODO list of runner_ids
    #TODO pridelat na vytvoreni runnera a batche, samostatne REST API + na remove archrunnera
    
    if runner_ids is None and batch_id is None:
        return -2, f"runner_id or batch_id must be present"

    if batch_id is not None:
        res, runner_ids =cs.get_archived_runnerslist_byBatchID(batch_id)

        if res != 0:
            print(f"no batch {batch_id} found")
            return -1, f"no batch {batch_id} found"
        
    trades = []
    for id in runner_ids:
        #get runner
        res, sada =cs.get_archived_runner_header_byID(id)
        if res != 0:
            print(f"no runner {id} found")
            return -1, f"no runner {id} found"
        
        print("archrunner")
        print(sada)
    
        # Parse trades
        #trades = [Trade(**trade_dict) for trade_dict in set.metrics["prescr_trades"]]

        trades_dicts =  sada.metrics["prescr_trades"]

        for trade_dict in trades_dicts:
            trade_dict['last_update'] = datetime.fromtimestamp(trade_dict.get('last_update')).astimezone(zoneNY) if trade_dict['last_update'] is not None else None
            trade_dict['entry_time'] = datetime.fromtimestamp(trade_dict.get('entry_time')).astimezone(zoneNY) if trade_dict['entry_time'] is not None else None
            trade_dict['exit_time'] = datetime.fromtimestamp(trade_dict.get('exit_time')).astimezone(zoneNY) if trade_dict['exit_time'] is not None else None
            trades.append(Trade(**trade_dict))

        print(trades)

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

    # # Setting up dark mode for the plots
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

    #NEW LOOK
    # # Set the style to dark mode with custom settings
    # plt.style.use('dark_background')

    # # Define a custom dark theme color palette
    # dark_theme_colors = {
    #     'background': '#1c1c1c',  # Dark gray
    #     'text': '#d6d6d6',       # Light gray for a subtle contrast
    #     'grid': '#414141',       # Slightly lighter gray than background for grid
    #     'highlight': '#3498db',  # Bright blue for highlights (max/min points, etc.)
    #     'warning': '#e74c3c',    # Red color for warnings or important highlights
    #     'neutral': '#7f8c8d',    # Neutral color for less important elements
    # }

    # # Customize the color scheme
    # params = {
    #     'figure.facecolor': dark_theme_colors['background'],
    #     'axes.titlesize': 10,
    #     'axes.labelsize': 9,
    #     'xtick.labelsize': 9,
    #     'ytick.labelsize': 9,
    #     'axes.labelcolor': dark_theme_colors['text'],
    #     'axes.facecolor': dark_theme_colors['background'],
    #     'axes.grid': False,  # Control grid visibility
    #     'axes.edgecolor': dark_theme_colors['text'],
    #     'xtick.color': dark_theme_colors['text'],
    #     'ytick.color': dark_theme_colors['text'],
    #     'text.color': dark_theme_colors['text'],
    #     'legend.facecolor': dark_theme_colors['background'],
    #     'legend.edgecolor': dark_theme_colors['text'],
    #     'legend.fontsize': 8,
    #     'legend.title_fontsize': 9,
    # }

    # # Apply the custom color scheme
    # plt.rcParams.update(params)

    # Create a combined figure for all plots
    fig, axs = plt.subplots(3, 4, figsize=(11, 7))

    #TITLE
    title = ""
    cnt_ids = len(runner_ids)
    if batch_id is not None:
        title = "Batch: "+str(batch_id)+ " "

    title += "Days: " + str(cnt_ids)
    if cnt_ids == 1:
        title += " ("+str(runner_ids[0])[0:14]+") "
       
        if sada.mode == Mode.BT:
            datum = sada.bt_from
        else:
            datum = sada.started

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


    #Cumulative profit - bud 1 den nebo vice dni
    if len(runner_ids)== 1:
        if cumulative_profits.size > 0:
            # Plot 3: Cumulative Profit Over Time with Max Profit Point
            max_profit_time = exit_times[np.argmax(cumulative_profits)]
            max_profit = max(cumulative_profits)
            min_profit_time = exit_times[np.argmin(cumulative_profits)]
            min_profit = min(cumulative_profits)
            sns.lineplot(x=exit_times, y=cumulative_profits, label='Cumulative Profit', ax=axs[1, 3])
            axs[1, 3].scatter(max_profit_time, max_profit, color='green', label='Max Profit')
            axs[1, 3].scatter(min_profit_time, min_profit, color='red', label='Min Profit')
            # Format dates on the x-axis
            axs[1, 3].xaxis.set_major_formatter(mdates.DateFormatter('%H', tz=zoneNY))
            axs[1, 3].set_title('Cumulative Profit Over Time')
            axs[1, 3].legend()
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
        sorted_trades = sorted([trade for trade in trades if trade.status == TradeStatus.CLOSED], 
                            key=lambda x: x.exit_time)
        cumulative_profits_sorted = np.cumsum([trade.profit for trade in sorted_trades])
        exit_times_sorted = [trade.exit_time for trade in sorted_trades if trade.exit_time is not None]
        axs[1, 3].plot(exit_times_sorted, cumulative_profits_sorted, color='blue')
        axs[1, 3].set_title('Cumulative Profit Over Time')
        axs[1, 3].set_xlabel('Time')
        axs[1, 3].set_ylabel('Cumulative Profit')
        axs[1, 3].xaxis.set_major_formatter(mdates.DateFormatter('%d', tz=zoneNY))

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

        # Plot 3: Heatmap of Profits
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
    
    # Plot 9: Profit/Loss Distribution Histogram
    sns.histplot(profits, bins=30, ax=axs[1, 1], kde=True, color='skyblue')
    axs[1, 1].set_title('Profit/Loss Distribution')
    axs[1, 1].set_xlabel('Profit/Loss')
    axs[1, 1].set_ylabel('Frequency')

    # Plot 5
    #    - pro 1 den: Position Size Distribution   
    #    - pro vice dnu:  Trade Duration vs. Profit/Loss
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

        # Plot 8: Trade Duration vs. Profit/Loss
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


    # Plot 6: Daily Relative Profit Chart
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

        # Plot 3: Heatmap of Profits
        sns.heatmap(heatmap_pivot, cmap='viridis', ax=axs[2, 0])
        axs[2, 0].set_title('Heatmap of Profits (based on Entry time)')
        axs[2, 0].set_xlabel('Hour of Day')
        axs[2, 0].set_ylabel('Day')

    # Plot 8: Profits Based on Hour of the Day (Entry)
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

    # Plot 9: Profits Based on Hour of the Day - based on Exit
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

    # Calculate profits by day of the week
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

# Example usage
# trades = [list of Trade objects]
if __name__ == '__main__':
    id_list = ["c3e31cb5-ddf9-467e-a932-2118f6844355"]
    generate_trading_report_image(runner_ids=id_list)
    # batch_id = "90973e57"
    # generate_trading_report_image(batch_id=batch_id)
