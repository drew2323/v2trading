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


def summarize_trade_metrics(runner_ids: list = None, batch_id: str = None, stream: bool = False):
    try:
        res, trades, days_cnt = load_trades(runner_ids, batch_id)
        if res != 0:
            raise Exception("Error in loading trades")
        
        closed_trades = [trade for trade in trades if trade.status == "closed"]

        # Calculate metrics
        metrics = calculate_metrics(closed_trades)

        # Generate and process image
        img_stream = generate_table_image(metrics)

        # Add footer to image
        #img_stream = add_footer_to_image(img_stream, days_cnt, runner_ids, batch_id, stream)

        # Output handling
        if stream:
            img_stream.seek(0)
            return (0, img_stream)
        else:
            with open(f'summarize_trade_metrics_{batch_id}.png', 'wb') as f:
                f.write(img_stream.getbuffer())
            return (0, None)

    except Exception as e:
        # Detailed error reporting
        return (-1, str(e)+format_exc())

def calculate_metrics(closed_trades):
    if not closed_trades:
        return {}

    total_profit = sum(trade.profit for trade in closed_trades)
    max_profit = max(trade.profit for trade in closed_trades)
    min_profit = min(trade.profit for trade in closed_trades)
    total_trades = len(closed_trades)
    long_trades = sum(1 for trade in closed_trades if trade.direction == "long")
    short_trades = sum(1 for trade in closed_trades if trade.direction == "short")

    # Daily Metrics Calculation
    trades_by_day = {}
    for trade in closed_trades:
        day = trade.entry_time.date() if trade.entry_time else None
        if day:
            trades_by_day.setdefault(day, []).append(trade)

    avg_trades_per_day = sum(len(trades) for trades in trades_by_day.values()) / len(trades_by_day)
    avg_long_trades_per_day = sum(sum(1 for trade in trades if trade.direction == "long") for trades in trades_by_day.values()) / len(trades_by_day)
    avg_short_trades_per_day = sum(sum(1 for trade in trades if trade.direction == "short") for trades in trades_by_day.values()) / len(trades_by_day)

    return {
        "Average Profit": total_profit / total_trades,
        "Maximum Profit": max_profit,
        "Minimum Profit": min_profit,
        "Total Number of Trades": total_trades,
        "Number of Long Trades": long_trades,
        "Number of Short Trades": short_trades,
        "Average Trades per Day": avg_trades_per_day,
        "Average Long Trades per Day": avg_long_trades_per_day,
        "Average Short Trades per Day": avg_short_trades_per_day
    }

def generate_table_image(metrics):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axis('tight')
    ax.axis('off')

    # Convert metrics to a 2D array where each row is a list
    cell_text = [[value] for value in metrics.values()]

    # Convert dict keys to a list for row labels
    row_labels = list(metrics.keys())

    ax.table(cellText=cell_text,
             rowLabels=row_labels,
             loc='center')

    plt.subplots_adjust(left=0.2, top=0.8)
    plt.title("Trade Metrics Summary", color='white')

    img_stream = BytesIO()
    plt.savefig(img_stream, format='png', bbox_inches='tight', pad_inches=0.1, facecolor='black')
    plt.close(fig)
    return img_stream

def add_footer_to_image(img_stream, days_cnt, runner_ids, batch_id, stream):
    # Implementation for adding a footer to the image
    # This can be done using PIL (Python Imaging Library) or other image processing libraries
    # For simplicity, I'm leaving this as a placeholder
    pass

# Local debugging
if __name__ == '__main__':
    batch_id = "73ad1866"
    res, val = summarize_trade_metrics(batch_id=batch_id)
    print(res, val)
