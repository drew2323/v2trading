from typing import Any, List, Tuple
from uuid import UUID, uuid4
import pickle
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockTradesRequest, StockBarsRequest
from alpaca.data.enums import DataFeed
from alpaca.data.timeframe import TimeFrame
from v2realbot.strategy.base import StrategyState
from v2realbot.enums.enums import RecordType, StartBarAlign, Mode, Account, OrderSide
from v2realbot.common.model import RunManagerRecord, StrategyInstance, RunDay, StrategyInstance, Runner, RunRequest, RunArchive, RunArchiveView, RunArchiveViewPagination, RunArchiveDetail, RunArchiveChange, Bar, TradeEvent, TestList, Intervals, ConfigItem, InstantIndicator, DataTablesRequest
from v2realbot.utils.utils import validate_and_format_time, AttributeDict, zoneNY, zonePRG, safe_get, dict_replace_value, Store, parse_toml_string, json_serial, is_open_hours, send_to_telegram, concatenate_weekdays, transform_data
from v2realbot.utils.ilog import delete_logs
from v2realbot.common.PrescribedTradeModel import Trade, TradeDirection, TradeStatus, TradeStoplossType
from datetime import datetime
from v2realbot.loader.trade_offline_streamer import Trade_Offline_Streamer
from threading import Thread, current_thread, Event, enumerate
from v2realbot.config import STRATVARS_UNCHANGEABLES, ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY, ACCOUNT1_LIVE_API_KEY, ACCOUNT1_LIVE_SECRET_KEY, DATA_DIR,BT_FILL_CONS_TRADES_REQUIRED,BT_FILL_LOG_SURROUNDING_TRADES,BT_FILL_CONDITION_BUY_LIMIT,BT_FILL_CONDITION_SELL_LIMIT, GROUP_TRADES_WITH_TIMESTAMP_LESS_THAN, MEDIA_DIRECTORY, RUNNER_DETAIL_DIRECTORY, OFFLINE_MODE
import importlib
from alpaca.trading.requests import GetCalendarRequest
from alpaca.trading.client import TradingClient
#from alpaca.trading.models import Calendar
from queue import Queue
from tinydb import TinyDB, Query, where
from tinydb.operations import set
import orjson
import numpy as np
from rich import print
import pandas as pd
from traceback import format_exc
from datetime import timedelta, time
from threading import Lock
import v2realbot.common.db as db
from sqlite3 import OperationalError, Row
import v2realbot.strategyblocks.indicators.custom as ci
from v2realbot.strategyblocks.inits.init_indicators import initialize_dynamic_indicators
from v2realbot.strategyblocks.indicators.indicators_hub import populate_dynamic_indicators
from v2realbot.interfaces.backtest_interface import BacktestInterface
import os
import v2realbot.reporting.metricstoolsimage as mt
import gzip
import os
import msgpack
import v2realbot.controller.services as cs
import v2realbot.scheduler.ap_scheduler as aps

# Functions for your 'run_manager' table

# CREATE TABLE "run_manager" (
# 	"moddus"	TEXT NOT NULL,
# 	"id"	varchar(32),
# 	"strat_id"	varchar(32) NOT NULL,
# 	"symbol"	TEXT,
# 	"account"	TEXT NOT NULL,
# 	"mode"	TEXT NOT NULL,
# 	"note"	TEXT,
# 	"ilog_save"	BOOLEAN,
# 	"bt_from"	TEXT,
# 	"bt_to"	TEXT,
# 	"weekdays_filter"	TEXT,
# 	"batch_id"	TEXT,
# 	"start_time"	TEXT NOT NULL,
# 	"stop_time"	TEXT NOT NULL,
# 	"status"	TEXT NOT NULL,
# 	"last_processed"	TEXT,
# 	"history"	TEXT,
# 	"valid_from"	TEXT,
# 	"valid_to"	TEXT,
# 	"testlist_id"	TEXT,
# 	"runner_id"	varchar2(32),
# 	PRIMARY KEY("id")
# )

# CREATE INDEX idx_moddus ON run_manager (moddus);
# CREATE INDEX idx_status ON run_manager (status);
# CREATE INDEX idx_status_moddus ON run_manager (status, moddus);
# CREATE INDEX idx_valid_from_to ON run_manager (valid_from, valid_to);
# CREATE INDEX idx_stopped_batch_id ON runner_header (stopped, batch_id); 
# CREATE INDEX idx_search_value ON runner_header (strat_id, batch_id);


##weekdays are stored as comma separated values
# Fetching (assume 'weekdays' field is a comma-separated string)
# weekday_str = record['weekdays']
# weekdays = [int(x) for x in weekday_str.split(',')]

# # ... logic to check whether today's weekday is in 'weekdays'

# # Storing 
# weekdays = [1, 2, 5]  # Example 
# weekday_str = ",".join(str(x) for x in weekdays)
# update_data = {'weekdays': weekday_str} 
# # ... use in an SQL UPDATE statement

        # for row in records:
        #     row['weekdays_filter'] = [int(x) for x in row['weekdays_filter'].split(',')] if row['weekdays_filter'] else []


#get stratin info return
# strat : StrategyInstance = None
# result, strat = cs.get_stratin("625760ac-6376-47fa-8989-1e6a3f6ab66a")
# if result == 0:
#     print(strat)
# else:
#     print("Error:", strat)


# Fetch all
#result, records = fetch_all_run_manager_records()

#TODO zvazit rozsireni vystupu o strat_status (running/stopped)


def fetch_all_run_manager_records() -> list[RunManagerRecord]:
    conn = db.pool.get_connection()
    try:
        conn.row_factory = Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM run_manager')
        rows = cursor.fetchall()
        results = []
        #Transform row to object
        for row in rows:
            #add transformed object into result list
            results.append(db.row_to_runmanager(row))

        return 0, results
    finally:
        conn.row_factory = None
        db.pool.release_connection(conn)

# Fetch by strategy_id
# result, record = fetch_run_manager_record_by_id('625760ac-6376-47fa-8989-1e6a3f6ab66a')
def fetch_run_manager_record_by_id(strategy_id) -> RunManagerRecord:
    conn = db.pool.get_connection()
    try:
        conn.row_factory = Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM run_manager WHERE id = ?', (str(strategy_id),))
        row = cursor.fetchone()
        if row is None:
            return -2, "not found"
        else:
            return 0, db.row_to_runmanager(row)

    except Exception as e:
        print("ERROR while fetching all records:", str(e) + format_exc())
        return -2, str(e) + format_exc()
    finally:
        conn.row_factory = None
        db.pool.release_connection(conn)

def add_run_manager_record(new_record: RunManagerRecord):
    #validation/standardization of time
    new_record.start_time = validate_and_format_time(new_record.start_time)
    if new_record.start_time is None:
        return -2, f"Invalid start_time format {new_record.start_time}"

    if new_record.stop_time is not None:
        new_record.stop_time = validate_and_format_time(new_record.stop_time)
        if new_record.stop_time is None:
            return -2, f"Invalid stop_time format {new_record.stop_time}"

    conn = db.pool.get_connection()
    try:

        strat : StrategyInstance = None
        result, strat = cs.get_stratin(id=str(new_record.strat_id))
        if result == 0:
            new_record.symbol = strat.symbol
        else:
            return -1, f"Strategy {new_record.strat_id} not found"

        cursor = conn.cursor()

        # Construct a suitable INSERT query based on your RunManagerRecord fields
        insert_query = """
            INSERT INTO run_manager (moddus, id, strat_id, symbol,account, mode, note,ilog_save,
                                    bt_from, bt_to, weekdays_filter, batch_id,
                                    start_time, stop_time, status, last_processed,
                                    history, valid_from, valid_to, testlist_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) 
        """
        values = [
            new_record.moddus, str(new_record.id), str(new_record.strat_id), new_record.symbol, new_record.account, new_record.mode, new_record.note,
            int(new_record.ilog_save),
            new_record.bt_from.isoformat() if new_record.bt_from is not None else None,
            new_record.bt_to.isoformat() if new_record.bt_to is not None else None,
            ",".join(str(x) for x in new_record.weekdays_filter) if new_record.weekdays_filter else None,
            new_record.batch_id, new_record.start_time, 
            new_record.stop_time, new_record.status,
            new_record.last_processed.isoformat() if new_record.last_processed is not None else None,
            new_record.history,
            new_record.valid_from.isoformat() if new_record.valid_from is not None else None,
            new_record.valid_to.isoformat() if new_record.valid_to is not None else None,
            new_record.testlist_id
        ]
        db.execute_with_retry(cursor, insert_query, values)
        conn.commit()

        #Add APS scheduler job refresh
        res, result = aps.initialize_jobs()
        if res < 0:
            return -2, f"Error initializing jobs: {res} {result}"

        return 0, new_record.id  # Assuming success, you might return something more descriptive
    except Exception as e:
        print("ERROR while adding record:", str(e) + format_exc())
        return -2, str(e) + format_exc()
    finally:
        db.pool.release_connection(conn)

# Update (example)
# update_data = {'last_started': '2024-02-13 10:35:00'}  
# result, message = update_run_manager_record('625760ac-6376-47fa-8989-1e6a3f6ab66a', update_data)
def update_run_manager_record(record_id, updated_record: RunManagerRecord):
    #validation/standardization of time
    updated_record.start_time = validate_and_format_time(updated_record.start_time)
    if updated_record.start_time is None:
        return -2, f"Invalid start_time format {updated_record.start_time}"

    if updated_record.stop_time is not None:
        updated_record.stop_time = validate_and_format_time(updated_record.stop_time)
        if updated_record.stop_time is None:
            return -2, f"Invalid stop_time format {updated_record.stop_time}"

    conn = db.pool.get_connection()
    try:
        cursor = conn.cursor()

        #strategy lookup check, if strategy still exists
        strat : StrategyInstance = None
        result, strat = cs.get_stratin(id=str(updated_record.strat_id))
        if result == 0:
            updated_record.symbol = strat.symbol
        else:
            return -1, f"Strategy {updated_record.strat_id} not found"

        #remove values with None, so they are not updated
        #updated_record_dict = updated_record.dict(exclude_none=True)

        # Construct update query and handle weekdays conversion
        update_query = 'UPDATE run_manager SET '
        update_params = []
        for key, value in updated_record.dict().items():  # Iterate over model attributes
            if key in ['id', 'strat_running']:  # Skip updating the primary key
                continue
            update_query += f"{key} = ?, "
            if key == "ilog_save":
                value = int(value)
            elif key in ["strat_id", "runner_id"]:
                value = str(value) if value else None
            elif key == "weekdays_filter":
                value = ",".join(str(x) for x in value) if value else None
            elif key in ['valid_from', 'valid_to', 'bt_from', 'bt_to', 'last_processed']:
                value = value.isoformat() if value else None
            update_params.append(value)
        # if 'weekdays_filter' in updated_record.dict():  
        #     updated_record.weekdays_filter = ",".join(str(x) for x in updated_record.weekdays_filter)
        update_query = update_query[:-2]  # Remove trailing comma and space
        update_query += ' WHERE id = ?'
        update_params.append(str(record_id))

        db.execute_with_retry(cursor, update_query, update_params)
        #cursor.execute(update_query, update_params)
        conn.commit()

        #Add APS scheduler job refresh
        res, result = aps.initialize_jobs()
        if res < 0:
            return -2, f"Error initializing jobs: {res} {result}"

    except Exception as e:
        print("ERROR while updating record:", str(e) + format_exc())
        return -2, str(e) + format_exc()
    finally:
        db.pool.release_connection(conn)
    return 0, record_id

# result, message = delete_run_manager_record('625760ac-6376-47fa-8989-1e6a3f6ab66a')
def delete_run_manager_record(record_id):
    conn = db.pool.get_connection()
    try:
        cursor = conn.cursor()
        db.execute_with_retry(cursor, 'DELETE FROM run_manager WHERE id = ?', (str(record_id),))
        #cursor.execute('DELETE FROM run_manager WHERE id = ?', (str(strategy_id),))
        conn.commit()
    except Exception as e:
        print("ERROR while deleting record:", str(e) + format_exc())
        return -2, str(e) + format_exc()
    finally:
        db.pool.release_connection(conn)
    return 0, record_id

def fetch_scheduled_candidates_for_start_and_stop(market_datetime_now, market) -> tuple[int, dict]:
    """
    Fetches all active records from the 'run_manager' table where the mode is 'schedule'. It checks if the current 
    time in the America/New_York timezone is within the operational intervals specified by 'start_time' and 'stop_time' 
    for each record. This function is designed to correctly handle scenarios where the operational interval crosses 
    midnight, as well as intervals contained within a single day.

    The function localizes 'valid_from', 'valid_to', 'start_time', and 'stop_time' using the 'zoneNY' timezone object 
    for accurate comparison with the current time. 

    Parameters:
        market_datetime_now (datetime): The current date and time in the America/New_York timezone.
        market (str): The market identifier.

    Returns:
        Tuple[int, dict]: A tuple where the first element is a status code (0 for success, -2 for error), and the 
        second element is a dictionary. This dictionary has keys 'start' and 'stop', each containing a list of 
        RunManagerRecord objects meeting the respective criteria. If an error occurs, the second element is a 
        descriptive error message.

    Note:
        - This function assumes that the 'zoneNY' pytz timezone object is properly defined and configured to represent 
          the America/New York timezone.
        - It also assumes that the 'run_manager' table exists in the database with the required columns.
        - 'start_time' and 'stop_time' are expected to be strings representing times in 24-hour format.
        - If 'valid_from', 'valid_to', 'start_time', or 'stop_time' are NULL in the database, they are considered as 
          having unlimited boundaries.
    
    Pozor: je jeste jeden okrajovy pripad, kdy by to nemuselo zafungovat: kdyby casy byly nastaveny pro
    beh strategie pres pulnoc, ale zapla by se pozdeji az po pulnoci
    (https://chat.openai.com/c/3c77674a-8a2c-45aa-afbd-ab140f473e07)

    """
    conn = db.pool.get_connection()
    try:
        conn.row_factory = Row
        cursor = conn.cursor()

        # Get current datetime in America/New York timezone
        market_datetime_now_str = market_datetime_now.strftime('%Y-%m-%d %H:%M:%S')
        current_time_str = market_datetime_now.strftime('%H:%M')
        print("current_market_datetime_str:", market_datetime_now_str)
        print("current_time_str:", current_time_str)

        # Select also supports scenarios where strategy runs overnight
        # SQL query to fetch records with active status and date constraints for both start and stop times
        query = """
        SELECT *,
        CASE 
            WHEN start_time <= stop_time AND (? >= start_time AND ? < stop_time) OR
                 start_time > stop_time AND (? >= start_time OR ? < stop_time) THEN 1 
            ELSE 0 
        END as is_start_time,
        CASE 
            WHEN start_time <= stop_time AND (? >= stop_time OR ? < start_time) OR
                 start_time > stop_time AND (? >= stop_time AND ? < start_time) THEN 1 
            ELSE 0 
        END as is_stop_time
        FROM run_manager 
        WHERE status = 'active' AND moddus = 'schedule' AND
        ((valid_from IS NULL OR strftime('%Y-%m-%d %H:%M:%S', valid_from) <= ?) AND 
         (valid_to IS NULL OR strftime('%Y-%m-%d %H:%M:%S', valid_to) >= ?))
        """
        cursor.execute(query, (current_time_str, current_time_str, current_time_str, current_time_str, 
                               current_time_str, current_time_str, current_time_str, current_time_str,
                               market_datetime_now_str, market_datetime_now_str))
        rows = cursor.fetchall()

        start_candidates = []
        stop_candidates = []
        for row in rows:
            run_manager_record = db.row_to_runmanager(row)
            if row['is_start_time']:
                start_candidates.append(run_manager_record)
            if row['is_stop_time']:
                stop_candidates.append(run_manager_record)

        results = {'start': start_candidates, 'stop': stop_candidates}

        return 0, results
    except Exception as e:
        msg_err = f"ERROR while fetching records for start and stop times with datetime {market_datetime_now_str}: {str(e)}  {format_exc()}"
        print(msg_err)
        return -2, msg_err  
    finally:
        conn.row_factory = None
        db.pool.release_connection(conn)


def fetch_startstop_scheduled_candidates(market_datetime_now, time_check, market = "US") -> tuple[int, list[RunManagerRecord]]:
    """
    Fetches all active records from the 'run_manager' table where moddus is schedule, the current date and time 
    in the America/New_York timezone falls between the 'valid_from' and 'valid_to' datetime 
    fields, and either 'start_time' or 'stop_time' matches the specified condition with the current time.
    If 'valid_from', 'valid_to', or the time column ('start_time'/'stop_time') are NULL, they are considered 
    as having unlimited boundaries.

    The function localizes the 'valid_from', 'valid_to', and the time column times using the 'zoneNY' 
    timezone object for accurate comparison with the current time. 

    Parameters:
        market_datetime_now (datetime): Current datetime in the market timezone.
        market (str): The market for which to fetch candidates.
        time_check (str): Either 'start' or 'stop', indicating which time condition to check.

    Returns:
        Tuple[int, list[RunManagerRecord]]: A tuple where the first element is a status code 
        (0 for success, -2 for error), and the second element is a list of RunManagerRecord 
        objects meeting the criteria. If an error occurs, the second element is a descriptive 
        error message.

    Note:
        This function assumes that the 'zoneNY' pytz timezone object is properly defined and 
        configured to represent the America/New York timezone. It also assumes that the 
        'run_manager' table exists in the database with the columns as described in the 
        provided schema.
    """
    if time_check not in ['start', 'stop']:
        return -2, "Invalid time_check parameter. Must be 'start' or 'stop'."

    conn = db.pool.get_connection()
    try:
        conn.row_factory = Row
        cursor = conn.cursor()

        # Get current datetime in America/New York timezone
        market_datetime_now_str = market_datetime_now.strftime('%Y-%m-%d %H:%M:%S')
        current_time_str = market_datetime_now.strftime('%H:%M')
        print("current_market_datetime_str:", market_datetime_now_str)
        print("current_time_str:", current_time_str)

        # SQL query to fetch records with active status, date constraints, and time condition
        time_column = 'start_time' if time_check == 'start' else 'stop_time'
        query = f"""
        SELECT * FROM run_manager 
        WHERE status = 'active' AND moddus = 'schedule' AND
        ((valid_from IS NULL OR strftime('%Y-%m-%d %H:%M:%S', valid_from) <= ?) AND 
        (valid_to IS NULL OR strftime('%Y-%m-%d %H:%M:%S', valid_to) >= ?)) AND
        ({time_column} IS NULL OR {time_column} <= ?)
        """
        cursor.execute(query, (market_datetime_now_str, market_datetime_now_str, current_time_str))
        rows = cursor.fetchall()
        results = [db.row_to_runmanager(row) for row in rows]

        return 0, results
    except Exception as e:
        msg_err = f"ERROR while fetching records based on {time_check} time with datetime {market_datetime_now_str}: {str(e)}  {format_exc()}"
        print(msg_err)
        return -2, msg_err  
    finally:
        conn.row_factory = None
        db.pool.release_connection(conn)


if __name__ == "__main__":
    res, sada = fetch_startstop_scheduled_candidates(datetime.now().astimezone(zoneNY), "start")
    if res == 0:
        print(sada)
    else:
        print("Error:", sada)

# from apscheduler.schedulers.background import BackgroundScheduler
# import time

# def print_hello():
#     print("Hello")

# def schedule_job():
#     scheduler = BackgroundScheduler()
#     scheduler.add_job(print_hello, 'interval', seconds=10)
#     scheduler.start()

# schedule_job()