from typing import Any, List
from uuid import UUID, uuid4
import pickle
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockTradesRequest, StockBarsRequest
from alpaca.data.enums import DataFeed
from alpaca.data.timeframe import TimeFrame
from v2realbot.enums.enums import RecordType, StartBarAlign, Mode, Account, OrderSide
from v2realbot.common.model import StrategyInstance, Runner, RunRequest, RunArchive, RunArchiveDetail, RunArchiveChange, Bar, TradeEvent, TestList, Intervals, ConfigItem
from v2realbot.utils.utils import AttributeDict, zoneNY, dict_replace_value, Store, parse_toml_string, json_serial, is_open_hours, send_to_telegram
from v2realbot.utils.ilog import delete_logs
from v2realbot.common.PrescribedTradeModel import Trade, TradeDirection, TradeStatus, TradeStoplossType
from datetime import datetime
from threading import Thread, current_thread, Event, enumerate
from v2realbot.config import STRATVARS_UNCHANGEABLES, ACCOUNT1_LIVE_API_KEY, ACCOUNT1_LIVE_SECRET_KEY, DATA_DIR,BT_FILL_CONS_TRADES_REQUIRED,BT_FILL_LOG_SURROUNDING_TRADES,BT_FILL_CONDITION_BUY_LIMIT,BT_FILL_CONDITION_SELL_LIMIT, GROUP_TRADES_WITH_TIMESTAMP_LESS_THAN
import importlib
from queue import Queue
from tinydb import TinyDB, Query, where
from tinydb.operations import set
import json
from numpy import ndarray
#from rich import print
import pandas as pd
from traceback import format_exc
from datetime import timedelta, time
from threading import Lock
from v2realbot.common.db import pool
#from pyinstrument import Profiler
#adding lock to ensure thread safety of TinyDB (in future will be migrated to proper db)
lock = Lock()

arch_header_file = DATA_DIR + "/arch_header.json"
#arch_detail_file = DATA_DIR + "/arch_detail.json"
#db layer to store runner archive
db_arch_h = TinyDB(arch_header_file, default=json_serial)
#db_arch_d = TinyDB(arch_detail_file, default=json_serial)

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
            if i.run_instance:
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
            i.run_profit = round(float(i.run_instance.state.profit),2)
            i.run_trade_count = len(i.run_instance.state.tradeList)
            i.run_positions = i.run_instance.state.positions
            i.run_avgp = round(float(i.run_instance.state.avgp),3)
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
    try:
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
    except Exception as e:
        return (-2, "Error Exception" + str(e) + format_exc())
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
def capsule(target: object, db: object, inter_batch_params: dict = None):
    
    #TODO zde odchytit pripadnou exceptionu a zapsat do history
    #cil aby padnuti jedne nezpusobilo pad enginu
    try:

        # profiler = Profiler()
        # profiler.start()
        target.start()

        print("Strategy instance stopped. Update runners")
        reason = "SHUTDOWN OK"
    except Exception as e:
        reason = "SHUTDOWN Exception:" + str(e) + format_exc()
        #raise RuntimeError('Exception v runneru POZOR') from e
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
                archive_runner(runner=i, strat=target, inter_batch_params=inter_batch_params)
                #mazeme runner po skonceni instance
                db.runners.remove(i)

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
        return 0, TestList(id=row[0], name=row[1], dates=json.loads(row[2]))


#volano pro batchove spousteni (BT,)
def run_batch_stratin(id: UUID, runReq: RunRequest):
    #pozor toto je test interval id (batch id se pak generuje pro kazdy davkovy run tohoto intervalu)
    if runReq.test_batch_id is None:
        return (-1, "batch_id required for batch run")
    
    if runReq.mode != Mode.BT:
        return (-1, "batch run only for backtest")
    
    print("request values:", runReq)

    print("getting intervals")
    testlist: TestList

    res, testlist = get_testlist_byID(record_id=runReq.test_batch_id)

    if res < 0:
        return (-1, f"not existing ID of testlists with {runReq.test_batch_id}")

#spousti se vlakno s paralelnim behem a vracime ok
    ridici_vlakno = Thread(target=batch_run_manager, args=(id, runReq, testlist), name=f"Batch run controll thread started.")
    ridici_vlakno.start()    
    print(enumerate())

    return 0, f"Batch run started"


#thread, ktery bude ridit paralelni spousteni 
# bud ceka na dokonceni v runners nebo to bude ridit jinak a bude mit jednoho runnera?
# nejak vymyslet.
# logovani zatim jen do print
def batch_run_manager(id: UUID, runReq: RunRequest, testlist: TestList):
    #zde muzu iterovat nad intervaly
    #cekat az dobehne jeden interval a pak spustit druhy
    #pripadne naplanovat beh - to uvidim
    #domyslet kompatibilitu s budoucim automatickym "dennim" spousteni strategii
    #taky budu mit nejaky konfiguracni RUN MANAGER, tak by krome rizeniho denniho runu
    #mohl podporovat i BATCH RUNy.
    batch_id = str(uuid4())[:8]
    runReq.batch_id = batch_id
    print("generated batch_ID", batch_id)

    print("test batch", testlist)

    print("test date", testlist.dates)
    interval: Intervals
    cnt_max = len(testlist.dates)
    cnt = 0
    #promenna pro sdileni mezi runy jednotlivych batchů (např. daily profit)
    inter_batch_params = dict(batch_profit=0)
    note_from_run_request = runReq.note
    for intrvl in testlist.dates:
        cnt += 1
        interval = intrvl
        if interval.note is not None:
            print("mame zde note")
        print("Datum od", interval.start)
        print("Datum do", interval.end)
        print("starting")

        #předání atributů datetime.fromisoformat
        runReq.bt_from = datetime.fromisoformat(interval.start)
        runReq.bt_to = datetime.fromisoformat(interval.end)
        runReq.note = f"Batch {batch_id} #{cnt}/{cnt_max} {testlist.name} N:{interval.note} {note_from_run_request}"

        #protoze jsme v ridicim vlaknu, poustime za sebou jednotlive stratiny v synchronnim modu
        res, id_val = run_stratin(id=id, runReq=runReq, synchronous=True, inter_batch_params=inter_batch_params)
        if res < 0:
            print(f"CHyba v runu #{cnt} od:{runReq.bt_from} do {runReq.bt_to} -> {id_val}")
            break

    print("Batch manager FINISHED")


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
        trades_request = StockTradesRequest(symbol_or_symbols=symbol, feed = DataFeed.SIP, start=datetime_object_from, end=datetime_object_to)
        all_trades = client.get_stock_trades(trades_request)
        #print(all_trades[symbol])
        return 0, all_trades[symbol]
    except Exception as e:
        return (-2, f"problem {e}")
    
def populate_metrics_output_directory(strat: StrategyInstance, inter_batch_params: dict = None):
    """
    WIP
    Spocte zakladni metriky pred ulozenim do archivu

    1) zatim jen max pozice
    """

    tradeList = strat.state.tradeList

    trade_dict = AttributeDict(orderid=[],timestamp=[],symbol=[],side=[],order_type=[],qty=[],price=[],position_qty=[])
    if strat.mode == Mode.BT:
        trade_dict["value"] = []
        trade_dict["cash"] = []
        trade_dict["pos_avg_price"] = []
    for t in tradeList:
        if t.event == TradeEvent.FILL:
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

    res = dict(profit={})
    #filt = max_positions['side'] == 'OrderSide.BUY'
    res["pos_cnt"] = dict(zip(max_positions['qty'], max_positions['count']))

    #naplneni batch sum profitu
    if inter_batch_params is not None:
        res["profit"]["batch_sum_profit"] = inter_batch_params["batch_profit"]

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
        long_cnt = 0
        short_cnt = 0

        if "prescribedTrades" in strat.state.vars:
            for trade in strat.state.vars.prescribedTrades:
                if trade.profit_sum > max_profit:
                    max_profit = trade.profit_sum
                    max_profit_time = trade.last_update
                if trade.status == TradeStatus.ACTIVATED and trade.direction == TradeDirection.LONG:
                    long_cnt += 1
                    if trade.profit is not None:
                        long_profit += trade.profit
                        if trade.profit < 0:
                            long_losses += trade.profit
                        if trade.profit > 0:
                            long_wins += trade.profit
                if trade.status == TradeStatus.ACTIVATED and trade.direction == TradeDirection.SHORT:
                    short_cnt +=1
                    if trade.profit is not None:
                        short_profit += trade.profit
                        if trade.profit < 0:
                            short_losses += trade.profit
                        if trade.profit > 0:
                            short_wins += trade.profit
            res["profit"]["long_cnt"] = long_cnt
            res["profit"]["short_cnt"] = short_cnt          
            res["profit"]["long_profit"] = round(long_profit,2)
            res["profit"]["short_profit"] = round(short_profit,2)
            res["profit"]["long_losses"] = round(long_losses,2)
            res["profit"]["short_losses"] = round(short_losses,2)
            res["profit"]["long_wins"] = round(long_wins,2)
            res["profit"]["short_wins"] = round(short_wins,2)
            res["profit"]["max_profit"] = round(max_profit,2)
            res["profit"]["max_profit_time"] = str(max_profit_time)
            #vlozeni celeho listu
            res["prescr_trades"]=json.loads(json.dumps(strat.state.vars.prescribedTrades, default=json_serial))

    except NameError:
        pass

    return res

#archives runner and details
def archive_runner(runner: Runner, strat: StrategyInstance, inter_batch_params: dict = None):
    results_metrics = dict()
    print("inside archive_runner")
    try:
        if strat.bt is not None:
            bp_from = strat.bt.bp_from
            bp_to = strat.bt.bp_to
        else:
            bp_from = None
            bp_to = None

        #get rid of attributes that are links to the models
        strat.state.vars["loaded_models"] = {}

        settings = dict(resolution=strat.state.timeframe,
                        rectype=strat.state.rectype,
                        configs=dict(
                            GROUP_TRADES_WITH_TIMESTAMP_LESS_THAN=GROUP_TRADES_WITH_TIMESTAMP_LESS_THAN,
                            BT_FILL_CONS_TRADES_REQUIRED=BT_FILL_CONS_TRADES_REQUIRED,
                            BT_FILL_LOG_SURROUNDING_TRADES=BT_FILL_LOG_SURROUNDING_TRADES,
                            BT_FILL_CONDITION_BUY_LIMIT=BT_FILL_CONDITION_BUY_LIMIT,
                            BT_FILL_CONDITION_SELL_LIMIT=BT_FILL_CONDITION_SELL_LIMIT))

        
        #add profit of this batch iteration to batch_sum_profit
        if inter_batch_params is not None:
            inter_batch_params["batch_profit"] += round(float(strat.state.profit),2)
        
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
                                            stratvars = strat.state.vars,
                                            settings = settings,
                                            profit=round(float(strat.state.profit),2),
                                            trade_count=len(strat.state.tradeList),
                                            end_positions=strat.state.positions,
                                            end_positions_avgp=round(float(strat.state.avgp),3),
                                            open_orders=json.dumps(results_metrics, default=json_serial),
                                            stratvars_toml=runner.run_stratvars_toml
                                            )
        
        #flatten indicators from numpy array
        flattened_indicators = {}
        #pole indicatoru, kazdy ma svoji casovou osu time
        flattened_indicators_list = []
        for key, value in strat.state.indicators.items():
                if isinstance(value, ndarray):
                    #print("is numpy", key,value)
                    flattened_indicators[key]= value.tolist()
                    #print("changed numpy:",value.tolist())
                else:
                    #print("is not numpy", key, value)
                    flattened_indicators[key]= value    
        flattened_indicators_list.append(flattened_indicators)
        flattened_indicators = {}
        for key, value in strat.state.cbar_indicators.items():
                if isinstance(value, ndarray):
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

def get_all_archived_runners():
    conn = pool.get_connection()
    try:
        conn.row_factory = lambda c, r: json.loads(r[0])
        c = conn.cursor()
        res = c.execute(f"SELECT data FROM runner_header")
    finally:
        conn.row_factory = None
        pool.release_connection(conn)        
    return 0, res.fetchall()

#vrátí konkrétní
def get_archived_runner_header_byID(id: UUID):
    conn = pool.get_connection()
    try:
        conn.row_factory = lambda c, r: json.loads(r[0])
        c = conn.cursor()
        result = c.execute(f"SELECT data FROM runner_header WHERE runner_id='{str(id)}'")
        res= result.fetchone()
    finally:
        conn.row_factory = None
        pool.release_connection(conn)
    if res==None:
        return -2, "not found"
    else:
        return 0, res

#vrátí seznam runneru s danym batch_id
def get_archived_runnerslist_byBatchID(batch_id: str):
    conn = pool.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT runner_id FROM runner_header WHERE batch_id='{str(batch_id)}'")
        runner_list = [row[0] for row in cursor.fetchall()]
    finally:
        pool.release_connection(conn)
    return 0, runner_list
    
def insert_archive_header(archeader: RunArchive):
    conn = pool.get_connection()
    try:
        c = conn.cursor()
        json_string = json.dumps(archeader, default=json_serial)
        if archeader.batch_id is not None:
            statement = f"INSERT INTO runner_header (runner_id, batch_id, data)  VALUES ('{str(archeader.id)}','{str(archeader.batch_id)}','{json_string}')"
        else:
            statement = f"INSERT INTO runner_header (runner_id, data) VALUES ('{str(archeader.id)}','{json_string}')"
        res = c.execute(statement)
        conn.commit()
    finally:
        pool.release_connection(conn)
    return res.rowcount
    
#edit archived runner note - headers
def edit_archived_runners(runner_id: UUID, archChange: RunArchiveChange):
    try:
        res, sada = get_archived_runner_header_byID(id=runner_id)
        if res == 0:
            archOriginal = RunArchive(**sada)
            archOriginal.note = archChange.note
            try:
                conn = pool.get_connection()
                c = conn.cursor()
                json_string = json.dumps(archOriginal, default=json_serial)
                statement = f"UPDATE runner_header SET data = '{json_string}' WHERE runner_id='{str(runner_id)}'"
                res = c.execute(statement)
                #print(res)
                conn.commit()
            finally:
                pool.release_connection(conn)
            return 0, runner_id
        else:
         return -1, f"Could not find arch runner {runner_id} {res} {sada}"

    except Exception as e:
        return -2, str(e)

#delete runner in archive and archive detail and runner logs
#predelano do JEDNE TRANSAKCE
def delete_archived_runners_byIDs(ids: list[UUID]):
    try:
        conn = pool.get_connection()
        out = []
        for id in ids:
            c = conn.cursor()
            print(str(id))
            resh = c.execute(f"DELETE from runner_header WHERE runner_id='{str(id)}';")
            print("header deleted",resh.rowcount)
            resd = c.execute(f"DELETE from runner_detail WHERE runner_id='{str(id)}';")
            print("detail deleted",resd.rowcount)
            resl = c.execute(f"DELETE from runner_logs WHERE runner_id='{str(id)}';")
            print("log deleted",resl.rowcount)
            out.append(str(id) + ":   " + str(resh.rowcount) + " " + str(resd.rowcount) + " " + str(resl.rowcount))
            conn.commit()
            print("commit")
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
        res = c.execute(f"DELETE from runner_header WHERE runner_id='{str(id)}';")
        conn.commit()
        print("deleted", res.rowcount)
    finally:
        pool.release_connection(conn)
    return res.rowcount
# endregion

# region ARCHIVE DETAIL

#returns number of deleted elements
def delete_archive_detail_byID(id: UUID):
    conn = pool.get_connection()
    try:
        c = conn.cursor()
        res = c.execute(f"DELETE from runner_detail WHERE runner_id='{str(id)}';")
        conn.commit()
        print("deleted", res.rowcount)
    finally:
        pool.release_connection(conn)
    return res.rowcount


def get_all_archived_runners_detail():
    conn = pool.get_connection()
    try:
        conn.row_factory = lambda c, r: json.loads(r[0])
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
def get_archived_runner_details_byID(id: UUID):
    conn = pool.get_connection()
    try:
        conn.row_factory = lambda c, r: json.loads(r[0])
        c = conn.cursor()
        result = c.execute(f"SELECT data FROM runner_detail WHERE runner_id='{str(id)}'")
        res= result.fetchone()
    finally:
        conn.row_factory = None
        pool.release_connection(conn)
    if res==None:
        return -2, "not found"
    else:
        return 0, res

def update_archive_detail(id: UUID, archdetail: RunArchiveDetail):
    conn = pool.get_connection()
    try:
        c = conn.cursor()
        json_string = json.dumps(archdetail, default=json_serial)
        res = c.execute(f"UPDATE runner_detail SET data = '{json_string}' WHERE runner_id='{str(id)}'")
        conn.commit()
    finally:
        pool.release_connection(conn)
    return res.rowcount

def insert_archive_detail(archdetail: RunArchiveDetail):
    conn = pool.get_connection()
    try:
        c = conn.cursor()
        json_string = json.dumps(archdetail, default=json_serial)
        res = c.execute("INSERT INTO runner_detail VALUES (?,?)",[str(archdetail.id), json_string])
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
        testlist = TestList(id=row[0], name=row[1], dates=json.loads(row[2]))
        testlists.append(testlist)
    
    return 0, testlists    

# endregion

# region CONFIG db services
#TODO vytvorit modul pro dotahovani z pythonu (get_from_config(var_name, def_value) {)- stejne jako v js 
#TODO zvazit presunuti do TOML z JSONu
def get_all_config_items():
    conn = pool.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT id, item_name, json_data FROM config_table')
        config_items = [{"id": row[0], "item_name": row[1], "json_data": row[2]} for row in cursor.fetchall()]
    finally:
        pool.release_connection(conn)
    return 0, config_items

# Function to get a config item by ID
def get_config_item_by_id(item_id):
    conn = pool.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT item_name, json_data FROM config_table WHERE id = ?', (item_id,))
        row = cursor.fetchone()
    finally:
        pool.release_connection(conn)
    if row is None:
        return -2, "not found"
    else:
        return 0, {"item_name": row[0], "json_data": row[1]}

# Function to get a config item by ID
def get_config_item_by_name(item_name):
    #print(item_name)
    conn = pool.get_connection()
    try:
        cursor = conn.cursor()
        query = f"SELECT item_name, json_data FROM config_table WHERE item_name = '{item_name}'"
        #print(query)
        cursor.execute(query)
        row = cursor.fetchone()
        #print(row)
    finally:
        pool.release_connection(conn)
    if row is None:
        return -2, "not found"
    else:
        return 0, {"item_name": row[0], "json_data": row[1]}

# Function to create a new config item
def create_config_item(config_item: ConfigItem):
    conn = pool.get_connection()
    try:
        try:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO config_table (item_name, json_data) VALUES (?, ?)', (config_item.item_name, config_item.json_data))
            item_id = cursor.lastrowid
            conn.commit()
            print(item_id)
        finally:
            pool.release_connection(conn)

        return 0, {"id": item_id, "item_name":config_item.item_name, "json_data":config_item.json_data}
    except Exception as e:
        return -2, str(e)

# Function to update a config item by ID
def update_config_item(item_id, config_item: ConfigItem):
    conn = pool.get_connection()
    try:
        try:
            cursor = conn.cursor()
            cursor.execute('UPDATE config_table SET item_name = ?, json_data = ? WHERE id = ?', (config_item.item_name, config_item.json_data, item_id))
            conn.commit()
        finally:
            pool.release_connection(conn)
        return 0, {"id": item_id, **config_item.dict()}
    except Exception as e:
        return -2, str(e)
    
# Function to delete a config item by ID
def delete_config_item(item_id):
    conn = pool.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM config_table WHERE id = ?', (item_id,))
        conn.commit()
    finally:
       pool.release_connection(conn) 
    return 0, {"id": item_id}

# endregion

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
        return -2, str(e)

# change_archived_runner
# delete_archived_runner_details


