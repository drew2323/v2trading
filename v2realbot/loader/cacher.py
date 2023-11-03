from v2realbot.loader.aggregator import TradeAggregator, TradeAggregator2List, TradeAggregator2Queue
from alpaca.trading.requests import GetCalendarRequest
from alpaca.trading.client import TradingClient
from alpaca.data.live import StockDataStream
from v2realbot.config import ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY, DATA_DIR, OFFLINE_MODE
from alpaca.data.enums import DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest, StockBarsRequest, StockTradesRequest
from threading import Thread, current_thread
from v2realbot.utils.utils import parse_alpaca_timestamp, ltp, zoneNY, print
from v2realbot.utils.tlog import tlog
from datetime import datetime, timedelta, date
from threading import Thread
import asyncio
from msgpack.ext import Timestamp
from msgpack import packb
from pandas import to_datetime
import pickle
import os
from rich import print
import queue
from alpaca.trading.models import Calendar
from v2realbot.enums.enums import RecordType, StartBarAlign
from datetime import datetime, timedelta
from v2realbot.utils.utils import parse_alpaca_timestamp, ltp, Queue,is_open_hours,zoneNY
from queue import Queue
from rich import print
from v2realbot.enums.enums import Mode
import threading

class Cacher:  
    def __init__(self,
                 
                 rectype: RecordType = RecordType.BAR,
                 timeframe: int = 5,
                 minsize: int = 100,
                 update_ltp: bool = False,
                 align: StartBarAlign = StartBarAlign.ROUND,
                 mintick: int = 0,
                 exthours: bool = False):
#vstupuje seznam aggregatoru - obvykle 1 pro queue, 1 pro backtest engine
def get_cached_agg_data(agg_list, open, close):
    file_path = DATA_DIR + "/cache/"+populate_file_name(agg_list[0], open, close)

    if os.path.exists(file_path):
        ##denní file existuje
        #loadujeme ze souboru
        #pokud je start_time < trade < end_time 
            #odesíláme do queue
            #jinak pass
        with open (file_path, 'rb') as fp:
            agg_data = pickle.load(fp)
            print("Loading AGGREGATED DATA from CACHE", file_path)      

    return agg_data

def store_cache_agg_data(aggregator, open, close):
    pass
    #ulozi data do fajlu

def populate_file_name(aggregator, open, close):
    aggregated_file = aggregator.symbol + '-' + str(aggregator.rectype) + "-" + aggregator.timeframe + "-" + aggregator.minsize + "-" + aggregator.align + aggregator.mintick + str(aggregator.exthours) + '-' + str(int(open.timestamp())) + '-' + str(int(close.timestamp())) + '.cache'
    return aggregated_file