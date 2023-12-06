import matplotlib
import matplotlib.dates as mdates
matplotlib.use('Agg')  # Set the Matplotlib backend to 'Agg'
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import seaborn as sns
import pandas as pd
from datetime import datetime
from typing import List
from enum import Enum
import numpy as np
import v2realbot.controller.services as cs
from rich import print
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
from v2realbot.reporting.load_trades import load_trades
from typing import Tuple, Optional, List
from traceback import format_exc
import pandas as pd

def daily_profit_distribution(runner_ids: list = None, batch_id: str = None, stream: bool = False):
    try:
        res, trades, days_cnt = load_trades(runner_ids, batch_id)
        if res != 0:
            raise Exception("Error in loading trades")
        
        #print(trades)

        # Convert list of Trade objects to DataFrame
        trades_df = pd.DataFrame([t.__dict__ for t in trades if t.status == "closed"])

        # Ensure 'exit_time' is a datetime object and make it timezone-naive if necessary
        trades_df['exit_time'] = pd.to_datetime(trades_df['exit_time']).dt.tz_convert(zoneNY)
        trades_df['date'] = trades_df['exit_time'].dt.date

        daily_profit = trades_df.groupby(['date', 'direction']).profit.sum().unstack(fill_value=0)
        #print("dp",daily_profit)
        daily_cumulative_profit = trades_df.groupby('date').profit.sum().cumsum()

        # Create the plot
        fig, ax1 = plt.subplots(figsize=(10, 6))

        # Bar chart for daily profit composition
        daily_profit.plot(kind='bar', stacked=True, ax=ax1, color=['green', 'red'], zorder=2)
        ax1.set_ylabel('Daily Profit')
        ax1.set_xlabel('Date')
        #ax1.xaxis.set_major_locator(MaxNLocator(10)) 

        # Line chart for cumulative daily profit
        #ax2 = ax1.twinx()
        #print(daily_cumulative_profit)
        #print(daily_cumulative_profit.index)
        #ax2.plot(daily_cumulative_profit.index, daily_cumulative_profit, color='yellow', linestyle='-', linewidth=2, zorder=3)
        #ax2.set_ylabel('Cumulative Profit')

        # Setting the secondary y-axis range dynamically based on cumulative profit values
        # ax2.set_ylim(daily_cumulative_profit.min() - (daily_cumulative_profit.std() * 2),
        #              daily_cumulative_profit.max() + (daily_cumulative_profit.std() * 2))

        # Dark mode settings
        ax1.set_facecolor('black')
        # ax1.grid(True)
        #ax2.set_facecolor('black')
        fig.patch.set_facecolor('black')
        ax1.tick_params(colors='white')
        #ax2.tick_params(colors='white')
        # ax1.xaxis_date() 
        # ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.', tz=zoneNY))
        ax1.tick_params(axis='x', rotation=45)

        # Footer
        footer_text = f'Days Count: {days_cnt} | Parameters: {{"runner_ids": {len(runner_ids) if runner_ids is not None else None}, "batch_id": {batch_id}, "stream": {stream}}}'
        plt.figtext(0.5, 0.01, footer_text, wrap=True, horizontalalignment='center', fontsize=8, color='white')

        # Save or stream the plot
        if stream:
            img_stream = BytesIO()
            plt.savefig(img_stream, format='png', bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
            img_stream.seek(0)
            plt.close(fig)
            return (0, img_stream)
        else:
            plt.savefig(f'{__name__}.png', bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
            plt.close(fig)
            return (0, None)

    except Exception as e:
        # Detailed error reporting
        return (-1, str(e) + format_exc())
# Local debugging
if __name__ == '__main__':
    batch_id = "6f9b012c"
    res, val = daily_profit_distribution(batch_id=batch_id)
    print(res, val)
