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
# Assuming Trade, TradeStatus, TradeDirection, TradeStoplossType classes are defined elsewhere

def profit_distribution_by_month(runner_ids: List = None, batch_id: str = None, stream: bool = False) -> Tuple[int, BytesIO or None]:
    try:
        # Load trades
        res, trades, days_cnt = load_trades(runner_ids, batch_id)
        if res != 0:
            raise Exception("Error in loading trades")

        # Filter trades by status and create DataFrame
        df_trades = pd.DataFrame([t.dict() for t in trades if t.status == 'closed'])

        # Extract month and year from trade exit time
        df_trades['month'] = df_trades['exit_time'].apply(lambda x: x.strftime('%Y-%m') if x is not None else None)

        # Group by direction and month, and sum the profits
        grouped = df_trades.groupby(['direction', 'month']).profit.sum().unstack(fill_value=0)

        # Visualization
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(10, 6))

        # Plotting
        grouped.T.plot(kind='bar', ax=ax)

        # Styling
        ax.set_title('Profit Distribution by Month: Long vs Short')
        ax.set_xlabel('Month')
        ax.set_ylabel('Total Profit')
        ax.legend(title='Trade Direction')

        # Adding footer
        plt.figtext(0.99, 0.01, f'Days Count: {days_cnt}', horizontalalignment='right')

        # Save or stream
        if stream:
            img = BytesIO()
            plt.savefig(img, format='png')
            plt.close()
            img.seek(0)
            return (0, img)
        else:
            plt.savefig('profit_distribution_by_month.png')
            plt.close()
            return (0, None)

    except Exception as e:
        # Detailed error reporting
        return (-1, str(e) + format_exc())

# Local debugging
if __name__ == '__main__':
    batch_id = "73ad1866"
    res, val = profit_distribution_by_month(batch_id=batch_id)
    print(res, val)