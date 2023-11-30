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

def ls_profit_distribution(runner_ids: List = None, batch_id: str = None, stream: bool = False) -> Tuple[int, Optional[BytesIO]]:
    try:
        # Load trades
        result, trades, days_cnt = load_trades(runner_ids, batch_id)

        # Proceed only if trades are successfully loaded
        if result == 0:
            # Filter trades based on direction and calculate profit
            long_trades = [trade for trade in trades if trade.direction == TradeDirection.LONG]
            short_trades = [trade for trade in trades if trade.direction == TradeDirection.SHORT]

            long_profits = [trade.profit for trade in long_trades]
            short_profits = [trade.profit for trade in short_trades]

            # Setting up dark mode for visualization with custom parameters
            plt.style.use('dark_background')
            custom_params = {
                'axes.titlesize': 9,
                'axes.labelsize': 8,
                'xtick.labelsize': 9,
                'ytick.labelsize': 9,
                'axes.labelcolor': '#a9a9a9',
                'axes.facecolor': '#121722',
                'axes.grid': False,
                'grid.color': 'gray',
                'grid.linestyle': '--',
                'grid.linewidth': 1,
                'xtick.color': '#a9a9a9',
                'ytick.color': '#a9a9a9',
                'axes.edgecolor': '#a9a9a9'
            }
            plt.rcParams.update(custom_params)

            plt.figure(figsize=(10, 6))
            sns.histplot(long_profits, color='blue', label='Long Trades', kde=True)
            sns.histplot(short_profits, color='red', label='Short Trades', kde=True)
            plt.xlabel('Profit')
            plt.ylabel('Number of Trades')
            plt.title('Profit Distribution by Trade Direction')
            plt.legend()

            # Handling the output
            if stream:
                img_stream = BytesIO()
                plt.savefig(img_stream, format='png')
                plt.close()
                img_stream.seek(0)
                return (0, img_stream)
            else:
                plt.savefig('profit_distribution.png')
                plt.close()
                return (0, None)
        else:
            return (-1, None)  # Error handling in case of unsuccessful trade loading

    except Exception as e:
        # Detailed error reporting
        return (-1, str(e) + format_exc())


# Example usage
# trades = [list of Trade objects]
if __name__ == '__main__':
    # id_list = ["e8938b2e-8462-441a-8a82-d823c6a025cb"]
    # generate_trading_report_image(runner_ids=id_list)
    batch_id = "73ad1866"
    res, val = ls_profit_distribution(batch_id=batch_id)
    #res, val  = find_optimal_cutoff(batch_id=batch_id, rem_outliers=True, file="optimal_cutoff_vectorized_nooutliers.png")

    print(res,val)