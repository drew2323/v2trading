from uuid import UUID
from typing import Any, List, Tuple
from uuid import UUID, uuid4
from v2realbot.enums.enums import Moddus, SchedulerStatus, RecordType, StartBarAlign, Mode, Account, OrderSide
from v2realbot.common.model import RunManagerRecord, StrategyInstance, RunDay, StrategyInstance, Runner, RunRequest, RunArchive, RunArchiveView, RunArchiveViewPagination, RunArchiveDetail, RunArchiveChange, Bar, TradeEvent, TestList, Intervals, ConfigItem, InstantIndicator, DataTablesRequest
from v2realbot.utils.utils import validate_and_format_time, AttributeDict, zoneNY, zonePRG, safe_get, dict_replace_value, Store, parse_toml_string, json_serial, is_open_hours, send_to_telegram, concatenate_weekdays, transform_data
from v2realbot.common.PrescribedTradeModel import Trade, TradeDirection, TradeStatus, TradeStoplossType
from datetime import datetime
from v2realbot.config import JOB_LOG_FILE, STRATVARS_UNCHANGEABLES, ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY, ACCOUNT1_LIVE_API_KEY, ACCOUNT1_LIVE_SECRET_KEY, DATA_DIR,BT_FILL_CONS_TRADES_REQUIRED,BT_FILL_LOG_SURROUNDING_TRADES,BT_FILL_CONDITION_BUY_LIMIT,BT_FILL_CONDITION_SELL_LIMIT, GROUP_TRADES_WITH_TIMESTAMP_LESS_THAN, MEDIA_DIRECTORY, RUNNER_DETAIL_DIRECTORY, OFFLINE_MODE
import numpy as np
from rich import print as richprint
import v2realbot.controller.services as cs
import v2realbot.controller.run_manager as rm
import v2realbot.scheduler.scheduler as sch
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.job import Job

#NOTE zatím není podporováno spouštění strategie přes půlnoc - musí se dořešit weekday_filter
#který je zatím jen jeden jak pro start_time tak stop_time - což by v případě strategií běžících
#přes půlnoc nezafungovalo (stop by byl následující den a scheduler by jej nespustil)

def format_apscheduler_jobs(jobs: list[Job]) -> list[dict]:
    if not jobs:
        print("No scheduled jobs.")
        return

    jobs_info = []

    for job in jobs:
        job_info = {
            "Job ID": job.id,
            "Next Run Time": job.next_run_time,
            "Job Function": job.func.__name__,
            "Trigger": str(job.trigger),
            "Job Args": ', '.join(map(str, job.args)),
            "Job Kwargs": ', '.join(f"{k}={v}" for k, v in job.kwargs.items())
        }
        jobs_info.append(job_info)

    return jobs_info

def get_day_of_week(weekdays_filter):
    if not weekdays_filter:
        return '*'  # All days of the week
    return ','.join(map(str, weekdays_filter))

#initialize_jobs se spousti 
#- pri spusteni
#- triggerovano z add/update a delete

#zatim cely refresh, v budoucnu upravime jen na zmene menene polozky - viz 
#https://chat.openai.com/c/2a1423ee-59df-47ff-b073-0c49ade51ed7

#pomocna funkce, ktera vraci strat_id, ktera jsou v scheduleru vickrat (logika pro ne se lisi)
def stratin_occurences(all_records: list[RunManagerRecord]):
    # Count occurrences
    strat_id_counts = {}
    for record in all_records:
        if record.strat_id in strat_id_counts:
            strat_id_counts[record.strat_id] += 1
        else:
            strat_id_counts[record.strat_id] = 1

    # Find strat_id values that appear twice or more
    repeated_strat_ids = [strat_id for strat_id, count in strat_id_counts.items() if count >= 2]

    return 0, repeated_strat_ids


def initialize_jobs(run_manager_records: RunManagerRecord = None):
    """
    Initialize all scheduled jobs from RunManagerRecords with moddus = "schedule"
    Triggered on app init and update of table
    It deleted all "schedule_" prefixed jobs and schedule new ones base on runmanager table
    prefiX of "schedule_" in aps scheduler allows to distinguisd schedule types jobs and allows more jobs categories

    Parameters
    ----------
    run_manager_records : RunManagerRecord, optional
        RunManagerRecords to initialize the jobs from, by default None

    Returns
    -------
    Tuple[int, Union[List[dict], str]]
        A tuple containing an error code and a message. If there is no error, the
        message will contain a list of dictionaries with information about the
        scheduled jobs, otherwise it will contain an error message.
    """
    if run_manager_records is None:
        res, run_manager_records = rm.fetch_all_run_manager_records()
        if res < 0:
            err_msg= f"Error {res} fetching all runmanager records, error {run_manager_records}"
            print(err_msg)
            return -2, err_msg  

    scheduled_jobs = scheduler.get_jobs()

    #print(f"Current {len(scheduled_jobs)} scheduled jobs: {str(scheduled_jobs)}")
    for job in scheduled_jobs:
        if job.id.startswith("scheduler_"):
            scheduler.remove_job(job.id)
    record : RunManagerRecord = None
    for record in run_manager_records:
        if record.status == SchedulerStatus.ACTIVE and record.moddus == Moddus.SCHEDULE:
            day_of_week = get_day_of_week(record.weekdays_filter)

            hour, minute = map(int, record.start_time.split(':'))
            start_trigger = CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute, 
                                        start_date=record.valid_from, end_date=record.valid_to, timezone=zoneNY)
            stop_hour, stop_minute = map(int, record.stop_time.split(':'))
            stop_trigger = CronTrigger(day_of_week=day_of_week, hour=stop_hour, minute=stop_minute, 
                                    start_date=record.valid_from, end_date=record.valid_to, timezone=zoneNY)

            # Schedule new jobs with the 'scheduler_' prefix
            scheduler.add_job(start_runman_record, start_trigger, id=f"scheduler_start_{record.id}", args=[record.id])
            scheduler.add_job(stop_runman_record, stop_trigger, id=f"scheduler_stop_{record.id}", args=[record.id])
                        
    #scheduler.add_job(print_hello, 'interval', seconds=10, id=f"scheduler_testinterval")
    scheduled_jobs = scheduler.get_jobs()
    print(f"APS jobs refreshed ({len(scheduled_jobs)})")
    current_jobs_dict = format_apscheduler_jobs(scheduled_jobs)
    richprint(current_jobs_dict)
    return 0, current_jobs_dict

#zastresovaci funkce resici error handling a printing
def start_runman_record(id: UUID, market = "US", debug_date = None):
    record = None
    res, record, msg = _start_runman_record(id=id, market=market, debug_date=debug_date)

    if record is not None:
        market_time_now = datetime.now().astimezone(zoneNY) if debug_date is None else debug_date
        record.last_processed = market_time_now
        formatted_date = market_time_now.strftime("%y.%m.%d %H:%M:%S")
        history_string = f"{formatted_date}"
        history_string += " STARTED" if res == 0 else "NOTE:" + msg if res == -1 else "ERROR:" + msg 
        print(history_string)
        if record.history is None:
            record.history = history_string
        else:
            record.history += "\n" + history_string

        rs, msg_rs = update_runman_record(record)
        if rs < 0:
            msg_rs = f"Error saving result to history: {msg_rs}"
            print(msg_rs)
            send_to_telegram(msg_rs)


    if res < -1:
        msg = f"START JOB: {id} ERROR\n" + msg
        send_to_telegram(msg)
        print(msg)
    else:
        print(f"START JOB: {id} FINISHED {res}")


def update_runman_record(record: RunManagerRecord):
    #update record (nejspis jeste upravit - last_run a history)
    res, set = rm.update_run_manager_record(record.id, record)
    if res == 0:
        print(f"Record updated {set}")
        return 0, "OK"
    else:
        err_msg= f"STOP: Error updating {record.id} errir {set} with values {record}"
        return -2, err_msg#toto stopne zpracovani dalsich zaznamu pri chybe, zvazit continue

def stop_runman_record(id: UUID, market = "US", debug_date = None):
    res, record, msg = _stop_runman_record(id=id, market=market, debug_date=debug_date)
    #results : 0 - ok, -1 not running/already running/not specific, -2 error

    #report vzdy zapiseme do history, pokud je record not None, pripadna chyba se stala po dotazeni recordu
    if record is not None:
        market_time_now = datetime.now().astimezone(zoneNY) if debug_date is None else debug_date
        record.last_processed = market_time_now
        formatted_date = market_time_now.strftime("%y.%m.%d %H:%M:%S")
        history_string = f"{formatted_date}"
        history_string += " STOPPED" if res == 0 else "NOTE:" + msg if res == -1 else "ERROR:" + msg 
        print(history_string)
        if record.history is None:
            record.history = history_string
        else:
            record.history += "\n" + history_string

        rs, msg_rs = update_runman_record(record)
        if rs < 0:
            msg_rs = f"Error saving result to history: {msg_rs}"
            print(msg_rs)
            send_to_telegram(msg_rs)

    if res < -1:
        msg = f"STOP JOB: {id} ERROR\n" + msg
        send_to_telegram(msg)
        print(msg)
    else:
        print(f"STOP JOB: {id} FINISHED")

#start function that is called from the job
def _start_runman_record(id: UUID, market = "US", debug_date = None):
    print(f"Start scheduled record {id}")

    record : RunManagerRecord = None
    res, result = rm.fetch_run_manager_record_by_id(id)
    if res < 0:
        result = "Error fetching run manager record by id: " + str(id) + " Error: " + str(result)
        return res, record, result
    
    record = result

    res, sada = sch.get_todays_market_times(market=market, debug_date=debug_date)
    if res == 0:
        market_time_now, market_open_datetime, market_close_datetime = sada
        print(f"OPEN:{market_open_datetime} CLOSE:{market_close_datetime}")
    else:
        sada = "Error getting market times (CLOSED): " + str(sada)
        return res, record, sada
    
    if cs.is_stratin_running(record.strat_id):
        return -1, record, f"Stratin {record.strat_id} is already running"

    res, result = sch.run_scheduled_strategy(record)
    if res < 0:
        result = "Error running strategy: " + str(result)
        return res, record, result
    else:
        record.runner_id = UUID(result)

    return 0, record, record.runner_id

#stop function that is called from the job
def _stop_runman_record(id: UUID, market = "US", debug_date = None):
    record = None
    #get all records
    print(f"Stopping record {id}")
    res, all_records = rm.fetch_all_run_manager_records()
    if res < 0:
        err_msg= f"Error {res} fetching all runmanager records, error {all_records}"
        return -2, record, err_msg  
    
    record : RunManagerRecord = None
    for rec in all_records:
        if rec.id == id:
            record = rec
            break
    
    if record is None:
        return -2, record, f"Record id {id} not found"

    #strat_ids that are repeated
    res, repeated_strat_ids = stratin_occurences(all_records)
    if res < 0:
        err_msg= f"Error {res} finding repeated strat_ids, error {repeated_strat_ids}"
        return -2, record, err_msg
    
    if record.strat_running is True:
        #stopneme na zaklade record.runner_id
        #this code
        id_to_stop = record.runner_id

    #pokud existuje manualne spustena stejna strategie a neni jich vic - je to jednoznacne - stopneme ji
    elif cs.is_stratin_running(record.strat_id) and record.strat_id not in repeated_strat_ids:
        #stopneme na zaklade record.strat_id
        id_to_stop = record.strat_id

    else:
        msg = f"strategy {record.strat_id} not RUNNING or not distinctive (manually launched or two strat_ids in scheduler)"
        print(msg)
        return -1, record, msg

    print(f"Requesting STOP {id_to_stop}")
    res, msg = cs.stop_runner(id=id_to_stop)
    if res < 0:
        msg = f"ERROR while STOPPING runner_id/strat_id {id_to_stop} {msg}"
        return -2, record, msg    
    else:
        record.runner_id = None

    return 0, record, "finished"

# Global scheduler instance
scheduler = BackgroundScheduler(timezone=zoneNY)
scheduler.start()


if __name__ == "__main__":
   #use naive datetoime
    debug_date = None
    debug_date = datetime(2024, 2, 16, 9, 37, 0, 0)
    #debug_date = datetime(2024, 2, 16, 10, 30, 0, 0)
    #debug_date = datetime(2024, 2, 16, 16, 1, 0, 0)

    id = UUID("bc4ec7d2-249b-4799-a02f-f1ce66f83d4a")

    if debug_date is not None:
        # Localize the naive datetime object to the Eastern timezone
        debug_date = zoneNY.localize(debug_date)
        #debugdate formatted as string in format "23.12.2024 9:30"
        formatted_date = debug_date.strftime("%d.%m.%Y %H:%M") 
        print("Scheduler.py NY time: ", formatted_date)
        print("ISoformat", debug_date.isoformat())

    # res, result = start_runman_record(id=id, market = "US", debug_date = debug_date)
    # print(f"CALL FINISHED, with {debug_date} RESULT: {res}, {result}")


    res, result = stop_runman_record(id=id, market = "US", debug_date = debug_date)
    print(f"CALL FINISHED, with {debug_date} RESULT: {res}, {result}")