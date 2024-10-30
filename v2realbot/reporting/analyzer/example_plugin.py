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
from rich import print
from v2realbot.common.model import AnalyzerInputs
from v2realbot.common.model import TradeDirection, TradeStatus, Trade, TradeStoplossType
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
from v2realbot.reporting.load_trades import load_trades
from traceback import format_exc
# Assuming Trade, TradeStatus, TradeDirection, TradeStoplossType classes are defined elsewhere


def example_plugin(runner_ids: list = None, batch_id: str = None, stream: bool = False, rem_outliers:bool = False, file: str = "optimalcutoff.png",steps:int = 50):
    try:
        res, trades, days = load_trades(runner_ids, batch_id)    
        if res < 0:
            return (res, trades)

        cnt_max = days
        #in trades is list of Trades

            #print(trades)

        ##THIS IS how you can fetch historical data for given period and for given TimeFrame (if needed in future)
        # symbol = sada.symbol
        # #hour bars for backtested period
        # print(start_date,end_date)
        # bars= get_historical_bars(symbol, start_date, end_date, TimeFrame.Hour)
        # print("bars for given period",bars)
        # """Bars a dictionary with the following keys:
        #     * high: A list of high prices
        #     * low: A list of low prices
        #     * volume: A list of volumes
        #     * close: A list of close prices
        #     * hlcc4: A list of HLCC4 indicators
        #     * open: A list of open prices
        #     * time: A list of times in UTC (ISO 8601 format)
        #     * trades: A list of number of trades
        #     * resolution: A list of resolutions (all set to 'D')
        #     * confirmed: A list of booleans (all set to True)
        #     * vwap: A list of VWAP indicator
        #     * updated: A list of booleans (all set to True)
        #     * index: A list of integers (from 0 to the length of the list of daily bars)
        # """

        # Filter to only use trades with status 'CLOSED'
        closed_trades = [trade for trade in trades if trade.status == TradeStatus.CLOSED]

        #print(closed_trades)

        if len(closed_trades) == 0:
            return -1, "image generation no closed trades"
        
        #  # Group trades by date and calculate daily profits
        # trades_by_day = defaultdict(list)
        # for trade in trades:
        #     if trade.status == TradeStatus.CLOSED and trade.exit_time:
        #         trade_day = trade.exit_time.date()
        #         trades_by_day[trade_day].append(trade)

        # Precompute daily cumulative profits
        daily_cumulative_profits = defaultdict(list)
        for trade in trades:
            if trade.status == TradeStatus.CLOSED and trade.exit_time:
                day = trade.exit_time.date()
                daily_cumulative_profits[day].append(trade.profit)

        for day in daily_cumulative_profits:
            daily_cumulative_profits[day] = np.cumsum(daily_cumulative_profits[day])


        if rem_outliers:
            # Remove outliers based on z-scores
            def remove_outliers(cumulative_profits):
                all_profits = [profit[-1] for profit in cumulative_profits.values() if len(profit) > 0]
                z_scores = zscore(all_profits)
                print(z_scores)
                filtered_profits = {}
                for day, profits in cumulative_profits.items():
                    if len(profits) > 0:
                        day_z_score = z_scores[list(cumulative_profits.keys()).index(day)]
                        if abs(day_z_score) < 3:  # Adjust threshold as needed
                            filtered_profits[day] = profits
                return filtered_profits

            daily_cumulative_profits = remove_outliers(daily_cumulative_profits)

        # OPT2 Calculate profit_range and loss_range based on all cumulative profits
        all_cumulative_profits = np.concatenate([profits for profits in daily_cumulative_profits.values()])
        max_cumulative_profit = np.max(all_cumulative_profits)
        min_cumulative_profit = np.min(all_cumulative_profits)
        profit_range = (0, max_cumulative_profit) if max_cumulative_profit > 0 else (0, 0)
        loss_range = (min_cumulative_profit, 0) if min_cumulative_profit < 0 else (0, 0)

        print("Calculated ranges", profit_range, loss_range)

        num_points = steps  # Adjust for speed vs accuracy
        profit_cutoffs = np.linspace(*profit_range, num_points)
        loss_cutoffs = np.linspace(*loss_range, num_points)

        # OPT 3Statically define ranges for loss and profit cutoffs
        # profit_range = (0, 1000)  # Adjust based on your data
        # loss_range = (-1000, 0)
        # num_points = 20  # Adjust for speed vs accuracy

        profit_cutoffs = np.linspace(*profit_range, num_points)
        loss_cutoffs = np.linspace(*loss_range, num_points)

        total_profits_matrix = np.zeros((len(profit_cutoffs), len(loss_cutoffs)))

        for i, profit_cutoff in enumerate(profit_cutoffs):
            for j, loss_cutoff in enumerate(loss_cutoffs):
                total_profit = 0
                for daily_profit in daily_cumulative_profits.values():
                    cutoff_index = np.where((daily_profit >= profit_cutoff) | (daily_profit <= loss_cutoff))[0]
                    if cutoff_index.size > 0:
                        total_profit += daily_profit[cutoff_index[0]]
                    else:
                        total_profit += daily_profit[-1] if daily_profit.size > 0 else 0
                total_profits_matrix[i, j] = total_profit

        # Find the optimal combination
        optimal_idx = np.unravel_index(total_profits_matrix.argmax(), total_profits_matrix.shape)
        optimal_profit_cutoff = profit_cutoffs[optimal_idx[0]]
        optimal_loss_cutoff = loss_cutoffs[optimal_idx[1]]
        max_profit = total_profits_matrix[optimal_idx]

        # Plotting
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
        plt.figure(figsize=(10, 8))
        sns.heatmap(total_profits_matrix, xticklabels=np.rint(loss_cutoffs).astype(int), yticklabels=np.rint(profit_cutoffs).astype(int), cmap="viridis")
        plt.xticks(rotation=90)  # Rotate x-axis labels to be vertical
        plt.yticks(rotation=0)   # Keep y-axis labels horizontal
        plt.gca().invert_yaxis()
        plt.gca().invert_xaxis()
        plt.suptitle(f"Total Profit for Combinations of Profit/Loss Cutoffs ({cnt_max})", fontsize=16)
        plt.title(f"Optimal Profit Cutoff: {optimal_profit_cutoff:.2f}, Optimal Loss Cutoff: {optimal_loss_cutoff:.2f}, Max Profit: {max_profit:.2f}", fontsize=10)
        plt.xlabel("Loss Cutoff")
        plt.ylabel("Profit Cutoff")

        if stream is False:
            plt.savefig(file) 
            plt.close()
            print(f"Optimal Profit Cutoff(rem_outliers:{rem_outliers}): {optimal_profit_cutoff}, Optimal Loss Cutoff: {optimal_loss_cutoff}, Max Profit: {max_profit}")
            return 0, None
        else:
            # Return the image as a BytesIO stream
            img_stream = BytesIO()
            plt.savefig(img_stream, format='png')
            plt.close()
            img_stream.seek(0)  # Rewind the stream to the beginning
            return 0, img_stream

    except Exception as e:
        # Detailed error reporting
        return (-1, str(e) + format_exc())

# Example usage
# trades = [list of Trade objects]
if __name__ == '__main__':
    # id_list = ["e8938b2e-8462-441a-8a82-d823c6a025cb"]
    # generate_trading_report_image(runner_ids=id_list)
    batch_id = "73ad1866"
    res, val = example_plugin(batch_id=batch_id, file="optimal_cutoff_vectorized.png",steps=20)
    #res, val  = find_optimal_cutoff(batch_id=batch_id, rem_outliers=True, file="optimal_cutoff_vectorized_nooutliers.png")

    print(res,val)