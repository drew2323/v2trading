from typing import Any, List
from uuid import UUID, uuid4
import pickle
from v2realbot.enums.enums import RecordType, StartBarAlign, Mode, Account
from v2realbot.common.model import StrategyInstance, Runner, RunRequest
from v2realbot.utils.utils import AttributeDict, zoneNY, dict_replace_value, Store, parse_toml_string
from datetime import datetime
from threading import Thread, current_thread, Event, enumerate
from v2realbot.config import STRATVARS_UNCHANGEABLES
import importlib
from queue import Queue
db = Store()

def get_all_threads():
    res = str(enumerate())
    if len(res) > 0:
        return (0, res)
    else:
        return (-2, "not found")
    
def get_all_runners():
    if len(db.runners) > 0:
        print(db.runners)
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
        if str(i.id) == str(id):
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
async def stratin_realtime_on(id: UUID, rtqueue: Queue):
    for i in db.runners:
        if str(i.id) == str(id):
            i.run_instance.rtqueue = rtqueue
            print("RT QUEUE added")
            return 0
    print("ERROR NOT FOUND")
    return -2

async def stratin_realtime_off(id: UUID):
    for i in db.runners:
        if str(i.id) == str(id):
            i.run_instance.rtqueue = None
            print("RT QUEUE removed")
            return 0
    print("ERROR NOT FOUND")
    return -2

##controller (run_stratefy, pause, stop, reload_params)
def pause_stratin(id: UUID):
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

def stop_stratin(id: UUID = None):
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
                save_history(id=i.id, st=target, runner=i, reason=reason)
                #mazeme runner po skonceni instance
                db.runners.remove(i)

    print("Runner STOPPED")

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
                #do budoucna vylepsit konfiguraci, udelat na frontendu jedno pole config
                #obsahujici cely toml dane strategie
                #nyni predpokladame, ze stratvars a add_data sloupce v gui obsahuji
                #dany TOML element
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
                                            open_rush=open_rush, close_rush=close_rush, pe=pe, se=se)
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
                runner = Runner(id = i.id,
                        run_started = datetime.now(zoneNY),
                        run_pause_ev = pe,
                        run_stop_ev = se,
                        run_thread = vlakno,
                        run_account = runReq.account,
                        run_mode = runReq.mode,
                        run_instance = instance)
                db.runners.append(runner)
                print(db.runners)
                print(i)
                print(enumerate())
                return (0, i.id)
            except Exception as e:
                return (-2, "Exception: "+str(e))
    return (-2, "not found")
