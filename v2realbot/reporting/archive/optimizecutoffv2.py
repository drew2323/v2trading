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
from v2realbot.common.PrescribedTradeModel import TradeDirection, TradeStatus, Trade, TradeStoplossType
from v2realbot.utils.utils import isrising, isfalling,zoneNY, price2dec, safe_get#, print
from pathlib import Path
from v2realbot.config import WEB_API_KEY, DATA_DIR, MEDIA_DIRECTORY
from v2realbot.enums.enums import RecordType, StartBarAlign, Mode, Account, OrderSide
from io import BytesIO
from v2realbot.utils.historicals import get_historical_bars
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from collections import defaultdict
# Assuming Trade, TradeStatus, TradeDirection, TradeStoplossType classes are defined elsewhere

#LOSS and PROFIT without GRAPH
def find_optimal_cutoff(runner_ids: list = None, batch_id: str = None, stream: bool = False):
    
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
            return -1, f"no runner {id} found"
        
        print("archrunner")
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

        #print(trades)

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

    print(closed_trades)

    if len(closed_trades) == 0:
        return -1, "image generation no closed trades"
    
     # Group trades by date and calculate daily profits
    trades_by_day = defaultdict(list)
    for trade in trades:
        if trade.status == TradeStatus.CLOSED and trade.exit_time:
            trade_day = trade.exit_time.date()
            trades_by_day[trade_day].append(trade)

    # Define ranges for loss and profit cutoffs
    min_profit = 50
    max_profit = 700  # Set an upper bound based on your data
    profit_cutoffs = np.linspace(min_profit, max_profit, 50)  # Adjust number of points as needed

    min_loss = -50
    max_loss = -700  # Assuming losses are negative values
    loss_cutoffs = np.linspace(min_loss, max_loss, 50)

    def calculate_total_profit(profit_cutoff, loss_cutoff):
        total_profit = 0
        for day, day_trades in trades_by_day.items():
            daily_profit = 0
            for trade in day_trades:
                daily_profit += trade.profit
                if daily_profit >= profit_cutoff or daily_profit <= loss_cutoff:
                    break
            total_profit += daily_profit
        return total_profit

    # Evaluate each combination of cutoffs
    optimal_profit_cutoff = max_profit
    optimal_loss_cutoff = min_loss
    max_total_profit = float('-inf')

    for profit_cutoff in profit_cutoffs:
        for loss_cutoff in loss_cutoffs:
            total_profit = calculate_total_profit(profit_cutoff, loss_cutoff)
            if total_profit > max_total_profit:
                max_total_profit = total_profit
                optimal_profit_cutoff = profit_cutoff
                optimal_loss_cutoff = loss_cutoff

    print(f"Optimal Profit Cutoff: {optimal_profit_cutoff}, Optimal Loss Cutoff: {optimal_loss_cutoff}, Max Profit: {max_total_profit}")

    # Optional: Plot the results or return them for further analysis

    return optimal_profit_cutoff, optimal_loss_cutoff, max_total_profit

    # # Plotting
    # plt.figure(figsize=(10, 6))
    # plt.plot(list(cutoff_profits.keys()), list(cutoff_profits.values()), label='Total Profit')
    # plt.scatter(optimal_cutoff, max_profit, color='red', label='Optimal Cutoff')
    # plt.title('Optimal Intra-Day Profit Cutoff Analysis')
    # plt.xlabel('Profit Cutoff')
    # plt.ylabel('Total Profit')
    # plt.legend()
    # plt.grid(True)
    # plt.savefig('optimal_cutoff.png') 

    # return optimal_cutoff, max_profit
  
# Example usage
# trades = [list of Trade objects]
if __name__ == '__main__':
    # id_list = ["e8938b2e-8462-441a-8a82-d823c6a025cb"]
    # generate_trading_report_image(runner_ids=id_list)
    batch_id = "c76b4414"
    optimal_profit_cutoff, optimal_loss_cutoff, max_profit  = find_optimal_cutoff(batch_id=batch_id)
    print(f"Optimal Profit Cutoff: {optimal_profit_cutoff}, Optimal Loss Cutoff: {optimal_loss_cutoff}, Max Profit: {max_profit}")