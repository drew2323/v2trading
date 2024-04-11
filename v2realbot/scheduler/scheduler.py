import json
import datetime
import v2realbot.controller.services as cs
import v2realbot.controller.run_manager as rm
from v2realbot.common.model import RunnerView, RunManagerRecord, StrategyInstance, Runner, RunRequest, Trade, RunArchive, RunArchiveView, RunArchiveViewPagination, RunArchiveDetail, Bar, RunArchiveChange, TestList, ConfigItem, InstantIndicator, DataTablesRequest, AnalyzerInputs, Market
from uuid import uuid4, UUID
from v2realbot.utils.utils import json_serial, send_to_telegram, zoneNY, zonePRG, zoneUTC, fetch_calendar_data
from datetime import datetime, timedelta, time
from traceback import format_exc
from rich import print
import requests
from v2realbot.config import WEB_API_KEY

#Puvodni varainta schedulera, ktera mela bezet v pravidelnych intervalech
#a spoustet scheduled items v RunManagerRecord
#Nově bylo zrefaktorováno a využitý apscheduler - knihovna v pythonu
#umožňující plánování jobů, tzn. nyní je každý scheduled záznam RunManagerRecord
#naplanovany jako samostatni job a triggerován pouze jednou v daný čas pro start a stop 
#novy kod v aps_scheduler.py

def is_market_day(date):
    cal_dates = fetch_calendar_data(date, date)
    if len(cal_dates) == 0:
        print("No Market Day today")
        return False, cal_dates
    else:
        print("Market is open")
        return True, cal_dates

def get_todays_market_times(market, debug_date = None):
    try:
        if market == Market.US:
            #zjistit vsechny podminky - mozna loopovat - podminky jsou vlevo
            if debug_date is not None:
                nowNY = debug_date
            else:
                nowNY = datetime.now().astimezone(zoneNY)
            nowNY_date = nowNY.date()
            #is market open - nyni pouze US
            stat, calendar_dates = is_market_day(nowNY_date)
            if stat:
            #zatim podpora pouze main session
            #pouze main session
                market_open_datetime = zoneNY.localize(calendar_dates[0].open)
                market_close_datetime = zoneNY.localize(calendar_dates[0].close)
                return 0, (nowNY, market_open_datetime, market_close_datetime)
            else:
                return -1, "Market is closed."
        elif market == Market.CRYPTO:
            now_market_datetime = datetime.now().astimezone(zoneUTC)
            market_open_datetime = datetime.combine(datetime.now(), time.min)
            matket_close_datetime = datetime.combine(datetime.now(), time.max)
            return 0, (now_market_datetime, market_open_datetime, matket_close_datetime)
        else:
            return -1, "Market not supported"
    except Exception as e:
        err_msg = f"General error in {e} {format_exc()}"
        print(err_msg)
        return -2, err_msg

def get_running_strategies():
    # Construct the URL for the local REST API endpoint on port 8000
    api_url = "http://localhost:8000/runners/"

    # Headers for the request
    headers = {
        "X-API-Key": WEB_API_KEY
    }

    try:
        # Make the GET request to the API with the headers
        response = requests.get(api_url, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            runners = response.json()
            print("Successfully fetched runners.")
            strat_ids = []
            ids = []

            for runner_view in runners:
                strat_ids.append(UUID(runner_view["strat_id"]))
                ids.append(UUID(runner_view["id"]))

            return 0, (strat_ids, ids)
        else:
            err_msg = f"Failed to fetch runners. Status Code: {response.status_code}, Response: {response.text}"
            print(err_msg)
            return -2, err_msg
    except requests.RequestException as e:
        err_msg = f"Request failed: {str(e)}"
        print(err_msg)
        return -2, err_msg

def stop_strategy(runner_id):
    # Construct the URL for the local REST API endpoint on port 8000 #option 127.0.0.1
    api_url = f"http://localhost:8000/runners/{runner_id}/stop"

    # Headers for the request
    headers = {
        "X-API-Key": WEB_API_KEY
    }

    try:
        # Make the PUT request to the API with the headers
        response = requests.put(api_url, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            print(f"Runner/strat_id {runner_id} stopped successfully.")
            return 0, runner_id
        else:
            err_msg = f"Failed to stop runner {runner_id}. Status Code: {response.status_code}, Response: {response.text}"
            print(err_msg)
            return -2, err_msg
    except requests.RequestException as e:
        err_msg = f"Request failed: {str(e)}"
        print(err_msg)
        return -2, err_msg
    
def fetch_stratin(stratin_id):
    # Construct the URL for the REST API endpoint
    api_url = f"http://localhost:8000/stratins/{stratin_id}"

    # Headers for the request
    headers = {
        "X-API-Key": WEB_API_KEY
    }

    try:
        # Make the GET request to the API with the headers
        response = requests.get(api_url, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the response as a StrategyInstance object
            strategy_instance = response.json() 
            #strategy_instance = response # Assuming the response is in JSON format
            print(f"StrategyInstance fetched: {stratin_id}")
            return 0, strategy_instance
        else:
            err_msg = f"Failed to fetch StrategyInstance {stratin_id}. " \
                      f"Status Code: {response.status_code}, Response: {response.text}"
            print(err_msg)
            return -1, err_msg
    except requests.RequestException as e:
        err_msg = f"Request failed: {str(e)}"
        print(err_msg)
        return -2, err_msg

#return list of strat_ids that are in the scheduled table more than once
#TODO toto je workaround dokud nebude canndidates logika ze selectu nyni presunuta na fetch_all_run_manager_records a logiku v pythonu
def stratin_occurences():
#get all records
    res, all_records = rm.fetch_all_run_manager_records()
    if res < 0:
        err_msg= f"Error {res} fetching all runmanager records, error {all_records}"
        print(err_msg)
        return -2, err_msg        

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

# in case debug_date is not provided, it takes current time of the given market
    #V budoucnu zde bude loopa pro kazdy obsluhovany market, nyni pouze US 
def startstop_scheduled(debug_date = None, market = "US") -> tuple[int, str]:
    res, sada = get_todays_market_times(market=market, debug_date=debug_date)
    if res == 0:
        market_time_now, market_open_datetime, market_close_datetime = sada
        print(f"OPEN:{market_open_datetime} CLOSE:{market_close_datetime}")
    else:
        return res, sada

    #its market day
    res, candidates = rm.fetch_scheduled_candidates_for_start_and_stop(market_time_now, market)
    if res == 0:
        print(f"Candidates fetched, start: {len(candidates['start'])} stop: {len(candidates['stop'])}")
    else:
        return res, candidates

    if candidates is None or (len(candidates["start"]) == 0 and len(candidates["stop"]) == 0):
        return -1, f"No candidates found for {market_time_now} and {market}"
    #do budoucna, az budou runnery persistovane, bude stav kazde strategie v RunManagerRecord
    #get current runners (mozna optimalizace, fetch per each section start/stop) 
    res, sada = get_running_strategies()
    if res < 0:
        err_msg= f"Error fetching running strategies, error {sada}"
        print(err_msg)
        send_to_telegram(err_msg)
        return -2, err_msg
    strat_ids_running, runnerids_running = sada
    print(f"Currently running: {len(strat_ids_running)}")

    #IERATE over START CAndidates
    record: RunManagerRecord = None
    print(f"START - Looping over {len(candidates['start'])} candidates")
    for record in candidates['start']:
        print("Candidate: ", record)

        if record.weekdays_filter is not None and len(record.weekdays_filter) > 0:
            curr_weekday = market_time_now.weekday()
            if curr_weekday not in record.weekdays_filter:
                print(f"Strategy {record.strat_id} not started, today{curr_weekday} not in weekdays filter {record.weekdays_filter}")
                continue
        #one strat_id can run only once at time
        if record.strat_id in strat_ids_running:
            msg = f"strategy already {record.strat_id} is running"
            continue

        res, result = run_scheduled_strategy(record)
        if res < 0:
            send_to_telegram(result)
            print(result)
        else:
            record.runner_id = UUID(result)
            strat_ids_running.append(record.strat_id)
            runnerids_running.append(record.runner_id)

        record.last_processed = market_time_now
        history_string = f"{market_time_now.isoformat()} strategy STARTED" if res == 0 else "ERROR:" + result

        if record.history is None:
            record.history = history_string
        else:
            record.history += "\n" + history_string

        #update record (nejspis jeste upravit - last_run a history)
        res, set = rm.update_run_manager_record(record.id, record)
        if res == 0:
            print(f"Record in db updated {set}")
            #return 0, set
        else:
            err_msg= f"Error updating {record.id} errir {set} with values {record}. Process stopped."
            print(err_msg)
            send_to_telegram(msg)
            return -2, err_msg #toto stopne dalsi zpracovani, zvazit continue

    #if stop candidates, then fetch existing runners
    stop_candidates_cnt = len(candidates['stop'])

    if stop_candidates_cnt > 0:
        res, repeated_strat_ids = stratin_occurences()
        if res < 0:
            err_msg= f"Error {res} in callin stratin_occurences, error {repeated_strat_ids}"
            send_to_telegram(err_msg)
            return -2, err_msg

    #dalsi OPEN ISSUE pri STOPu:
    # má STOP_TIME strategie záviset na dni v týdnu? jinými slovy pokud je strategie
    # nastavená na 9:30-10 v pondělí. Mohu si ji manuálně spustit v úterý a systém ji neshodí?
    # Zatím to je postaveno, že předpis určuje okno, kde má strategie běžet a mimo tuto dobu bude 
    # automaticky shozena. Druhou možností je potom, že scheduler si striktně hlídá jen strategie,
    # které byly jím zapnuté a ostatní jsou mu putna. V tomto případě pak např. později ručně spuštěmá 
    # strategie (např. kvůli opravě bugu) bude scheduler ignorovat a nevypne ji i kdyz je nastavena na vypnuti.
    # Dopady: weekdays pri stopu a stratin_occurences

    #IERATE over STOP Candidates
    record: RunManagerRecord = None
    print(f"STOP - Looping over {stop_candidates_cnt} candidates")
    for record in candidates['stop']:
        print("Candidate: ", record)

        #Tento šelmostroj se stratin_occurences tu je jen proto, aby scheduler zafungoval i na manualne spustene strategie (ve vetsine pripadu)
        # Při stopu evaluace kandidátů na vypnutí
        #     - pokud mám v schedules jen 1 strategii s konkretnim strat_id, můžu jet přes strat_id - bezici strategie s timto strat_id bude vypnuta (i manualne startnuta)
        #     - pokud jich mám více, musím jet přes runnery uložené v schedules
        #         (v tomto případě je omezení: ručně pouštěna strategii nebude automaticky
        #          stopnuta - systém neví, která to je)

        #zjistime zda strategie bezi

        #strategii mame v scheduleru pouze jednou, muzeme pouzit strat_id
        if record.strat_id not in repeated_strat_ids:
            if record.strat_id not in strat_ids_running:
                msg = f"strategy {record.strat_id} NOT RUNNING"
                print(msg)
                continue
            else:
                #do stop
                id_to_stop = record.strat_id
        #strat_id je pouzito v scheduleru vicekrat, musime pouzit runner_id
        elif record.runner_id is not None and record.runner_id in runnerids_running:
            #do stop
            id_to_stop = record.runner_id
        #no distinctive condition
        else:
            #dont do anything
            print(f"strategy {record.strat_id} not RUNNING or not distinctive (manually launched or two strat_ids in scheduler)")
            continue

        print(f"Requesting STOP {id_to_stop}")
        res, msg = stop_strategy(id_to_stop)
        if res < 0:
            msg = f"ERROR while STOPPING runner_id/strat_id {id_to_stop} {msg}"
            send_to_telegram(msg)      
        else:
            if record.strat_id in strat_ids_running:
                strat_ids_running.remove(record.strat_id)
            if record.runner_id is not None and record.runner_id in runnerids_running:
                runnerids_running.remove(record.runner_id)
            record.runner_id = None

        record.last_processed = market_time_now
        history_string = f"{market_time_now.isoformat()} strategy {record.strat_id}" + "STOPPED" if res == 0 else "ERROR:" + msg
        if record.history is None:
            record.history = history_string
        else:
            record.history += "\n" + history_string

        #update record (nejspis jeste upravit - last_run a history)
        res, set = rm.update_run_manager_record(record.id, record)
        if res == 0:
            print(f"Record updated {set}")
        else:
            err_msg= f"Error updating {record.id} errir {set} with values {record}"
            print(err_msg)
            send_to_telegram(err_msg)  
            return -2, err_msg#toto stopne zpracovani dalsich zaznamu pri chybe, zvazit continue

    return 0, "DONE"

##LIVE or PAPER
#tato verze využívate REST API, po predelani jobu na apscheduler uz muze vyuzivat prime volani cs.run_stratin
#TODO predelat
def run_scheduled_strategy(record: RunManagerRecord):
    #get strat_json
    sada : StrategyInstance = None
    res, sada = fetch_stratin(record.strat_id)
    if res == 0:
        # #TODO toto overit jestli je stejny vystup jako JS
        # print("Sada", sada)
        # #strategy_instance = StrategyInstance(**sada)
        strat_json = json.dumps(sada, default=json_serial)
        # Replace escaped characters with their unescaped versions so it matches the JS output
        #strat_json = strat_json.replace('\\r\\n', '\r\n')
        #print(f"Strat_json fetched, {strat_json}")
    else:
        err_msg= f"Strategy {record.strat_id} not found. ERROR {sada}"
        print(err_msg)
        return -2, err_msg

    #TBD mozna customizovat NOTE

    #pokud neni batch_id pak vyhgeneruju a ulozim do db
    # if record.batch_id is None:
    #     record.batch_id = str(uuid4())[:8]

    api_url = f"http://localhost:8000/stratins/{record.strat_id}/run"

    # Initialize RunRequest with record values
    runReq = {
        "id": str(record.strat_id),
        "strat_json": strat_json,
        "mode": record.mode,
        "account": record.account,
        "ilog_save": record.ilog_save,
        "weekdays_filter": record.weekdays_filter,
        "test_batch_id": record.testlist_id,
        "batch_id": record.batch_id or str(uuid4())[:8],
        "bt_from": record.bt_from.isoformat() if record.bt_from else None,
        "bt_to": record.bt_to.isoformat() if record.bt_to else None,
        "note": f"SCHED {record.start_time}-" + record.stop_time if record.stop_time else "" + record.note if record.note is not None else ""
    }

    # Headers for the request
    headers = {
        "X-API-Key": WEB_API_KEY
    }

    try:
        # Make the PUT request to the API with the headers
        response = requests.put(api_url, json=runReq, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            print(f"Strategy {record.strat_id} started successfully.")
            return 0, response.json()
        else:
            err_msg = f"Strategy {record.strat_id} NOT started. Status Code: {response.status_code}, Response: {response.text}"
            print(err_msg)
            return -2, err_msg
    except requests.RequestException as e:
        err_msg = f"Request failed: {str(e)}"
        print(err_msg)
        return -2, err_msg

    # #intiializae RunRequest with record values
    # runReq = RunRequest(id=record.strat_id,
    #                     strat_json=strat_json,
    #                     mode=record.mode,
    #                     account=record.account,
    #                     ilog_save=record.ilog_save,
    #                     weekdays_filter=record.weekdays_filter,
    #                     test_batch_id=record.testlist_id,
    #                     batch_id=record.batch_id,
    #                     bt_from=record.bt_from,
    #                     bt_to=record.bt_to,
    #                     note=record.note)
    # #call rest API to start strategy

    
    # #start strategy
    # res, sada = cs.run_stratin(id=record.strat_id, runReq=runReq, inter_batch_params=None)
    # if res == 0:
    #     print(f"Strategy {sada} started")
    #     return 0, sada
    # else:
    #     err_msg= f"Strategy {record.strat_id} NOT started. ERROR {sada}"
    #     print(err_msg)
    #     return -2, err_msg


if __name__ == "__main__":
    #use naive datetoime
    debug_date = None
    debug_date = datetime(2024, 2, 16, 16, 37, 0, 0)
    #debug_date = datetime(2024, 2, 16, 10, 30, 0, 0)
    #debug_date = datetime(2024, 2, 16, 16, 1, 0, 0)

    if debug_date is not None:
        # Localize the naive datetime object to the Eastern timezone
        debug_date = zoneNY.localize(debug_date)
        #debugdate formatted as string in format "23.12.2024 9:30"
        formatted_date = debug_date.strftime("%d.%m.%Y %H:%M") 
        print("Scheduler.py NY time: ", formatted_date)
        print("ISoformat", debug_date.isoformat())

    res, msg = startstop_scheduled(debug_date=debug_date, market="US")
    print(f"CALL FINISHED, with {debug_date} RESULT: {res}, {msg}")