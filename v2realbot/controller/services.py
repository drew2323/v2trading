from typing import Any, List
from uuid import UUID, uuid4
import pickle
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockTradesRequest, StockBarsRequest
from alpaca.data.enums import DataFeed
from alpaca.data.timeframe import TimeFrame
from v2realbot.enums.enums import RecordType, StartBarAlign, Mode, Account
from v2realbot.common.model import StrategyInstance, Runner, RunRequest, RunArchive, RunArchiveDetail, RunArchiveChange, Bar
from v2realbot.utils.utils import AttributeDict, zoneNY, dict_replace_value, Store, parse_toml_string, json_serial, is_open_hours
from v2realbot.utils.ilog import delete_logs
from datetime import datetime
from threading import Thread, current_thread, Event, enumerate
from v2realbot.config import STRATVARS_UNCHANGEABLES, ACCOUNT1_LIVE_API_KEY, ACCOUNT1_LIVE_SECRET_KEY, DATA_DIR,BT_FILL_CONS_TRADES_REQUIRED,BT_FILL_LOG_SURROUNDING_TRADES,BT_FILL_CONDITION_BUY_LIMIT,BT_FILL_CONDITION_SELL_LIMIT
import importlib
from queue import Queue
from tinydb import TinyDB, Query, where
from tinydb.operations import set
import json
from numpy import ndarray

arch_header_file = DATA_DIR + "/arch_header.json"
arch_detail_file = DATA_DIR + "/arch_detail.json"
#db layer to store runner archive
db_arch_h = TinyDB(arch_header_file, default=json_serial)
db_arch_d = TinyDB(arch_detail_file, default=json_serial)

#db layer to store stratins, TBD zmigrovat do TinyDB
db = Store()

def get_all_threads():
    res = str(enumerate())
    if len(res) > 0:
        return (0, res)
    else:
        return (-2, "not found")
    
def get_all_runners():
    if len(db.runners) > 0:
        #print(db.runners)
        for i in db.runners:
            i.run_profit = round(float(i.run_instance.state.profit),2)
            i.run_trade_count = len(i.run_instance.state.tradeList)
            i.run_positions = i.run_instance.state.positions
            i.run_avgp = round(float(i.run_instance.state.avgp),3)
        return (0, db.runners)
    else:
        return (0, [])
 
def get_all_stratins():
    if len(db.stratins) > 0:
        return (0, db.stratins)
    else:
        return (0, [])
     
def get_stratin(id: UUID):
    for i in db.stratins:
        if str(i.id) == str(id):
            return (0, i)
    return (-2, "not found")

def get_runner(id: UUID):
    for i in db.runners:
        if str(i.id) == str(id):
            i.run_profit = round(i.run_instance.state.profit,2)
            i.run_trade_count = len(i.run_instance.state.tradeList)
            i.run_positions = i.run_instance.state.positions
            i.run_avgp = round(i.run_instance.state.avgp,3)
            return (0, i)
    return (-2, "not found")

def create_stratin(si: StrategyInstance):
    #validate toml
    res, stp = parse_toml_string(si.stratvars_conf)
    if res < 0:
        return (-1,"stratvars invalid")
    res, adp = parse_toml_string(si.add_data_conf)
    if res < 0:
        return (-1, "None")
    si.id = uuid4()
    print(si)
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
        return (-1, "stratvars invalid")
    res, adp = parse_toml_string(si.add_data_conf)
    if res < 0:
        return (-1, "add data conf invalid") 
    for i in db.stratins:
        if str(i.id) == str(id):
            print("removing",i)
            db.stratins.remove(i)
            print("adding",si)
            db.stratins.append(si)
            print(db.stratins)
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
            return (-1, "new stratvars format invalid")
        for i in db.stratins:
            if str(i.id) == str(id):
                if not is_stratin_running(id=str(id)):
                    return (-1, "not running")
                res,stp_old = parse_toml_string(i.stratvars_conf)
                if res < 0:
                    return (-1, "current stratin stratvars invalid")
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
    for i in db.runners:
        if str(i.id) == str(id):
            i.run_instance.rtqueue = rtqueue
            print("RT QUEUE added")
            return 0
    print("ERROR NOT FOUND")
    return -2

async def runner_realtime_off(id: UUID):
    for i in db.runners:
        if str(i.id) == str(id):
            i.run_instance.rtqueue = None
            print("RT QUEUE removed")
            return 0
    print("ERROR NOT FOUND")
    return -2

##controller (run_stratefy, pause, stop, reload_params)
def pause_runner(id: UUID):
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

def stop_runner(id: UUID = None):
    chng = []
    for i in db.runners:
        #print(i['id'])
        if id is None or str(i.id) == id:
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
    if len(chng) > 0:
        return (0, "Sent STOP signal to those" + str(chng))
    else:
        return (-2, "not found" + str(id))

def is_stratin_running(id: UUID):
    for i in db.runners:
        if str(i.strat_id) == str(id):
            if i.run_started is not None and i.run_stopped is None:
                return True
    return False

def is_runner_running(id: UUID):
    for i in db.runners:
        if str(i.id) == str(id):
            if i.run_started is not None and i.run_stopped is None:
                return True
    return False

def save_history(id: UUID, st: object, runner: Runner, reason: str = None):
    
    #zkousime precist profit z objektu
    try:
        profit = st.state.profit
        trade_count = len(st.state.tradeList)
    except Exception as e:
        profit = str(e)
    
    for i in db.stratins:
        if str(i.id) == str(id):
            i.history += "START:"+str(runner.run_started)+"STOP:"+str(runner.run_stopped)+"ACC:"+runner.run_account.value+"M:"+runner.run_mode.value+"PROFIT:"+str(round(profit,2))+ "TradeCNT:"+str(trade_count) + "REASON:" + str(reason)
            #i.history += str(runner.__dict__)+"<BR>"
            db.save()
 
#Capsule to run the thread in. Needed in order to update db after strat ends for any reason#
def capsule(target: object, db: object):
    
    #TODO zde odchytit pripadnou exceptionu a zapsat do history
    #cil aby padnuti jedne nezpusobilo pad enginu
    try:
        target.start()
        print("Strategy instance stopped. Update runners")
        reason = "SHUTDOWN OK"
    except Exception as e:
        reason = "SHUTDOWN Exception:" + str(e)
        print(str(e))
        print(reason)
    finally:
        # remove runners after thread is stopped and save results to stratin history
        for i in db.runners:
            if i.run_instance == target:
                i.run_stopped = datetime.now().astimezone(zoneNY)
                i.run_thread = None
                i.run_instance = None
                i.run_pause_ev = None
                i.run_stop_ev = None
                #ukladame radek do historie (pozdeji refactor)
                save_history(id=i.strat_id, st=target, runner=i, reason=reason)
                #store in archive header and archive detail
                archive_runner(runner=i, strat=target)
                #mazeme runner po skonceni instance
                db.runners.remove(i)

    print("Runner STOPPED")
#stratin run
def run_stratin(id: UUID, runReq: RunRequest):
    if runReq.mode == Mode.BT:
        if runReq.bt_from is None:
            return (-1, "start date required for BT")
        if runReq.bt_to is None:
            runReq.bt_to = datetime.now().astimezone(zoneNY)
    
    print("hodnota ID pred",id)
    #volani funkce instantiate_strategy
    for i in db.stratins:
        if str(i.id) == str(id):
            try:
                if is_stratin_running(id=id):
                    return(-1, "already running")
                #validate toml
                res, stp = parse_toml_string(i.stratvars_conf)
                if res < 0:
                    return (-1, "stratvars invalid")
                res, adp = parse_toml_string(i.add_data_conf)
                if res < 0:
                    return (-1, "add data conf invalid") 
                print("jsme uvnitr")
                id = uuid4()
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
                                            ilog_save=runReq.ilog_save)
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
                vlakno = Thread(target=capsule, args=(instance,db), name=instance.name)
                vlakno.start()
                print("Spuštěna", instance.name)
                ##storing the attributtes - pozor pri stopu je zase odstranit
                #id runneru je nove id, stratin se dava dalsiho parametru
                runner = Runner(id = id,
                        strat_id = i.id,
                        run_started = datetime.now(zoneNY),
                        run_pause_ev = pe,
                        run_name = name,
                        run_symbol = symbol,
                        run_note = runReq.note,
                        run_stop_ev = se,
                        run_thread = vlakno,
                        run_account = runReq.account,
                        run_ilog_save = runReq.ilog_save,
                        run_mode = runReq.mode,
                        run_instance = instance)
                db.runners.append(runner)
                print(db.runners)
                print(i)
                print(enumerate())
                return (0, id)
            except Exception as e:
                return (-2, "Exception: "+str(e))
    return (-2, "not found")

def get_trade_history(symbol: str, timestamp_from: float, timestamp_to:float):
    try:
        datetime_object_from = datetime.fromtimestamp(timestamp_from, zoneNY)
        datetime_object_to = datetime.fromtimestamp(timestamp_to, zoneNY)
        #datetime_object_from = datetime(2023, 4, 14, 15, 51, 38, tzinfo=zoneNY)
        #datetime_object_to = datetime(2023, 4, 14, 15, 51, 39, tzinfo=zoneNY)   
        client = StockHistoricalDataClient(ACCOUNT1_LIVE_API_KEY, ACCOUNT1_LIVE_SECRET_KEY, raw_data=False)
        trades_request = StockTradesRequest(symbol_or_symbols=symbol, feed = DataFeed.SIP, start=datetime_object_from, end=datetime_object_to)
        all_trades = client.get_stock_trades(trades_request)
        #print(all_trades[symbol])
        return 0, all_trades[symbol]
    except Exception as e:
        return (-2, f"problem {e}")
    
#archives runner and details
def archive_runner(runner: Runner, strat: StrategyInstance):
    print("inside archive_runner")
    try:
        if strat.bt is not None:
            bp_from = strat.bt.bp_from
            bp_to = strat.bt.bp_to
        else:
            bp_from = None
            bp_to = None

        settings = dict(resolution=strat.state.timeframe,
                        rectype=strat.state.rectype,
                        configs=dict(
                            BT_FILL_CONS_TRADES_REQUIRED=BT_FILL_CONS_TRADES_REQUIRED,
                            BT_FILL_LOG_SURROUNDING_TRADES=BT_FILL_LOG_SURROUNDING_TRADES,
                            BT_FILL_CONDITION_BUY_LIMIT=BT_FILL_CONDITION_BUY_LIMIT,
                            BT_FILL_CONDITION_SELL_LIMIT=BT_FILL_CONDITION_SELL_LIMIT))

        runArchive: RunArchive = RunArchive(id = runner.id,
                                            strat_id = runner.strat_id,
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
                                            stratvars = strat.state.vars,
                                            settings = settings,
                                            profit=round(float(strat.state.profit),2),
                                            trade_count=len(strat.state.tradeList),
                                            end_positions=strat.state.positions,
                                            end_positions_avgp=round(float(strat.state.avgp),3),
                                            open_orders=9999
                                            )
        
        #flatten indicators from numpy array
        flattened_indicators = {}
        for key, value in strat.state.indicators.items():
                if isinstance(value, ndarray):
                    print("is numpy", key,value)
                    flattened_indicators[key]= value.tolist()
                    print("changed numpy:",value.tolist())
                else:
                    print("is not numpy", key, value)
                    flattened_indicators[key]= value    

        runArchiveDetail: RunArchiveDetail = RunArchiveDetail(id = runner.id,
                                                            name=runner.run_name,
                                                            bars=strat.state.bars,
                                                            indicators=flattened_indicators,
                                                            statinds=strat.state.statinds,
                                                            trades=strat.state.tradeList)
        resh = db_arch_h.insert(runArchive.__dict__)
        resd = db_arch_d.insert(runArchiveDetail.__dict__)
        print("archive runner finished")
        return 0, str(resh) + " " + str(resd)
    except Exception as e:
        print("Exception in archive_runner: " + str(e))
        return -2, str(e)

def get_all_archived_runners():
    res = db_arch_h.all()
    return 0, res

#delete runner in archive and archive detail and runner logs
def delete_archived_runners_byID(id: UUID):
    try:
            resh = db_arch_h.remove(where('id') == id)
            resd = db_arch_d.remove(where('id') == id)
            reslogs = delete_logs(id) 
            if len(resh) == 0 or len(resd) == 0 or reslogs ==0:
                return -1, "not found "+str(resh) + " " + str(resd) + " " + str(reslogs)
            return 0, str(resh) + " " + str(resd) + " " + str(reslogs)
    except Exception as e:
        return -2, str(e)
    
#edit archived runner note
def edit_archived_runners(runner_id: UUID, archChange: RunArchiveChange):
    try:
        res = db_arch_h.update(set('note', archChange.note), where('id') == str(runner_id))
        if len(res) == 0:
            return -1, "not found "+str(runner_id)
        return 0, runner_id
    except Exception as e:
        return -2, str(e)

def get_all_archived_runners_detail():
    res = db_arch_d.all()
    return 0, res

def get_archived_runner_details_byID(id: UUID):
    res = db_arch_d.get(where('id') == str(id))
    if res==None:
        return -2, "not found"
    else:
        return 0, res

#returns b
def get_alpaca_history_bars(symbol: str, datetime_object_from: datetime, datetime_object_to: datetime, timeframe: TimeFrame):
    """Returns Bar object
    """
    try:
        client = StockHistoricalDataClient(ACCOUNT1_LIVE_API_KEY, ACCOUNT1_LIVE_SECRET_KEY, raw_data=False)
        #datetime_object_from = datetime(2023, 2, 27, 18, 51, 38, tzinfo=datetime.timezone.utc)
        #datetime_object_to = datetime(2023, 2, 27, 21, 51, 39, tzinfo=datetime.timezone.utc)
        bar_request = StockBarsRequest(symbol_or_symbols=symbol,timeframe=timeframe, start=datetime_object_from, end=datetime_object_to, feed=DataFeed.SIP)
        #print("before df")
        bars = client.get_stock_bars(bar_request)
        result = []
        for row in bars.data[symbol]:
            if is_open_hours(row.timestamp):
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

        return 0, bars.data[symbol]
    except Exception as e:
        return -2, str(e)

# change_archived_runner
# delete_archived_runner_details


