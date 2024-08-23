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
from typing import Tuple, Optional, List
from v2realbot.common.model import TradeDirection, TradeStatus, Trade, TradeStoplossType

def load_trades(runner_ids: List = None, batch_id: str = None) -> Tuple[int, List[Trade], int]:
    if runner_ids is None and batch_id is None:
        return -2, f"runner_id or batch_id must be present", 0

    if batch_id is not None:
        res, runner_ids =cs.get_archived_runnerslist_byBatchID(batch_id)

        if res != 0:
            print(f"no batch {batch_id} found")
            return -1, f"no batch {batch_id} found", 0

    #DATA PREPARATION
    trades = []
    cnt_max = len(runner_ids) 
    cnt = 0
    #zatim zjistujeme start a end z min a max dni - jelikoz muze byt i seznam runner_ids a nejenom batch
    end_date = None
    start_date = None
    for id in runner_ids:
        cnt += 1
        #get runner
        res, sada =cs.get_archived_runner_header_byID(id)
        if res != 0:
            print(f"no runner {id} found")
            return -1, f"no runner {id} found", 0
        
        #print("archrunner")
        #print(sada)
    
        if cnt == 1:
            start_date = sada.bt_from if sada.mode in [Mode.BT,Mode.PREP] else sada.started
        if cnt == cnt_max:
            end_date = sada.bt_to if sada.mode in [Mode.BT or Mode.PREP] else sada.stopped
        # Parse trades

        trades_dicts =  sada.metrics["prescr_trades"]

        for trade_dict in trades_dicts:
            trade_dict['last_update'] = datetime.fromtimestamp(trade_dict.get('last_update')).astimezone(zoneNY) if trade_dict['last_update'] is not None else None
            trade_dict['entry_time'] = datetime.fromtimestamp(trade_dict.get('entry_time')).astimezone(zoneNY) if trade_dict['entry_time'] is not None else None
            trade_dict['exit_time'] = datetime.fromtimestamp(trade_dict.get('exit_time')).astimezone(zoneNY) if trade_dict['exit_time'] is not None else None
            trades.append(Trade(**trade_dict))
    return 0, trades, cnt_max