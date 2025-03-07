from typing import Any, List, Tuple
from uuid import UUID, uuid4
import pickle
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockTradesRequest, StockBarsRequest
from alpaca.data.enums import DataFeed 
from alpaca.data.timeframe import TimeFrame
from v2realbot.strategy.base import StrategyState
from v2realbot.enums.enums import RecordType, StartBarAlign, Mode, Account, OrderSide
from v2realbot.common.model import RunDay, StrategyInstance, Runner, RunRequest, RunArchive, RunArchiveView, RunArchiveViewPagination, RunArchiveDetail, RunArchiveChange, Bar, TradeEvent, TestList, Intervals, ConfigItem, InstantIndicator, DataTablesRequest
from v2realbot.utils.utils import AttributeDict, zoneNY, zonePRG, safe_get, dict_replace_value, Store, parse_toml_string, json_serial, is_open_hours, send_to_telegram, concatenate_weekdays, transform_data, gaka
from v2realbot.utils.ilog import delete_logs
from v2realbot.common.model import Trade, TradeDirection, TradeStatus, TradeStoplossType
from datetime import datetime
from v2realbot.loader.trade_offline_streamer import Trade_Offline_Streamer
from threading import Thread, current_thread, Event, enumerate
from v2realbot.config import PRE_MARKET_OFFSET, POST_MARKET_OFFSET, STRATVARS_UNCHANGEABLES, ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY, ACCOUNT1_PAPER_FEED, ACCOUNT1_LIVE_API_KEY, ACCOUNT1_LIVE_SECRET_KEY, ACCOUNT1_LIVE_FEED, DATA_DIR, MEDIA_DIRECTORY, RUNNER_DETAIL_DIRECTORY
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
from v2realbot.common.db import pool, execute_with_retry
import v2realbot.common.transform as tr
from sqlite3 import OperationalError, Row
import v2realbot.strategyblocks.indicators.custom as ci
from v2realbot.strategyblocks.inits.init_indicators import initialize_dynamic_indicators
from v2realbot.strategyblocks.indicators.indicators_hub import populate_dynamic_indicators
from v2realbot.strategyblocks.inits.init_attached_data import attach_previous_data
from v2realbot.interfaces.backtest_interface import BacktestInterface
import os
import v2realbot.reporting.metricstoolsimage as mt
import gzip
import os
import msgpack
import v2realbot.utils.config_handler as cfh
#import gc
#from pyinstrument import Profiler
#adding lock to ensure thread safety of TinyDB (in future will be migrated to proper db)
lock = Lock()

arch_header_file = DATA_DIR + "/arch_header.json"
#arch_detail_file = DATA_DIR + "/arch_detail.json"
#db layer to store runner archive
db_arch_h = TinyDB(arch_header_file, default=json_serial, option=orjson.OPT_PASSTHROUGH_DATETIME)
#db_arch_d = TinyDB(arch_detail_file, default=json_serial, option=orjson.OPT_PASSTHROUGH_DATETIME)

#db layer to store stratins, TBD zmigrovat do TinyDB
db = Store()

def get_all_threads():
    res = str(enumerate())
    if len(res) > 0:
        return (0, res)
    else:
        return (-2, "not found")
    
def get_all_runners():
    with db.runners_lock: 
        if len(db.runners) > 0:
            #print(db.runners)
            for i in db.runners:
                if i.run_instance:
                    i.run_profit = round(float(i.run_instance.state.profit),2)
                    i.run_trade_count = len(i.run_instance.state.tradeList)
                    i.run_positions = gaka(i.run_instance.state.account_variables, "positions")
                    i.run_avgp = gaka(i.run_instance.state.account_variables, "avgp", lambda x: round(float(x),3))
            return (0, db.runners)
        else:
            return (0, [])
 
def get_all_stratins():
    if len(db.stratins) > 0:
        return (0, db.stratins)
    else:
        return (0, [])
     
def get_stratin(id: UUID) -> List[StrategyInstance]:
    for i in db.stratins:
        if str(i.id) == str(id):
            return (0, i)
    return (-2, "not found")

def get_runner(id: UUID):
    with db.runners_lock: 
        for i in db.runners:
            if str(i.id) == str(id):
                i.run_profit = round(float(i.run_instance.state.profit),2)
                i.run_trade_count = len(i.run_instance.state.tradeList)
                i.run_positions =gaka(i.run_instance.state.account_variables, "positions")
                i.run_avgp = gaka(i.run_instance.state.account_variables, "avgp", lambda x: round(float(x),3))
                return (0, i)
        return (-2, "not found")

def create_stratin(si: StrategyInstance):
    #validate toml
    res, stp = parse_toml_string(si.stratvars_conf)
    if res < 0:
        return (-1,f"stratvars invalid: {stp}")
    res, adp = parse_toml_string(si.add_data_conf)
    if res < 0:
        return (-1, f"add data conf invalid {adp}") 
    si.id = uuid4()
    #print(si)
    db.stratins.append(si)
    db.save()
    #print(db.stratins)
    return (0,si.id)

def modify_stratin(si: StrategyInstance, id: UUID):
    #validate toml if fields exists
    if is_stratin_running(id):
        return (-1, "strat is running, use modify_stratin_running")
    res, stp = parse_toml_string(si.stratvars_conf)
    if res < 0:
        return (-1, f"stratvars invalid {stp}")
    res, adp = parse_toml_string(si.add_data_conf)
    if res < 0:
        return (-1, f"add data conf invalid {adp}") 
    for i in db.stratins:
        if str(i.id) == str(id):
            #print("removing",i)
            db.stratins.remove(i)
            #print("adding",si)
            db.stratins.append(si)
            #print(db.stratins)
            db.save()
            return (0, i.id)
    return (-2, "not found")

def delete_stratin(id: UUID):
    if is_stratin_running(id=str(id)):
        return (-1, "Strategy Instance is running " + str(id))
    for i in db.stratins:
        if str(i.id) == str(id):
            db.stratins.remove(i)
            db.save()
            print(db.stratins)
            return (0, i.id)
    return (-2, "not found")

def inject_stratvars(id: UUID, stratvars_parsed_new: AttributeDict, stratvars_parsed_old: AttributeDict):
    with db.runners_lock: 
        for i in db.runners:
            if str(i.strat_id) == str(id):
                #inject only those changed, some of them cannot be changed (for example pendingbuys)

                changed_keys = []
                #get changed values
                for key,value in stratvars_parsed_new.items():
                    if value != stratvars_parsed_old[key]:
                        changed_keys.append(key)

                #print("changed before check", changed_keys)
                #remove keys that cannot be changed
                for k in changed_keys:
                    if k in STRATVARS_UNCHANGEABLES:
                        #print(k, "cant be changed removing")
                        changed_keys.remove(k)
                        return -2, "Stratvar Key "+k+" cannot be changed"

                #print("clean changed keys", changed_keys)
                #inject clean keys
                for k in changed_keys:
                    print("INJECTING ",k, "value", stratvars_parsed_new[k])
                    i.run_instance.state.vars[k] = stratvars_parsed_new[k]
                    i.run_instance.stratvars[k] = stratvars_parsed_new[k]
                return 0, None
        return -2, "No runners found"

#allows change of set of parameters that are possible to change while it is running
#also injects those parameters to instance
def modify_stratin_running(si: StrategyInstance, id: UUID):
    try:
        #validate toml
        res,stp = parse_toml_string(si.stratvars_conf)
        if res < 0:
            return (-1, f"new stratvars format invalid {stp}")
        for i in db.stratins:
            if str(i.id) == str(id):
                if not is_stratin_running(id=str(id)):
                    return (-1, "not running")
                res,stp_old = parse_toml_string(i.stratvars_conf)
                if res < 0:
                    return (-1, f"current stratin stratvars invalid {stp_old}")
                #TODO reload running strat
                #print(stp)
                #print("starting injection", stp)
                res, msg = inject_stratvars(id=si.id, stratvars_parsed_new=stp["stratvars"], stratvars_parsed_old=stp_old["stratvars"])
                if res < 0:
                    print("ajajaj inject se nepovedl", msg)
                    return(-3, "inject failed: " + msg)
                i.id2 = si.id2
                i.name = si.name
                i.open_rush = si.open_rush
                i.stratvars_conf = si.stratvars_conf
                i.note = si.note
                i.history = si.history
                db.save()
                return (0, i.id)
        return (-2, "not found")
    except Exception as e:
        return (-2, "Error Exception" + str(e))


##enable realtime chart - inject given queue for strategy instance
##webservice listens to this queue
async def runner_realtime_on(id: UUID, rtqueue: Queue):
    with db.runners_lock: 
        for i in db.runners:
            if str(i.id) == str(id):
                i.run_instance.rtqueue = rtqueue
                print("RT QUEUE added")
                return 0
        print("ERROR NOT FOUND")
        return -2

async def runner_realtime_off(id: UUID):
    with db.runners_lock: 
        for i in db.runners:
            if str(i.id) == str(id):
                i.run_instance.rtqueue = None
                print("RT QUEUE removed")
                return 0
        print("ERROR NOT FOUND")
        return -2

##controller (run_stratefy, pause, stop, reload_params)
def pause_runner(id: UUID):
    with db.runners_lock: 
        for i in db.runners:
            print(i.id)
            if str(i.id) == id:
                if i.run_pause_ev.is_set():
                    i.run_pause_ev.clear()
                    i.run_paused = None
                    print("Unpaused")
                    return (0, "unpaused runner " + str(i.id))
                print("pausing runner", i.id)
                i.run_pause_ev.set()
                i.run_paused = datetime.now().astimezone(zoneNY)
                return (0, "paused runner " + str(i.id))
        print("no ID found")
        return (-1, "not running instance found")
#allows to delete runner based on runner_id, strat_id or all (both none)
#podpruje i hodnotu strat_id v id
def stop_runner(id: UUID = None, strat_id: UUID = None):
    with db.runners_lock: 
        chng = []
        try:
            for i in db.runners:
                #print(i['id'])
                if (id is None and strat_id is None) or str(i.id) == str(id) or str(i.strat_id) == str(strat_id) or str(i.strat_id) == str(id):
                    chng.append(i.id)
                    print("Sending STOP signal to Runner", i.id)
                    #just sending the signal, update is done in stop after plugin
                    i.run_stop_ev.set()
                    # i.run_stopped = datetime.now().astimezone(zoneNY)
                    # i.run_thread = None
                    # i.run_instance = None
                    # i.run_pause_ev = None
                    # i.run_stop_ev = None
                    # #stratins.remove(i)
        except Exception as e:
            return (-2, "Error Exception" + str(e) + format_exc())
        if len(chng) > 0:
            return (0, "Sent STOP signal to those" + str(chng))
        else:
            return (-2, "not found" + str(id))

def is_stratin_running(id: UUID):
    with db.runners_lock: 
        for i in db.runners:
            if str(i.strat_id) == str(id):
                if i.run_started is not None and i.run_stopped is None:
                    return True
        return False

def is_runner_running(id: UUID):
    with db.runners_lock: 
        for i in db.runners:
            if str(i.id) == str(id):
                if i.run_started is not None and i.run_stopped is None:
                    return True
        return False

def save_history(id: UUID, st: object, runner: Runner, reason: str = None):
    
    # #zkousime precist profit z objektu
    # try:
    #     profit = st.state.profit
    #     trade_count = len(st.state.tradeList)
    # except Exception as e:
    #     profit = str(e)
    
    #zapisujeme pouze reason - pouzito jen pri exceptione
    if reason is not None:
        for i in db.stratins:
            if str(i.id) == str(id):
                i.history += "\nREASON:" + str(reason)
                #i.history += str(runner.__dict__)+"<BR>"
                db.save()
 
#Capsule to run the thread in. Needed in order to update db after strat ends for any reason#
def capsule(target: object, db: object, inter_batch_params: dict = None):
    
    #TODO zde odchytit pripadnou exceptionu a zapsat do history
    #cil aby padnuti jedne nezpusobilo pad enginu
    try:

        # profiler = Profiler()
        # profiler.start()
        target.start()

        print("Strategy instance stopped. Update runners")
        reason = None

        if target.se.is_set():
            print("EXTERNAL STOP FLAG IS SET - cancel BATCH if running")
            if inter_batch_params is not None:
                inter_batch_params["stop"] = True
            reason = "STOP Signal received"

    except Exception as e:
        reason = "SHUTDOWN Exception:" + str(e) + format_exc()
        #raise RuntimeError('Exception v runneru POZOR') from e
        if inter_batch_params is not None:
            inter_batch_params["error"] = reason
        print(str(e))
        print(reason)
        send_to_telegram(reason)
    finally:
        # profiler.stop()
        # now = datetime.now()
        # results_file = "profiler"+now.strftime("%Y-%m-%d_%H-%M-%S")+".html"
        # with open(results_file, "w", encoding="utf-8") as f_html:
        #     f_html.write(profiler.output_html())

        # remove runners after thread is stopped and save results to stratin history
        with db.runners_lock:   
            for i in db.runners:
                if i.run_instance == target:
                    i.run_stopped = datetime.now().astimezone(zoneNY)
                    i.run_thread = None
                    i.run_instance = None
                    i.run_pause_ev = None
                    i.run_stop_ev = None
                    #ukladame jen pro zapis exception reasonu
                    save_history(id=i.strat_id, st=target, runner=i, reason=reason)
                    #store in archive header and archive detail
                    archive_runner(runner=i, strat=target, inter_batch_params=inter_batch_params)
                    #mazeme runner po skonceni instance
                    db.runners.remove(i)
                    #vytvoreni report image pro RUNNER
                    try:
                        res, val = mt.generate_trading_report_image(runner_ids=[str(i.id)])
                        if res == 0:
                            print("DAILY REPORT IMAGE CREATED")
                        else:
                            print(f"Daily report ERROR - {val}")
                    except Exception as e:
                        err_msg = "Nepodarilo se vytvorit daily report image" + str(e)+format_exc()
                        send_to_telegram(err_msg)
                        print(err_msg)
                    #PRO LIVE a PAPER pri vyplnenem batchi vytvarime batchovy soubor zde (pro BT ridi batch_manager)
                    if i.run_mode in [Mode.LIVE, Mode.PAPER] and i.batch_id is not None:
                        try:
                            res, val = mt.generate_trading_report_image(batch_id=i.batch_id)
                            if res == 0:
                                print("BATCH REPORT CREATED")
                            else:
                                print(f"BATCH REPORT ERROR - {val}")
                        except Exception as e:
                            err_msg = f"Nepodarilo se vytvorit batchj report image pro {i.strat_id} a batch{i.batch_id}" + str(e)+format_exc()
                            send_to_telegram(err_msg)
                            print(err_msg)

        target.release()
    print("Runner STOPPED")

#vrátí konkrétní sadu testlistu
def get_testlist_byID(record_id: str):
    conn = pool.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, dates FROM test_list WHERE id = ?", (record_id,))
        row = cursor.fetchone()
    finally:
        pool.release_connection(conn)
    
    if row is None:
        return -2, "not found"
    else:
        return 0, TestList(id=row[0], name=row[1], dates=orjson.loads(row[2]))


##TADY JSEM SKONCIL PROJIT - dodelat nastavni timezone
#nejspis vse v RunDays by melo byt jiz lokalizovano na zoneNY
#zaroven nejak vymyslet, aby bt_from/to uz bylo lokalizovano
#ted jsem dal natvrdo v main rest lokalizaci
#ale odtrasovat,ze vse funguje (nefunguje)

#volano pro batchove spousteni (BT,)
def run_batch_stratin(id: UUID, runReq: RunRequest):
    #pozor test_batch_id je test interval id (batch id se pak generuje pro kazdy davkovy run tohoto intervalu)
    if runReq.test_batch_id is None and (runReq.bt_from is None or runReq.bt_from.date() == runReq.bt_to.date()):
        return (-1, "test interval or different days required for batch run")

    if runReq.mode not in (Mode.BT, Mode.PREP):
        return (-1, "batch run only for backtest/prep")
    
    #print("request values:", runReq)

    def get_market_days_in_interval(datefrom, dateto, note = None, id = None, exthours: bool = False):
        """
        If ext hours then the whole day is selected.
        """
        #getting dates from calendat
        clientTrading = TradingClient(ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY, raw_data=False, paper=True)        
        calendar_request = GetCalendarRequest(start=datefrom.date(),end=dateto.date())
        cal_dates = clientTrading.get_calendar(calendar_request)
        #list(Calendar)
        # Calendar
        #     date: date
        #     open: datetime
        #     close: datetime
        cal_list = []
        for day in cal_dates:
            start_time = zoneNY.localize(day.open)
            end_time = zoneNY.localize(day.close)
 
            #ZDE JSEM SKONCIL
            #dotestovat exthours a pak se vratit do ipynb a pokracovat tam
            if exthours:
                # Extend schedule with pre- and post-market times
                pre_market_open = start_time - PRE_MARKET_OFFSET
                post_market_close = end_time + POST_MARKET_OFFSET

                min_day_time = pre_market_open
                max_day_time = post_market_close
                #or alternatively use day min and day max times
                #min_day_time = zoneNY.localize(datetime.combine(start_time.date(), datetime.min.time()))
                #max_day_time = zoneNY.localize(datetime.combine(start_time.date(), datetime.max.time()))   
                start_time = max(datefrom, min_day_time)
                end_time = min(dateto, max_day_time)

            #u prvni polozky
            if day == cal_dates[0] and exthours is False:
                #pokud je cas od po konci marketa, nedavame tento den
                if datefrom > end_time:
                    print("Cas od je po konci marketu, vynechavame tento den")
                    continue

                #pokud je cas od od vetsi nez open marketu prvniho dne, pouzijeme tento pozdejis cas
                if datefrom > start_time:
                    start_time = datefrom

            #u posledni polozky
            if day == cal_dates[-1] and exthours is False:
                #cas do, je pred openenem market, nedavame tento den
                if dateto < start_time:
                    continue
                #pokud koncovy cas neni do konce marketu, pouzijeme tento drivejsi namisto konce posledniho dne
                if dateto < end_time:
                    end_time = dateto
            cal_list.append(RunDay(start = start_time, end = end_time, note = note, id = id))

        print(f"Getting interval dates from - to - RESULT ({len(cal_list)}):")
        #print(cal_list)
        return cal_list

    def is_ext_hours(id: UUID):
        """
        Temporary function to set ext_hours from add_data, before issue #260 will be implemented
        """
        #volani funkce instantiate_strategy
        for i in db.stratins:
            if str(i.id) == str(id):
                    res, adp = parse_toml_string(i.add_data_conf)
                    if res < 0:
                        return (-1, f"add data conf invalid {adp}")
                    break
        for st in adp["add_data"]:
            if st.get("exthours", False) and st["exthours"]:
                return True
        return False

    exthours = is_ext_hours(id)

    #getting days to run into RunDays format
    if runReq.test_batch_id is not None:
        print("getting intervals days")
        testlist: TestList

        res, testlist = get_testlist_byID(record_id=runReq.test_batch_id)

        if res < 0:
            return (-1, f"not existing ID of testlists with {runReq.test_batch_id}")
        
        print("test interval:", testlist)

        cal_list = []
        #interval dame do formatu list(RunDays)
        #v intervalu je market local time
        for intrvl in testlist.dates:
            start_time = zoneNY.localize(datetime.fromisoformat(intrvl.start))
            end_time = zoneNY.localize(datetime.fromisoformat(intrvl.end))
            #pokud nejde o konkretni dny, ale o interval, pridame vsechny dny z tohoto intervalu
            if start_time.date() != end_time.date():
                print("interval within testlist, fetching market days")
                cal_list += get_market_days_in_interval(start_time, end_time, intrvl.note, testlist.id, exthours)
            else:
                cal_list.append(RunDay(start = start_time, end = end_time, note=intrvl.note, id=testlist.id))

        #sem getting dates
    else:
        if runReq.bt_to is None:
            runReq.bt_to = datetime.now().astimezone(zoneNY)
        
        cal_list = get_market_days_in_interval(runReq.bt_from, runReq.bt_to, exthours=exthours)

    print(f"Getted cal intervals - RESULT ({len(cal_list)}):")
    print(cal_list)
#spousti se vlakno s paralelnim behem a vracime ok
    ridici_vlakno = Thread(target=batch_run_manager, args=(id, runReq, cal_list), name=f"Batch run control thread started.")
    ridici_vlakno.start()    
    print(enumerate())

    return 0, f"Batch run started"

#thread, ktery bude ridit paralelni spousteni 
# bud ceka na dokonceni v runners nebo to bude ridit jinak a bude mit jednoho runnera?
# nejak vymyslet.
# logovani zatim jen do print

##OFFLINE BATCH RUN MANAGER (generuje batch_id, ridi datove provazani runnerů(inter_batch_data) a generuje batch report
## a samozrejme spousti jednotlivé dny
def batch_run_manager(id: UUID, runReq: RunRequest, rundays: list[RunDay]):
    #zde muzu iterovat nad intervaly
    #cekat az dobehne jeden interval a pak spustit druhy
    #pripadne naplanovat beh - to uvidim
    #domyslet kompatibilitu s budoucim automatickym "dennim" spousteni strategii
    #taky budu mit nejaky konfiguracni RUN MANAGER, tak by krome rizeniho denniho runu
    #mohl podporovat i BATCH RUNy.
    batch_id = str(uuid4())[:8]
    runReq.batch_id = batch_id
    print("Entering BATCH RUN MANAGER")
    print("generated batch_ID", batch_id)

    #SORT RUNDAYS according to start atttibute
    #print("RUNDAYS before sort:", rundays)
    rundays.sort(key=lambda x: x.start)
    #print("RUNDAYS after sort:", rundays)

    #APPLY WEEKDAYS filter - necháváme pouze ty, ktere jsou uvedene
    if runReq.weekdays_filter is not None:
        rundays = [run_day for run_day in rundays if run_day.start.weekday() in runReq.weekdays_filter]

    if len(rundays) == 0:
        print("No eligible DAYS")
        return
    
    cnt_max = len(rundays)
    cnt = 0
    #promenna pro sdileni mezi runy jednotlivych batchů (např. daily profit)
    inter_batch_params = dict(batch_profit=0, batch_rel_profit=0)
    note_from_run_request = runReq.note
    first = None
    first_frm = None
    last = None
    last_frm = None

    # Find the minimum start date and maximum end date to add to Note
    first = min(runday.start for runday in rundays)
    last = max(runday.end for runday in rundays)
    first_frm = first.strftime("%d.%m.")
    last_frm = last.strftime("%d.%m.") 

    weekdayfilter_string = ""
    if runReq.weekdays_filter is not None:
        weekdayfilter_string = concatenate_weekdays(runReq.weekdays_filter)
        weekdayfilter_string = "DAYS:" + weekdayfilter_string.upper() if weekdayfilter_string != '' else ''

    for day in rundays:
        cnt += 1
        print("Datum od", day.start)
        print("Datum do", day.end)
        runReq.bt_from = day.start
        runReq.bt_to = day.end
        #pozor z tohoto parsuje GUI Na batchheader
        runReq.note = f"{first_frm}-{last_frm} Batch {batch_id} #{cnt}/{cnt_max} {weekdayfilter_string} {day.name} {day.note if day.note is not None else ''} N: {note_from_run_request}"

        #protoze jsme v ridicim vlaknu, poustime za sebou jednotlive stratiny v synchronnim modu
        res, id_val = run_stratin(id=id, runReq=runReq, synchronous=True, inter_batch_params=inter_batch_params)
        if res < 0:
            msg = f"Chyba v runu #{cnt} od:{runReq.bt_from} do {runReq.bt_to} -> {id_val}"
            if inter_batch_params is not None:
                inter_batch_params["error"] = msg
            print(msg)
            break

        if "stop" in inter_batch_params and inter_batch_params["stop"] is True:
            #mame stop signal rusime cely BATCH
            print("STOP SIGNAL RECEIVED")
            break


    print("Batch manager FINISHED")
    ##TBD sem zapsat do hlavicky batchů! abych měl náhled - od,do,profit, metrics
    batch_abs_profit = 0
    batch_rel_profit = 0
    try:
        #print(inter_batch_params)
        batch_abs_profit = inter_batch_params["batch_profit"]
        batch_rel_profit = inter_batch_params["batch_rel_profit"]
    except Exception as e:
        print("inter batch params problem", inter_batch_params, str(e)+format_exc())

    for i in db.stratins:
        if str(i.id) == str(id):
            i.history += "\nBatch: "+str(batch_id)+" "+str(first_frm)+" "+str(last_frm)+" P:"+str(int(batch_abs_profit))+ "R:"+str(round(batch_rel_profit,4))
            #i.history += str(runner.__dict__)+"<BR>"
            db.save()

    inter_batch_params = None
    runReq = None
    #vytvoreni report image pro batch
    try:
        res, val = mt.generate_trading_report_image(batch_id=batch_id)
        if res == 0:
            print("BATCH REPORT CREATED")
        else:
            print(f"BATCH REPORT ERROR - {val}")

    except Exception as e:
        err_msg = "Nepodarilo se vytvorit batch report image" + str(e)+format_exc()
        send_to_telegram(err_msg)
        print(err_msg)       

    #gc.collect()

#stratin run
def run_stratin(id: UUID, runReq: RunRequest, synchronous: bool = False, inter_batch_params: dict = None):
    if runReq.mode == Mode.BT:
        if runReq.bt_from is None:
            return (-1, "start date required for BT")
        if runReq.bt_to is None:
            runReq.bt_to = datetime.now().astimezone(zoneNY)
    
    #print("hodnota ID pred",id)
    #volani funkce instantiate_strategy
    for i in db.stratins:
        if str(i.id) == str(id):
            try:
                if is_stratin_running(id=id):
                    return(-1, "already running")
                #validate toml
                res, stp = parse_toml_string(i.stratvars_conf)
                if res < 0:
                    return (-1, f"stratvars invalid {stp}")
                res, adp = parse_toml_string(i.add_data_conf)
                if res < 0:
                    return (-1, f"add data conf invalid {adp}")
                id = uuid4()
                print(f"RUN {id} INITIATED")
                name = i.name
                symbol = i.symbol
                open_rush = i.open_rush
                close_rush = i.close_rush
                try:            
                    stratvars = AttributeDict(stp["stratvars"])
                except KeyError:
                    return (-1, "stratvars musi obsahovat element [stratvars]")
                classname = i.class_name
                script = "v2realbot."+i.script
                pe = Event()
                se = Event()

                import_script = importlib.import_module(script)
                next = getattr(import_script, "next")
                init = getattr(import_script, "init")
                my_module = importlib.import_module("v2realbot.strategy."+classname)
                StrategyClass = getattr(my_module, classname)
                #instance strategie
                instance = StrategyClass(name= name,
                                            symbol=symbol,
                                            account=runReq.account,
                                            next=next,
                                            init=init,
                                            stratvars=stratvars,
                                            open_rush=open_rush,
                                            close_rush=close_rush,
                                            pe=pe,
                                            se=se,
                                            runner_id=id,
                                            ilog_save=runReq.ilog_save,
                                            batch_id=runReq.batch_id)
                print("instance vytvorena", instance)
                #set mode
                if runReq.mode == Mode.LIVE or runReq.mode == Mode.PAPER:
                    instance.set_mode(mode=runReq.mode, debug = runReq.debug)
                else:
                    instance.set_mode(mode = Mode.BT,
                                    debug = runReq.debug,
                                    start = runReq.bt_from.astimezone(zoneNY),
                                    end =   runReq.bt_to.astimezone(zoneNY),
                                    cash=runReq.cash)
                ##add data streams
                for st in adp["add_data"]:
                    print("adding stream", st)
                    instance.add_data(**st)

                print("Starting strategy", instance.name)

                #vlakno = Thread(target=instance.start, name=instance.name)
                #pokus na spusteni v kapsli, abychom po skonceni mohli updatnout stratin
                vlakno = Thread(target=capsule, args=(instance,db, inter_batch_params), name=instance.name)
                vlakno.start()
                print("Spuštěna", instance.name)

                ##storing the attributtes - pozor pri stopu je zase odstranit
                #id runneru je nove id, stratin se dava dalsiho parametru
                runner = Runner(id = id,
                        strat_id = i.id,
                        batch_id = runReq.batch_id,
                        run_started = datetime.now(zoneNY),
                        run_pause_ev = pe,
                        run_name = name,
                        run_symbol = symbol,
                        run_note = runReq.note,
                        run_stop_ev = se,
                        run_strat_json = runReq.strat_json,
                        run_thread = vlakno,
                        run_account = runReq.account,
                        run_ilog_save = runReq.ilog_save,
                        run_mode = runReq.mode,
                        run_instance = instance,
                        run_stratvars_toml=i.stratvars_conf)
                
                with db.lock:
                    db.runners.append(runner)
                #print(db.runners)
                #print(i)
                #print(enumerate())

                #pokud spoustime v batch módu, tak čekáme na výsledek a pak pouštíme další run
                if synchronous:
                    print(f"waiting for thread {vlakno} to finish")
                    vlakno.join()

                if inter_batch_params is not None:
                    return (0, inter_batch_params)
                else:
                    return (0, id)
            except Exception as e:
                return (-2, "Exception: "+str(e)+format_exc())
    return (-2, "not found")

def get_trade_history(symbol: str, timestamp_from: float, timestamp_to:float):
    try:
        datetime_object_from = datetime.fromtimestamp(timestamp_from, zoneNY)
        datetime_object_to = datetime.fromtimestamp(timestamp_to, zoneNY)
        #datetime_object_from = datetime(2023, 4, 14, 15, 51, 38, tzinfo=zoneNY)
        #datetime_object_to = datetime(2023, 4, 14, 15, 51, 39, tzinfo=zoneNY)   
        client = StockHistoricalDataClient(ACCOUNT1_LIVE_API_KEY, ACCOUNT1_LIVE_SECRET_KEY, raw_data=False)
        trades_request = StockTradesRequest(symbol_or_symbols=symbol, feed = ACCOUNT1_LIVE_FEED, start=datetime_object_from, end=datetime_object_to)
        all_trades = client.get_stock_trades(trades_request)
        #print(all_trades[symbol])
        return 0, all_trades[symbol]
    except Exception as e:
        return (-2, f"problem {e}")
    
def populate_metrics_output_directory(strat: StrategyInstance, inter_batch_params: dict = None):
    """
    WIP
    Spocte zakladni metriky pred ulozenim do archivu

    Toto cele predelat nejak systemove v ramci systemoveho reportingu. Tato preliminary cast by mela umoznovat pridavat
     a ukladat zakladni metriky, ktere me zajimaji ihned po skonceni runu.
    """

    tradeList = strat.state.tradeList

    trade_dict = AttributeDict(account=[],orderid=[],timestamp=[],symbol=[],side=[],order_type=[],qty=[],price=[],position_qty=[])
    if strat.mode == Mode.BT:
        trade_dict["value"] = []
        trade_dict["cash"] = []
        trade_dict["pos_avg_price"] = []
    for t in tradeList:
        if t.event == TradeEvent.FILL:
            trade_dict.account.append(t.account)
            trade_dict.orderid.append(str(t.order.id))
            trade_dict.timestamp.append(t.timestamp)
            trade_dict.symbol.append(t.order.symbol)
            trade_dict.side.append(t.order.side)
            trade_dict.qty.append(t.qty)
            trade_dict.price.append(t.price)
            trade_dict.position_qty.append(t.position_qty)
            trade_dict.order_type.append(t.order.order_type)
            #backtest related additional attributtes, not present on LIVE
            if strat.mode == Mode.BT: 
                trade_dict.value.append(t.value)
                trade_dict.cash.append(t.cash)
                trade_dict.pos_avg_price.append(t.pos_avg_price)

    trade_df = pd.DataFrame(trade_dict)
    trade_df = trade_df.set_index('timestamp',drop=False)

    #max positions- tzn. count max quantity ze sell fill orderu
    #nepocita otevrene objednavky
    max_positions = trade_df.groupby('side')['qty'].value_counts().reset_index(name='count').sort_values(['qty'], ascending=False)
    max_positions = max_positions[max_positions['side'] == OrderSide.SELL]
    max_positions = max_positions.drop(columns=['side'], axis=1)

    res = dict(account_variables={}, profit={})
    #filt = max_positions['side'] == 'OrderSide.BUY'

    res["account_variables"] = transform_data(strat.state.account_variables, json_serial)

    res["pos_cnt"] = dict(zip(str(max_positions['qty']), max_positions['count']))
    #naplneni batch sum profitu
    if inter_batch_params is not None:
        res["profit"]["batch_sum_profit"] = int(inter_batch_params["batch_profit"])
        res["profit"]["batch_sum_rel_profit"] = inter_batch_params["batch_rel_profit"]

    #metrikz z prescribedTrades, pokud existuji
    try:
        long_profit = 0
        short_profit = 0
        long_losses = 0
        short_losses = 0
        long_wins = 0
        short_wins = 0
        max_profit = 0
        max_profit_time = None
        max_loss = 0
        max_loss_time = None
        long_cnt = 0
        short_cnt = 0
        sum_wins_profit= 0
        sum_loss = 0

        if "prescribedTrades" in strat.state.vars:
            for trade in strat.state.vars.prescribedTrades:
                if trade.status == TradeStatus.CLOSED:
                    if trade.profit_sum < max_loss:
                        max_loss = trade.profit_sum
                        max_loss_time = trade.last_update
                    if trade.profit_sum > max_profit:
                        max_profit = trade.profit_sum
                        max_profit_time = trade.last_update
                    if trade.direction == TradeDirection.LONG:
                        long_cnt += 1
                        if trade.profit is not None:
                            long_profit += trade.profit
                            if trade.profit < 0:
                                long_losses += trade.profit
                            if trade.profit > 0:
                                long_wins += trade.profit
                    if trade.direction == TradeDirection.SHORT:
                        short_cnt +=1
                        if trade.profit is not None:
                            short_profit += trade.profit
                            if trade.profit < 0:
                                short_losses += trade.profit
                            if trade.profit > 0:
                                short_wins += trade.profit
            sum_wins = long_wins + short_wins
            sum_losses = long_losses + short_losses
            #toto nejak narovnat, mozna diskutovat s Martinem nebo s Vercou

            #zatim to neukazuje moc jasne - poznámka: ztráta by měla být jenom negativní profit, nikoliv nová veličina
            #jediná vyjímka je u max.kumulativní ztráty (drawdown)
            res["profit"]["sum_wins"] = sum_wins
            res["profit"]["sum_losses"] = sum_losses
            res["profit"]["long_cnt"] = long_cnt
            res["profit"]["short_cnt"] = short_cnt
            #celkovy profit za long/short          
            res["profit"]["long_profit"] = round(long_profit,2)
            res["profit"]["short_profit"] = round(short_profit,2)
            #maximalni kumulativni profit (tzn. peaky profitu)
            res["profit"]["max_profit_cum"] = round(max_profit,2)
            res["profit"]["max_profit_cum_time"] = str(max_profit_time)
            #maximalni kumulativni ztrata (tzn. peaky v lossu)
            res["profit"]["max_loss_cum"] = round(max_loss,2)
            res["profit"]["max_loss_time_cum"] = str(max_loss_time)
            res["profit"]["long_wins"] = round(long_wins,2)
            res["profit"]["long_losses"] = round(long_losses,2)
            res["profit"]["short_wins"] = round(short_wins,2)
            res["profit"]["short_losses"] = round(short_losses,2)

            mpt_string = "PT"+str(max_profit_time.hour)+":"+str(max_profit_time.minute) if max_profit_time is not None else "" 
            mlt_string ="LT"+str(max_loss_time.hour)+":"+str(max_loss_time.minute) if max_loss_time is not None else "" 
            rp_string = "RP" + str(float(np.sum(strat.state.rel_profit_cum))) if len(strat.state.rel_profit_cum) >0 else "noRP"

            ##summary pro rychle zobrazeni P333L-222 PT9:30 PL10:30
            res["profit"]["sum"]="P"+str(int(sum_wins))+"L"+str(int(sum_losses))+" "+"MP"+str(int(max_profit))+"ML"+str(int(max_loss))
            
            #summary pokracovani - max casy + rel profity
            res["profit"]["sum_detail"] = mpt_string+" " + mlt_string + rp_string + " "+str(strat.state.rel_profit_cum)

            #rel_profit zprumerovane
            res["profit"]["daily_rel_profit_sum"] = float(np.sum(strat.state.rel_profit_cum)) if len(strat.state.rel_profit_cum) > 0 else 0
            #rel_profit rozepsane zisky
            res["profit"]["daily_rel_profit_list"] = strat.state.rel_profit_cum

            #vlozeni celeho listu
            res["prescr_trades"]=transform_data(strat.state.vars.prescribedTrades, json_serial)

    except NameError:
        pass

    return res

#archives runner and details
def archive_runner(runner: Runner, strat: StrategyInstance, inter_batch_params: dict = None):
    results_metrics = dict()
    print("inside store archive_runner")
    try:
        if strat.bt is not None:
            bp_from = strat.bt.bp_from
            bp_to = strat.bt.bp_to
        else:
            bp_from = None
            bp_to = None

        #get rid of attributes that are links to the models
        strat.state.vars["loaded_models"] = {}

        #ulozime informace o nastavení
        # if self.mode in [Mode.BT, Mode.PREP]:
        #     str(self.dataloader.cache_used)
        
        settings = dict(resolution=strat.state.resolution,
                        rectype=strat.state.rectype,
                        agg_cache_used=strat.dataloader.cache_used if isinstance(strat.dataloader, Trade_Offline_Streamer) else None,
                        configs=dict(
                            CONFIG_HANDLER=dict(profile=cfh.config_handler.active_profile, values=cfh.config_handler.active_config)))

    
        #add profit of this batch iteration to batch_sum_profit
        if inter_batch_params is not None:
            inter_batch_params["batch_profit"] += round(float(strat.state.profit),2)
            inter_batch_params["batch_rel_profit"] += float(np.sum(strat.state.rel_profit_cum)) if len(strat.state.rel_profit_cum) > 0 else 0

        
        #WIP
        #populate result metrics dictionary (max drawdown etc.)
        #list of maximum positions (2000 2x, 1800 x 1, 900 x 1, 100 x 20)
        #list of most profitable trades (pos,avgp + cena)
        #file pro vyvoj: ouptut_metriky_tradeList.py
        results_metrics = populate_metrics_output_directory(strat, inter_batch_params)


        runArchive: RunArchive = RunArchive(id = runner.id,
                                            strat_id = runner.strat_id,
                                            batch_id = runner.batch_id,
                                            name=runner.run_name,
                                            note=runner.run_note,
                                            symbol=runner.run_symbol,
                                            started=runner.run_started,
                                            stopped=runner.run_stopped,
                                            mode=runner.run_mode,
                                            account=runner.run_account,
                                            ilog_save=runner.run_ilog_save,
                                            bt_from=bp_from,
                                            bt_to = bp_to,
                                            strat_json = runner.run_strat_json,
                                            settings = settings,
                                            profit=round(float(strat.state.profit),2),
                                            trade_count=len(strat.state.tradeList),
                                            end_positions=gaka(strat.state.account_variables, "positions"),
                                            end_positions_avgp=gaka(strat.state.account_variables, "avgp", lambda x: round(float(x),3)),
                                            metrics=results_metrics,
                                            stratvars_toml=runner.run_stratvars_toml,
                                            transferables=strat.state.vars["transferables"]
                                            )
        
        #flatten indicators from numpy array
        flattened_indicators = {}
        #pole indicatoru, kazdy ma svoji casovou osu time
        flattened_indicators_list = []
        for key, value in strat.state.indicators.items():
                if isinstance(value, np.ndarray):
                    #print("is numpy", key,value)
                    flattened_indicators[key]= value.tolist()
                    #print("changed numpy:",value.tolist())
                else:
                    #print("is not numpy", key, value)
                    flattened_indicators[key]= value    
        flattened_indicators_list.append(flattened_indicators)
        flattened_indicators = {}
        for key, value in strat.state.cbar_indicators.items():
                if isinstance(value, np.ndarray):
                    #print("is numpy", key,value)
                    flattened_indicators[key]= value.tolist()
                    #print("changed numpy:",value.tolist())
                else:
                    #print("is not numpy", key, value)
                    flattened_indicators[key]= value   
        flattened_indicators_list.append(flattened_indicators)
        # flattened_indicators = {}
        # for key, value in strat.state.secondary_indicators.items():
        #         if isinstance(value, ndarray):
        #             #print("is numpy", key,value)
        #             flattened_indicators[key]= value.tolist()
        #             #print("changed numpy:",value.tolist())
        #         else:
        #             #print("is not numpy", key, value)
        #             flattened_indicators[key]= value   
        # flattened_indicators_list.append(flattened_indicators)


        runArchiveDetail: RunArchiveDetail = RunArchiveDetail(id = runner.id,
                                                            name=runner.run_name,
                                                            bars=strat.state.bars,
                                                            indicators=flattened_indicators_list,
                                                            statinds=strat.state.statinds,
                                                            trades=strat.state.tradeList,
                                                            ext_data=strat.state.extData)
        with lock:
            #resh = db_arch_h.insert(runArchive.__dict__)
            resh = insert_archive_header(runArchive)
            resd = insert_archive_detail(runArchiveDetail)
            #resd = db_arch_d.insert(runArchiveDetail.__dict__)
        print("archive runner finished")
        return 0, str(resh) + " " + str(resd)
    except Exception as e:
        print("Exception in archive_runner: " + str(e) + format_exc())
        return -2, str(e) + format_exc()

# region ARCH HEADER
def migrate_archived_runners() -> list[RunArchive]:
    try:
        res = db_arch_h.all()

        #migration part
        for item in res:
            r = insert_archive_header(RunArchive(**item))
            print("migrated",r)

        return 0, r
    except Exception as e:
        print("Exception in migration: " + str(e) + format_exc())
        return -2, str(e) + format_exc()


def get_all_archived_runners() -> list[RunArchiveView]:
    conn = pool.get_connection()
    try:
        conn.row_factory = Row
        c = conn.cursor()
        c.execute(f"SELECT runner_id, strat_id, batch_id, symbol, name, note, started, stopped, mode, account, bt_from, bt_to, ilog_save, profit, trade_count, end_positions, end_positions_avgp, metrics FROM runner_header")
        rows = c.fetchall()
        results = []
        for row in rows:
            results.append(tr.row_to_runarchiveview(row))
    finally:
        conn.row_factory = None
        pool.release_connection(conn)        
    return 0, results

#with pagination
# def get_all_archived_runners_p(request: DataTablesRequest) -> list[RunArchiveViewPagination]:
#     conn = pool.get_connection()
#     try:
#         conn.row_factory = Row
#         c = conn.cursor()

#         # Query to get the total count of records
#         total_count_query = "SELECT COUNT(*) FROM runner_header"
#         c.execute(total_count_query)
#         total_count = c.fetchone()[0]

#         # Query to get the paginated data
#         paginated_query = f"""
#         SELECT runner_id, strat_id, batch_id, symbol, name, note, started, 
#                stopped, mode, account, bt_from, bt_to, ilog_save, profit, 
#                trade_count, end_positions, end_positions_avgp, metrics 
#         FROM runner_header
#         ORDER BY stopped DESC
#         LIMIT {request.length} OFFSET {request.start}
#         """
#         c.execute(paginated_query)
#         rows = c.fetchall()

#         results = [tr.row_to_runarchiveview(row) for row in rows]

#     finally:
#         conn.row_factory = None
#         pool.release_connection(conn)

#     try:
#         obj = RunArchiveViewPagination(draw=request.draw,recordsTotal=total_count, recordsFiltered=total_count,data=results)
#         return 0, obj
#     except Exception as e:
#         return -2, str(e)+format_exc()

#new version to support search and ordering
#TODO index nad strat_id a batch_id mam?
def get_all_archived_runners_p_original(request: DataTablesRequest) -> Tuple[int, RunArchiveViewPagination]:
    conn = pool.get_connection()
    search_value = request.search.value  # Extract the search value from the request
    try:
        conn.row_factory = Row
        c = conn.cursor()

        # Modify the total count query to include the search filter if search_value is provided
        total_count_query = """
        SELECT COUNT(*) FROM runner_header
        WHERE (:search_value = '' OR strat_id LIKE :search_value OR batch_id LIKE :search_value)
        """
        c.execute(total_count_query, {'search_value': f'%{search_value}%'})
        total_count = c.fetchone()[0]

        # Modify the paginated query to include the search filter if search_value is provided
        paginated_query = f"""
        SELECT runner_id, strat_id, batch_id, symbol, name, note, started, 
               stopped, mode, account, bt_from, bt_to, ilog_save, profit, 
               trade_count, end_positions, end_positions_avgp, metrics 
        FROM runner_header
        WHERE (:search_value = '' OR strat_id LIKE :search_value OR batch_id LIKE :search_value)
        ORDER BY stopped DESC
        LIMIT {request.length} OFFSET {request.start}
        """
        c.execute(paginated_query, {'search_value': f'%{search_value}%'})
        rows = c.fetchall()

        # Filtered count might be different from total count when search is applied
        filtered_count_query = """
        SELECT COUNT(*) FROM runner_header
        WHERE (:search_value = '' OR strat_id LIKE :search_value OR batch_id LIKE :search_value)
        """
        c.execute(filtered_count_query, {'search_value': f'%{search_value}%'})
        filtered_count = c.fetchone()[0]

        results = [tr.row_to_runarchiveview(row) for row in rows]

    finally:
        conn.row_factory = None
        pool.release_connection(conn)

    try:
        obj = RunArchiveViewPagination(draw=request.draw, recordsTotal=total_count, recordsFiltered=filtered_count, data=results)
        return 0, obj
    except Exception as e:
        return -2, str(e) + format_exc()


#new version with batch_id asc sortin https://chat.openai.com/c/64511445-5181-411b-b9d0-51d16930bf71
#Tato verze správně groupuje záznamy se stejnym batch_id (podle maximalniho batche) a non batch zaznamy prolne mezi ne podle jeho stopped date - vlozi zaznam po nebo pred jednotlivou skupinu (dle jejiho max.date)
#diky tomu se mi radi batche a nonbatche spravne a pokud do batche pridame zaznam zobrazi se nam batch nahore
def get_all_archived_runners_p(request: DataTablesRequest) -> Tuple[int, RunArchiveViewPagination]:
    conn = pool.get_connection()
    search_value = request.search.value  # Extract the search value from the request
    try:
        conn.row_factory = Row
        c = conn.cursor()

        # Total count query
        total_count_query = """
        SELECT COUNT(*) FROM runner_header
        WHERE (:search_value = '' OR strat_id LIKE :search_value OR batch_id LIKE :search_value OR symbol like :search_value OR name like :search_value)
        """
        c.execute(total_count_query, {'search_value': f'%{search_value}%'})
        total_count = c.fetchone()[0]

        # Paginated query with advanced sorting logic
        paginated_query = f"""
        WITH GroupedData AS (
            SELECT runner_id, strat_id, batch_id, symbol, name, note, started, 
                stopped, mode, account, bt_from, bt_to, ilog_save, profit, 
                trade_count, end_positions, end_positions_avgp, metrics,
                MAX(stopped) OVER (PARTITION BY batch_id) AS max_stopped,
                SUM(profit) OVER (PARTITION BY batch_id) AS batch_profit,
                COUNT(*) OVER (PARTITION BY batch_id) AS batch_count
            FROM runner_header
            WHERE (:search_value = '' OR strat_id LIKE :search_value OR batch_id LIKE :search_value OR symbol like :search_value OR name like :search_value)
        ),
        InterleavedGroups AS (
            SELECT *,
                CASE 
                    WHEN batch_id IS NOT NULL THEN max_stopped
                    ELSE stopped
                END AS sort_key
            FROM GroupedData
        )
        SELECT runner_id, strat_id, batch_id, symbol, name, note, started, 
            stopped, mode, account, bt_from, bt_to, ilog_save, profit, 
            trade_count, end_positions, end_positions_avgp, metrics, 
            batch_profit, batch_count
        FROM InterleavedGroups
        ORDER BY 
            sort_key DESC,
            CASE WHEN batch_id IS NOT NULL THEN 0 ELSE 1 END,
            stopped DESC
        LIMIT {request.length} OFFSET {request.start}
        """
        c.execute(paginated_query, {'search_value': f'%{search_value}%'})
        rows = c.fetchall()

        # Filtered count query
        filtered_count_query = """
        SELECT COUNT(*) FROM runner_header
        WHERE (:search_value = '' OR strat_id LIKE :search_value OR batch_id LIKE :search_value OR symbol like :search_value OR name like :search_value)
        """
        c.execute(filtered_count_query, {'search_value': f'%{search_value}%'})
        filtered_count = c.fetchone()[0]

        results = [tr.row_to_runarchiveview(row) for row in rows]

    finally:
        conn.row_factory = None
        pool.release_connection(conn)

    try:
        obj = RunArchiveViewPagination(draw=request.draw, recordsTotal=total_count, recordsFiltered=filtered_count, data=results)
        return 0, obj
    except Exception as e:
        return -2, str(e) + format_exc()


#DECOMMS
# def get_all_archived_runners():
#     conn = pool.get_connection()
#     try:
#         conn.row_factory = lambda c, r: orjson.loads(r[0])
#         c = conn.cursor()
#         res = c.execute(f"SELECT data FROM runner_header")
#     finally:
#         conn.row_factory = None
#         pool.release_connection(conn)        
#     return 0, res.fetchall()

#vrati cely kompletni zaznam RunArchive
def get_archived_runner_header_byID(id: UUID) -> RunArchive:
    conn = pool.get_connection()
    try:
        conn.row_factory = Row
        c = conn.cursor()
        c.execute(f"SELECT * FROM runner_header WHERE runner_id='{str(id)}'")
        row = c.fetchone()

        if row:
            return 0, tr.row_to_runarchive(row)
        else:
            return -2, "not found"

    finally:
        conn.row_factory = None
        pool.release_connection(conn)
    

#DECOMM
# #vrátí vsechny datakonkrétní 
# def get_archived_runner_header_byID(id: UUID):
#     conn = pool.get_connection()
#     try:
#         conn.row_factory = lambda c, r: orjson.loads(r[0])
#         c = conn.cursor()
#         result = c.execute(f"SELECT data FROM runner_header WHERE runner_id='{str(id)}'")
#         res= result.fetchone()
#     finally:
#         conn.row_factory = None
#         pool.release_connection(conn)
#     if res==None:
#         return -2, "not found"
#     else:
#         return 0, res

# #vrátí seznam runneru s danym batch_id
# def get_archived_runnerslist_byBatchID(batch_id: str):
#     conn = pool.get_connection()
#     try:
#         cursor = conn.cursor()
#         cursor.execute(f"SELECT runner_id FROM runner_header WHERE batch_id='{str(batch_id)}'")
#         runner_list = [row[0] for row in cursor.fetchall()]
#     finally:
#         pool.release_connection(conn)
#     return 0, runner_list

#update that allows to sort
def get_archived_runnerslist_byBatchID(batch_id: str, sort_order: str = "asc"):
    """
    Fetches all runner records by batch_id, sorted by the 'started' column.

    :param batch_id: The batch ID to filter runners by.
    :param sort_order: The sort order of the 'started' column. Defaults to 'asc'.
                       Accepts 'asc' for ascending or 'desc' for descending order.
    :return: A tuple with the first element being a status code and the second being the list of runner_ids.
    """
    # Validate sort_order
    if sort_order.lower() not in ['asc', 'desc']:
        return -1, []  # Returning an error code and an empty list in case of invalid sort_order
    
    conn = pool.get_connection()
    try:
        cursor = conn.cursor()
        query = f"""SELECT runner_id FROM runner_header 
                    WHERE batch_id=? 
                    ORDER BY datetime(started) {sort_order.upper()}"""
        cursor.execute(query, (batch_id,))
        runner_list = [row[0] for row in cursor.fetchall()]
    finally:
        pool.release_connection(conn)
    return 0, runner_list

def insert_archive_header(archeader: RunArchive):
    conn = pool.get_connection()
    try:
        c = conn.cursor()
        #json_string = orjson.dumps(archeader, default=json_serial, option=orjson.OPT_PASSTHROUGH_DATETIME)
        #print(archeader)

        res = c.execute("""
            INSERT INTO runner_header 
            (runner_id, strat_id, batch_id, symbol, name, note, started, stopped, mode, account, bt_from, bt_to, strat_json, settings, ilog_save, profit, trade_count, end_positions, end_positions_avgp, metrics, stratvars_toml, transferables) 
            VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (str(archeader.id), str(archeader.strat_id), archeader.batch_id, archeader.symbol, archeader.name, archeader.note, archeader.started, archeader.stopped, archeader.mode, archeader.account, archeader.bt_from, archeader.bt_to, orjson.dumps(archeader.strat_json).decode('utf-8'), orjson.dumps(archeader.settings, default=json_serial).decode('utf-8'), archeader.ilog_save, archeader.profit, archeader.trade_count, orjson.dumps(archeader.end_positions).decode('utf-8'), orjson.dumps(archeader.end_positions_avgp).decode('utf-8'), orjson.dumps(archeader.metrics, default=json_serial, option=orjson.OPT_PASSTHROUGH_DATETIME).decode('utf-8'), archeader.stratvars_toml, orjson.dumps(archeader.transferables).decode('utf-8')))

        #retry not yet supported for statement format above
        #res = execute_with_retry(c,statement)
        conn.commit()
    finally:
        pool.release_connection(conn)
    return res.rowcount
    
#edit archived runner note - headers
def edit_archived_runners(runner_id: UUID, archChange: RunArchiveChange):
    try:
        res, sada = get_archived_runner_header_byID(id=runner_id)
        if res == 0:

            #updatujeme pouze note
            try:
                conn = pool.get_connection()
                c = conn.cursor()

                res = c.execute('''
                    UPDATE runner_header 
                    SET note=?
                    WHERE runner_id=?
                    ''',
                    (archChange.note, str(runner_id)))
                
                #retry not yet supported here
                #res = execute_with_retry(c,statement)
                #print(res)
                conn.commit()
            finally:
                pool.release_connection(conn)
            return 0, runner_id
        else:
         return -1, f"Could not find arch runner {runner_id} {res} {sada}"

    except Exception as e:
        errmsg = str(e) + format_exc()
        print(errmsg)
        return -2, errmsg


def delete_report_files(id):
    
    #ZATIM MAME JEN BASIC
    #delete report images
    image_file_name = f"{id}.png"
    image_path = str(MEDIA_DIRECTORY / "basic" / image_file_name)
    try:
        if os.path.exists(image_path):
            os.remove(image_path)
            print(f"File {image_path} has been deleted.")
            return (0, "deleted")
        else:
            print(f"No File {image_path} found to delte.")
            return (1, "not found")
    except Exception as e:
        print(f"An error occurred while deleting the file: {e}")
        return (-1, str(e))        

#delete runners by BatchID
#NOTE: Batch image is deleted on runners level - uvidime jak to bude moc overhead
def delete_archived_runners_byBatchID(batch_id: str):
        res, runner_ids = get_archived_runnerslist_byBatchID(batch_id)

        if res != 0:
            print(f"no batch {batch_id} found")
            return -1, f"no batch {batch_id} found"
        
        res, val = delete_archived_runners_byIDs(runner_ids)

        if res == 0:
            return 0, batch_id
        else:
            print(f"error delete")
            return res, f"ERROR deleting {batch_id} : {val}"


#delete runner in archive and archive detail and runner logs
#predelano do JEDNE TRANSAKCE
def delete_archived_runners_byIDs(ids: list[UUID]):
    try:
        conn = pool.get_connection()
        out = []
        for id in ids:
            c = conn.cursor()
            print(str(id))

           # Get batch_id for the current runner_id
            c.execute("SELECT batch_id FROM runner_header WHERE runner_id = ?", (str(id),))
            batch_id = c.fetchone()
            if batch_id:
                batch_id = batch_id[0]
                # Check if this is the last record with the given batch_id
                c.execute("SELECT COUNT(*) FROM runner_header WHERE batch_id = ?", (batch_id,))
                count = c.fetchone()[0]
                if count == 1:
                    # If it's the last record, call delete_batch_report_files
                    delete_report_files(batch_id)
                    print("Batch report file deleted")

            resh = c.execute(f"DELETE from runner_header WHERE runner_id='{str(id)}';")
            print("header deleted",resh.rowcount)
            resd = c.execute(f"DELETE from runner_detail WHERE runner_id='{str(id)}';")
            print("detail deleted",resd.rowcount)
            resl = c.execute(f"DELETE from runner_logs WHERE runner_id='{str(id)}';")
            print("log deleted",resl.rowcount)
            out.append(str(id) + ":   " + str(resh.rowcount) + " " + str(resd.rowcount) + " " + str(resl.rowcount))
            conn.commit()
            print("commit")

            delete_report_files(id)

        # if resh.rowcount == 0 or resd.rowcount == 0:
        #     return -1, "not found "+str(resh.rowcount) + " " + str(resd.rowcount) + " " + str(resl.rowcount)
        return 0, out
        
    except Exception as e:
        conn.rollback()
        return -2, "ROLLBACKED" + str(e)
    finally:
        pool.release_connection(conn)

#returns number of deleted elements
def delete_archive_header_byID(id: UUID):
    conn = pool.get_connection()
    try:
        c = conn.cursor()
        statement=f"DELETE from runner_header WHERE runner_id='{str(id)}';"
        res = execute_with_retry(c,statement)
        conn.commit()
        print("deleted", res.rowcount)
        #delete report images
        image_file_name = f"report_{id}.png"
        image_path = str(MEDIA_DIRECTORY / image_file_name)
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
                print(f"File {image_path} has been deleted.")
        except Exception as e:
            print(f"An error occurred while deleting the file: {e}")  
    finally:
        pool.release_connection(conn)
    return res.rowcount
# endregion

# region ARCHIVE DETAIL

#FILE SERVICES
#during runner_detail refactoring to file here https://chat.openai.com/c/b18eab9d-1e1c-413b-b25c-ccc180f3b3c2
#vcetne migrace
def get_rd_fn(runner_id):
    return str(RUNNER_DETAIL_DIRECTORY / f"{runner_id}.msgpack.gz")

# Helper functions for file operations
def save_to_file(runner_id, data):
    file_path = get_rd_fn(runner_id)
    with gzip.open(file_path, "wb") as f:
        f.write(msgpack.packb(data))

def read_from_file(runner_id):
    file_path = get_rd_fn(runner_id)
    if os.path.exists(file_path):
        with gzip.open(file_path, "rb") as f:
            return msgpack.unpackb(f.read())
    return None

def delete_file(runner_id):
    file_path = get_rd_fn(runner_id)
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False

#returns number of deleted elements
def delete_archive_detail_byID(id: UUID):
    conn = pool.get_connection()
    try:
        c = conn.cursor()
        statement=f"DELETE from runner_detail WHERE runner_id='{str(id)}';"
        res = execute_with_retry(c,statement)
        conn.commit()
        print("deleted", res.rowcount)
    finally:
        pool.release_connection(conn)
    return res.rowcount


def get_all_archived_runners_detail():
    conn = pool.get_connection()
    try:
        conn.row_factory = lambda c, r: orjson.loads(r[0])
        c = conn.cursor()
        res = c.execute(f"SELECT data FROM runner_detail")
    finally:
        conn.row_factory = None
        pool.release_connection(conn)        
    return 0, res.fetchall()

# def get_archived_runner_details_byID_old(id: UUID):
#     res = db_arch_d.get(where('id') == str(id))
#     if res==None:
#         return -2, "not found"
#     else:
#         return 0, res

#vrátí konkrétní
# def get_archived_runner_details_byID(id: UUID):
#     conn = pool.get_connection()
#     try:
#         conn.row_factory = lambda c, r: orjson.loads(r[0])
#         c = conn.cursor()
#         result = c.execute(f"SELECT data FROM runner_detail WHERE runner_id='{str(id)}'")
#         res= result.fetchone()
#     finally:
#         conn.row_factory = None
#         pool.release_connection(conn)
#     if res==None:
#         return -2, "not found"
#     else:
#         return 0, res
    
#version allowing return of parsed(json) or json string  data
def get_archived_runner_details_byID(id: UUID, parsed: bool = True):
    conn = pool.get_connection()
    try:
        c = conn.cursor()
        result = c.execute(f"SELECT data FROM runner_detail WHERE runner_id='{str(id)}'")
        res = result.fetchone()
    finally:
        pool.release_connection(conn)

    if res is None:
        return -2, "not found"
    else:
        # Return the JSON string directly
        if parsed:
            return 0, orjson.loads(res[0])
        else:
            return 0, res[0]    

def update_archive_detail(id: UUID, archdetail: RunArchiveDetail):
    conn = pool.get_connection()
    try:
        c = conn.cursor()
        json_string = orjson.dumps(archdetail, default=json_serial, option=orjson.OPT_PASSTHROUGH_DATETIME).decode('utf-8')
        statement = "UPDATE runner_detail SET data = ? WHERE runner_id = ?"
        params = (json_string, str(id))
        ##statement = f"UPDATE runner_detail SET data = '{json_string}' WHERE runner_id='{str(id)}'"
        ##print(statement)
        res = execute_with_retry(cursor=c,statement=statement,params=params)
        conn.commit()
    finally:
        pool.release_connection(conn)
    return 0, res.rowcount

def insert_archive_detail(archdetail: RunArchiveDetail):
    conn = pool.get_connection()
    try:
        c = conn.cursor()
        json_string = orjson.dumps(archdetail, default=json_serial, option=orjson.OPT_PASSTHROUGH_DATETIME).decode('utf-8')
        # Use parameterized queries instead of string formatting
        statement = "INSERT INTO runner_detail VALUES (?, ?)"
        params = (str(archdetail.id), json_string)
        res = execute_with_retry(cursor=c, statement=statement, params=params)
        conn.commit()
    finally:
        pool.release_connection(conn)
    return res.rowcount

# endregion

# region TESTLISTS db services
def get_testlists():
    try:
        conn = pool.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, dates FROM test_list")
        rows = cursor.fetchall()
    finally:
        pool.release_connection(conn)
        
    testlists = []
    for row in rows:
        #print(row)
        testlist = TestList(id=row[0], name=row[1], dates=orjson.loads(row[2]))
        testlists.append(testlist)
    
    return 0, testlists    

# endregion

#WIP - instant indicators
def preview_indicator_byTOML(id: UUID, indicator: InstantIndicator, save: bool = True):
    try:
        if indicator.name is None:
            return (-2, ["name is required"])
        
        #print("na zacatku", indicator.toml)

        tomlino = indicator.toml
        jmeno = indicator.name
        #print("tomlino",tomlino)
        #print("jmeno",jmeno)

        # indicator = AttributeDict(**indicator.__dict__)


        # print(indicator)
        # def format_toml_string(toml_string):
        #     return f"'''{toml_string.strip()}'''"
        # print("before",indicator['toml'])
        # indicator['toml'] = format_toml_string(indicator['toml'])
        # print(indicator['toml'])

        # print("jmeno", str(indicator.name))
        # row = f"[stratvars]\n[stratvars.indicators.{str(indicator.name)}]\n"
        # print(row, end='')
        # row = "[stratvars]\n[stratvars.indicators.{indicator.name}]\n"
        # print(row.format(indicator=indicator))
        # print(row)
        res, toml_parsed = parse_toml_string(tomlino)
        if res < 0:
            return (-2, f"toml invalid: {toml_parsed}")
        
        #print("parsed toml", toml_parsed)

        subtype = safe_get(toml_parsed, 'subtype', False)
        if subtype is None:
            return (-2, "subtype invalid")
        
        output = safe_get(toml_parsed, 'output', "bar")
        if output is None:
            return (-2, "output invalid (bar/tick)")

        returns = safe_get(toml_parsed, 'returns', [])

        custom_params = safe_get(toml_parsed, "cp", None)
        print("custom params",custom_params)

        #dotahne runner details
        res, val = get_archived_runner_details_byID(id)
        if res < 0:
            return (-2, "no archived runner {id}")

        detail = RunArchiveDetail(**val)
        #print("toto jsme si dotahnuli", detail.bars)

        #pokud tento indikator jiz je v detailu, tak ho odmazeme - jde o main
        #BAR indikatory
        if indicator.name in detail.indicators[0]:
            del detail.indicators[0][indicator.name]
        #CBAR indikatory
        elif indicator.name in detail.indicators[1]:
            del detail.indicators[1][indicator.name]

        #to same i s pripdadnymi multivystupy
        if len(returns)>0:
            for ind_name in returns:
                if ind_name in detail.indicators[0]:
                    del detail.indicators[0][ind_name]
                #CBAR indikatory
                elif ind_name in detail.indicators[1]:
                    del detail.indicators[1][ind_name]                

        #new dicts
        new_bars = {key: [] for key in detail.bars.keys()}
        new_bars = AttributeDict(**new_bars)
        new_data = {key: None for key in detail.bars.keys()}
        new_data= AttributeDict(**new_data)
        new_inds = {key: [] for key in detail.indicators[0].keys()}
        new_inds = AttributeDict(**new_inds)
        new_tick_inds = {key: [] for key in detail.indicators[1].keys()}
        new_tick_inds = AttributeDict(**new_tick_inds)
        def_account = Account("ACCOUNT1")
        interface = BacktestInterface(symbol="X", bt=None, account=def_account)

        ##dame nastaveni indikatoru do tvaru, ktery stratvars ocekava (pro dynmaicke inicializace)
        stratvars = AttributeDict(indicators=AttributeDict(**{jmeno:toml_parsed}))
        #print("stratvars", stratvars)

        state = StrategyState(name="XX", symbol = "X", stratvars = AttributeDict(**stratvars), interface=interface, accounts=[def_account], account=def_account)

        #inicializujeme stavove promenne a novy indikator v cilovem dict
        if output == "bar":
            state.bars = new_bars
            state.indicators = new_inds
            state.cbar_indicators = detail.indicators[1] #mozna toto vubec neopotrebujeme
            new_inds[indicator.name] = []
            new_inds[indicator.name] = []
            #init multiinputu
            if len(returns)>0:
                for ind_name in returns:
                    new_inds[ind_name] = []
        #pro tick, nechavame bary a nechavame volne pouze tickbary, nad kterymi iterujeme
        else:
            state.bars = new_bars
            state.indicators = new_inds
            state.cbar_indicators = new_tick_inds
            new_tick_inds[indicator.name] = []
            new_tick_inds[indicator.name] = []
            #init multiinputu
            if len(returns)>0:
                for ind_name in returns:
                    new_tick_inds[ind_name] = []

        #pridavame dailyBars z extData
        if hasattr(detail, "ext_data") and "dailyBars" in detail.ext_data:
            state.dailyBars = detail.ext_data["dailyBars"]
            #print("daiyl bars added to state.dailyBars", state.dailyBars)
        print("delka",len(detail.bars["close"]))

        #intitialize indicator mapping - in order to use eval in expression
        local_dict_cbar_inds = {key: state.cbar_indicators[key] for key in state.cbar_indicators.keys() if key != "time"}
        local_dict_inds = {key: state.indicators[key] for key in state.indicators.keys() if key != "time"}
        local_dict_bars = {key: state.bars[key] for key in state.bars.keys() if key != "time"}
        state.ind_mapping = {**local_dict_inds, **local_dict_bars, **local_dict_cbar_inds}
        #print("IND MAPPING DONE:", state.ind_mapping)

        ##intialize required vars from strat init
        state.vars["loaded_models"] = {}
        #state attributes for martingale sizing mngmt
        state.vars["transferables"] = {}
        state.vars["transferables"]["martingale"] = dict(cont_loss_series_cnt=0)

        ##intialize dynamic indicators
        initialize_dynamic_indicators(state)
        #TODO vazit attached data (z toho potrebuji jen transferables, tzn. najit nejak predchozi runner a prelipnout transferables od zacatku)
        #nejspis upravit attach_previous_data a nebo udelat specialni verzi
        #attach_previous_data(state)     

        # print("subtype")   
        # function = "ci."+subtype+"."+subtype
        # print("funkce", function)
        # custom_function = eval(function)
        
        #pokud jde o bar, tak cbary nemennime, nechavame je inicializovane plnou hodnotou pro pripadne dotazeni
        if output == "bar":
            #iterujeme nad bary a on the fly pridavame novou hodnotu do vsech indikatoru a nakonec nad tim spustime indikator
            #tak muzeme v toml pouzit i hodnoty ostatnich indikatoru
            for i in range(len(detail.bars["close"])):
                for key in detail.bars:
                    state.bars[key].append(detail.bars[key][i])
                    #naplnime i data aktualne
                    new_data[key] = state.bars[key][-1]
                for key in detail.indicators[0]:
                    state.indicators[key].append(detail.indicators[0][key][i])

                #inicializujeme 0 v novém indikatoru
                state.indicators[indicator.name].append(0)

                #init pro multipuput
                for ind_name in returns:
                    state.indicators[ind_name].append(0)

                try:
                    populate_dynamic_indicators(new_data, state)
                    # res_code, new_val = custom_function(state, custom_params)
                    # if res_code == 0:
                    #     new_inds[indicator.name][-1]=new_val
                except Exception as e:
                    print(str(e) + format_exc())


            #print("Done", state.indicators[indicator.name])

            #print pro multioutput
            for ind_name in returns:
                print("Done",ind_name, state.indicators[indicator.name])                

            output_dict = {}
            new_inds[indicator.name] = state.indicators[indicator.name]
            
            #ukládáme do ArchRunneru
            detail.indicators[0][indicator.name] = new_inds[indicator.name]
            output_dict[indicator.name] = new_inds[indicator.name]

            #to same s multiinputy:
            if len(returns)>0:
                for ind_name in returns:
                    new_inds[ind_name] = state.indicators[ind_name]
                    detail.indicators[0][ind_name] = new_inds[ind_name]
                    output_dict[ind_name] = new_inds[ind_name]                  

        #TOTOZNE PRO TICK INDICATOR
        else:
            #iterujeme nad bary a on the fly pridavame novou hodnotu do vsech indikatoru a nakonec nad tim spustime indikator
            #OMEZENI ZATIM pro preview jde velmi omezeně používat bary - OTESTOVAT poradne
            new_data = dict(close=0,confirmed=0,high=0,hlcc4=0,index=0,low=0,open=0,resolution=0,time=0,trades=0,updated=0,volume=0,vwap=0)
            bar_idx = 0
            max_bar_idx = len(detail.bars["time"])
            for i in range(len(detail.indicators[1]["time"])):
                for key in detail.indicators[1]:
                    state.cbar_indicators[key].append(detail.indicators[1][key][i])
                    match key:
                        case "time":
                            #pokud existuje bar a indikator s mensim casem vkladame je
                            if bar_idx < max_bar_idx and detail.indicators[1][key][i] >= detail.bars[key][bar_idx]:
                                for bar_key in detail.bars:
                                    state.bars[bar_key].append(detail.bars[bar_key][bar_idx])
                                    #naplnime i data aktualne
                                    new_data[bar_key] = state.bars[bar_key][-1]
                                for ind_key in detail.indicators[0]:
                                    state.indicators[ind_key].append(detail.indicators[0][ind_key][bar_idx])
                                bar_idx += 1                    
                        case "tick_price":
                            new_data['close'] = detail.indicators[1][key][i]
                        # case "tick_volume":
                        #     new_data['volume'] = detail.indicators[1][key][i]

                #inicializujeme 0 v novém indikatoru
                state.cbar_indicators[indicator.name].append(0)

                #init pro multipuput
                for ind_name in returns:
                    state.cbar_indicators[ind_name].append(0)

                try:
                    populate_dynamic_indicators(new_data, state)
                    # res_code, new_val = custom_function(state, custom_params)
                    # if res_code == 0:
                    #     new_inds[indicator.name][-1]=new_val
                except Exception as e:
                    print(str(e) + format_exc())

            #print("Done", state.cbar_indicators[indicator.name])
            output_dict = {}
            new_tick_inds[indicator.name] = state.cbar_indicators[indicator.name]
            
            #ukládáme do ArchRunneru
            detail.indicators[1][indicator.name] = new_tick_inds[indicator.name]
            output_dict[indicator.name] = new_tick_inds[indicator.name] 

            #to same s multiinputy:
            if len(returns)>0:
                for ind_name in returns:
                    new_tick_inds[ind_name] = state.cbar_indicators[ind_name]
                    detail.indicators[1][ind_name] = new_tick_inds[ind_name]
                    output_dict[ind_name] = new_tick_inds[ind_name]       

        #do ext dat ukladame jmeno indikatoru (podle toho oznacuje jako zmenene)

        #inicializace ext_data a instantindicator pokud neexistuje
        if hasattr(detail, "ext_data"):
            if "instantindicators" not in detail.ext_data:
                detail.ext_data["instantindicators"] = []
        else:
            setattr(detail, "ext_data", dict(instantindicators=[]))
        
        #pokud tam je tak odebereme
        for ind in detail.ext_data["instantindicators"]:
            if ind["name"] == indicator.name:
                detail.ext_data["instantindicators"].remove(ind)
                print("removed old from EXT_DATA")

        #a pridame aktualni 
        #NOTE - multivystupy tedy nebudou oznacene na GUI
        detail.ext_data["instantindicators"].append(indicator)
        print("added to EXT_DATA")
        
        #updatneme ArchRunner
        res, val = update_archive_detail(id, detail)
        if res == 0:
            print(f"arch runner {id} updated")


        #output bude nyni ve formatu {key:list}

        #vracime list, kde pozice 0 je bar indicators, pozice 1 je ticks indicators
        if output == "bar":
            return 0, [output_dict, {}]
            #return 0, [new_inds[indicator.name], []]
        else:
            return 0, [{}, output_dict]
            #return 0, [[], new_tick_inds[indicator.name]]

    except Exception as e:
        print(str(e) + format_exc())
        return -2, str(e)

def delete_indicator_byName(id: UUID, indicator: InstantIndicator):
    try:
        #dotahne runner details
        res, val = get_archived_runner_details_byID(id)
        if res < 0:
            return (-2, "no archived runner {id}")

        detail = RunArchiveDetail(**val)
        #print("toto jsme si dotahnuli", detail.bars)

        #pokud tento indikator je v detailu
        if indicator.name in detail.indicators[0]:
            del detail.indicators[0][indicator.name]
            print("values removed from indicators")

        #do ext dat ukladame jmeno indikatoru (podle toho oznacuje jako zmenene)
        if hasattr(detail, "ext_data") and "instantindicators" in detail.ext_data:
                for ind in detail.ext_data["instantindicators"]:
                    if ind["name"] == indicator.name:
                        detail.ext_data["instantindicators"].remove(ind)
                        print("removed from EXT_DATA")

        #updatneme ArchRunner
        res, val = update_archive_detail(id, detail)
        if res == 0:
            print("Archive udpated")

        return 0, val

    except Exception as e:
        print(str(e) + format_exc())
        return -2, str(e)

#returns b
def get_alpaca_history_bars(symbol: str, datetime_object_from: datetime, datetime_object_to: datetime, timeframe: TimeFrame):
    """Returns Bar object
    """
    try:
        result = []
        client = StockHistoricalDataClient(ACCOUNT1_LIVE_API_KEY, ACCOUNT1_LIVE_SECRET_KEY, raw_data=False)
        #datetime_object_from = datetime(2023, 2, 27, 18, 51, 38, tzinfo=datetime.timezone.utc)
        #datetime_object_to = datetime(2023, 2, 27, 21, 51, 39, tzinfo=datetime.timezone.utc)
        bar_request = StockBarsRequest(symbol_or_symbols=symbol,timeframe=timeframe, start=datetime_object_from, end=datetime_object_to, feed=ACCOUNT1_LIVE_FEED)
        #print("before df")
        bars = client.get_stock_bars(bar_request)
        ##pridavame pro jistotu minutu z obou stran kvuli frontendu
        business_hours = {
            # monday = 0, tuesday = 1, ... same pattern as date.weekday()
            "weekdays": [0, 1, 2, 3, 4],
            "from": time(hour=9, minute=28),
            "to": time(hour=16, minute=2)
        }
        for row in bars.data[symbol]:
            if is_open_hours(row.timestamp, business_hours):
                result.append(row)

        # print("df", bars)
        # print(bars.info())
        # bars = bars.droplevel(0)
        # print("after drop", bars)
        # print(bars.info())
        # print("before tz", bars)
        # bars = bars.tz_convert('America/New_York')
        # print("before time", bars)
        # bars = bars.between_time("9:30","16:00")
        # print("after time", bars)
        # bars = bars.reset_index()
        # bars = bars.to_dict(orient="records")
        #print(ohlcvList)
        #ohlcvList = {}

        #bars = {}
        #bars.data[symbol]
        return 0, result
    except Exception as e:
        # Workaround of error when no data foun d AttributeError and has the specific message
        if isinstance(e, AttributeError) and str(e) == "'NoneType' object has no attribute 'items'":
            print("Caught the specific AttributeError: 'NoneType' object has no attribute 'items' means NO DATA FOUND")
            print(str(e) + format_exc())        
            return 0, result            
        else:
            print(str(e) + format_exc())
            if cfh.config_handler.get_val('OFFLINE_MODE'):
                print("OFFLINE MODE ENABLED")
                return 0, []
            return -2, str(e)    
# change_archived_runner
# delete_archived_runner_details

#Example of using config directive
# config_directive = "python"
# ret, res = get_config_item_by_name(config_directive)
# if ret < 0:
#     print(f"Error {res}")
# else:
#     config = orjson.loads(res["json_data"])
#     print(config)