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
from typing import Tuple, Optional, List
from traceback import format_exc
# Assuming Trade, TradeStatus, TradeDirection, TradeStoplossType classes are defined elsewhere
def profit_sum_by_hour(runner_ids: list = None, batch_id: str = None, stream: bool = False, group_by: str = 'entry_time'):
    try:
        # Load trades
        res, trades, days_cnt = load_trades(runner_ids, batch_id)
        if res != 0:
            raise Exception("Error in loading trades")

        # Filter closed trades
        closed_trades = [trade for trade in trades if trade.status == 'closed']
        total_closed_trades = len(closed_trades)

        # Extract hour and profit/loss based on group_by parameter
        hourly_profit_loss = {}
        hourly_trade_count = {}
        for trade in closed_trades:
            # Determine the time attribute to group by
            time_attribute = getattr(trade, group_by) if group_by in ['entry_time', 'exit_time'] else trade.entry_time
            if time_attribute:
                hour = time_attribute.hour
                hourly_profit_loss.setdefault(hour, []).append(trade.profit)
                hourly_trade_count[hour] = hourly_trade_count.get(hour, 0) + 1

        # Aggregate profits and losses by hour
        hourly_aggregated = {hour: sum(profits) for hour, profits in hourly_profit_loss.items()}

        # Visualization
        hours = list(hourly_aggregated.keys())
        profits = list(hourly_aggregated.values())
        trade_counts = [hourly_trade_count.get(hour, 0) for hour in hours]

        plt.style.use('dark_background')
        colors = ['blue' if profit >= 0 else 'orange' for profit in profits]
        bars = plt.bar(hours, profits, color=colors)

        # Make the grid subtler
        plt.grid(True, color='gray', linestyle='--', linewidth=0.5, alpha=0.5)

        plt.xlabel('Hour of Day')
        plt.ylabel('Profit/Loss')
        plt.title(f'Distribution of Profit/Loss Sum by Hour ({group_by.replace("_", " ").title()})')

        # Add trade count and percentage inside the bars
        for bar, count in zip(bars, trade_counts):
            height = bar.get_height()
            percent = (count / total_closed_trades) * 100
            # Position the text inside the bars
            position = height - 20 if height > 0 else height + 20
            plt.text(bar.get_x() + bar.get_width() / 2., position,
                     f'{count} Trades\n({percent:.1f}%)', ha='center', va='center', color='white', fontsize=9)

        # Adjust footer position and remove large gap
        footer_text = f'Days Count: {days_cnt} | Parameters: {{"runner_ids": {len(runner_ids) if runner_ids is not None else None}, "batch_id": {batch_id}, "stream": {stream}, "group_by": "{group_by}"}}'
        plt.gcf().subplots_adjust(bottom=0.2)
        plt.figtext(0.5, 0.02, footer_text, ha="center", fontsize=8, color='gray', bbox=dict(facecolor='black', edgecolor='none', pad=3.0))

        # Output
        if stream:
            img = BytesIO()
            plt.savefig(img, format='png', bbox_inches='tight')
            plt.close()
            img.seek(0)
            return (0, img)
        else:
            plt.savefig('profit_loss_by_hour.png', bbox_inches='tight')
            plt.close()
            return (0, None)

    except Exception as e:
        # Detailed error reporting
        plt.close()
        return (-1, str(e))

# Local debugging
if __name__ == '__main__':
    batch_id = "9e990e4b"
    # Example usage with group_by parameter
    res, val = profit_sum_by_hour(batch_id=batch_id, group_by='exit_time')
    print(res, val)