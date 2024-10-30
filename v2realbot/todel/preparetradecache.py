import pandas as pd
import numpy as np
from numba import jit
from alpaca.data.historical import StockHistoricalDataClient
from v2realbot.config import ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY, DATA_DIR
from alpaca.data.requests import StockTradesRequest
from v2realbot.enums.enums import AggType
import time
import os
from datetime import timedelta

from datetime import datetime
from v2realbot.utils.utils import parse_alpaca_timestamp, ltp, zoneNY, send_to_telegram, fetch_calendar_data
from v2realbot.loader.fetcher import prepare_trade_cache
import vectorbtpro as vbt
import argparse

"""
Python script prepares trade cache for specified symbols and date range.

Usually 1 day takes about 35s. It is stored in /tradescache/ directory as daily file keyed by symbol.

To run this script in the background with specific arguments:

```bash
# Running without forcing remote fetch
python3 prepare_cache.py --symbols BAC AAPL --day_start 2024-10-14 --day_stop 2024-10-18 &

# Running with force_remote set to True
python3 prepare_cache.py --symbols BAC AAPL --day_start 2024-10-14 --day_stop 2024-10-18 --force_remote &

```
"""
def main(symbols, day_start, day_stop, force_remote=False):
    # Convert day_start and day_stop to datetime objects in zoneNY
    day_start = zoneNY.localize(datetime.strptime(day_start, "%Y-%m-%d") + timedelta(hours=9, minutes=45))
    day_stop = zoneNY.localize(datetime.strptime(day_stop, "%Y-%m-%d") + timedelta(hours=15, minutes=1))
    
    prepare_trade_cache(symbols, day_start, day_stop, force_remote=force_remote)

if __name__ == "__main__":
    # Argument parser
    parser = argparse.ArgumentParser(description="Prepare cache with trades for specified symbols and date range.")
    parser.add_argument(
        "-s", "--symbols", nargs="+", required=True, help="List of symbols to prepare cache for (e.g., BAC AAPL MSFT)"
    )
    parser.add_argument(
        "-start", "--day_start", type=str, required=True, help="Start date in format YYYY-MM-DD"
    )
    parser.add_argument(
        "-end", "--day_stop", type=str, required=True, help="End date in format YYYY-MM-DD"
    )
    parser.add_argument(
        "-f", "--force_remote", action="store_true", help="Set this flag to force remote data fetch (default: False)"
    )
    args = parser.parse_args()

    # Run main function with parsed arguments
    main(args.symbols, args.day_start, args.day_stop, force_remote=args.force_remote)
