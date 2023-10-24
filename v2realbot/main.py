import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v2realbot.config import WEB_API_KEY, DATA_DIR
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from datetime import datetime
import os
from rich import print
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
import uvicorn
from uuid import UUID
import v2realbot.controller.services as cs
from v2realbot.utils.ilog import get_log_window
from v2realbot.common.model import StrategyInstance, RunnerView, RunRequest, Trade, RunArchive, RunArchiveView, RunArchiveDetail, Bar, RunArchiveChange, TestList, ConfigItem, InstantIndicator
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, WebSocketException, Cookie, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Annotated
import os
import uvicorn
import json
from queue import Queue, Empty
from threading import Thread
import asyncio
from v2realbot.common.db import insert_queue, insert_conn, pool
from v2realbot.utils.utils import json_serial, send_to_telegram, zoneNY, zonePRG
from uuid import uuid4
from sqlite3 import OperationalError
from time import sleep
#from async io import Queue, QueueEmpty
                   
# install()
# ic.configureOutput(includeContext=True)
# def threadName():
#     return '%s |> ' % str(current_thread().name)
# ic.configureOutput(prefix=threadName)
# ic.disable()
"""""   
Main entry point of the bot. Starts strategies according to config file, each
in separate thread.
   
CONF:
{'general': {'make_network_connection': True, 'ping_time': 1200},
            'strategies': [{'name': 'Dokupovaci 1', 'symbol': 'BAC'},
                           {'name': 'Vykladaci', 'symbol': 'year'}]}
"""""

        # <link href="https://unpkg.com/tabulator-tables/dist/css/tabulator.min.css" rel="stylesheet">
        # <script type="text/javascript" src="https://unpkg.com/tabulator-tables/dist/js/tabulator.min.js"></script>
 

X_API_KEY = APIKeyHeader(name='X-API-Key')
  
def api_key_auth(api_key: str = Depends(X_API_KEY)):
    if api_key != WEB_API_KEY:
        raise HTTPException( 
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Forbidden"
        )  
     
app = FastAPI()
root = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(html=True, directory=os.path.join(root, 'static')), name="static")
#app.mount("/", StaticFiles(html=True, directory=os.path.join(root, 'static')), name="www")

security = HTTPBasic()

def get_current_username(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)]
):
    if not (credentials.username == "david") or not (credentials.password == "david"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )

async def get_api_key(
    websocket: WebSocket,
    session: Annotated[str | None, Cookie()] = None,
    api_key: Annotated[str | None, Query()] = None,
):
    if api_key != WEB_API_KEY:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    return session or api_key

#TODO predelat z Async?
@app.get("/static")
async def get(username: Annotated[str, Depends(get_current_username)]):
    return FileResponse("index.html")

@app.websocket("/runners/{runner_id}/ws")
async def websocket_endpoint(
    *, 
    websocket: WebSocket,
    runner_id: str,
    api_key: Annotated[str, Depends(get_api_key)],
):
    await websocket.accept()
    if not cs.is_runner_running(runner_id):
        #await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA, reason="Strat not running")
        raise WebSocketException(code=status.WS_1003_UNSUPPORTED_DATA, reason="Runner not running.")
        return
    else:
        print("stratin exists")
        q: Queue = Queue()
        await cs.runner_realtime_on(id=runner_id, rtqueue=q)

        # tx task; reads data from queue and sends to websocket
        async def websocket_tx_task(ws, _q):
            print("Starting WS tx...")
            
            while True:
                try:            
                    data = _q.get(timeout=10)
                    if data=="break":
                        break
                    await ws.send_text(data)
                    print("WSTX thread received data") #,data)
                except Empty:
                    print("WSTX thread Heartbeat. No data received from queue.")
                    continue
                except WebSocketDisconnect:
                    print("WSTX thread disconnected - terminating tx job")
                    break

            print("WSTX thread terminated")

        def websocket_tx_task_wrapper(ws, _q):
            asyncio.run(websocket_tx_task(ws, _q))

        ws_tx_thread = Thread(target=websocket_tx_task_wrapper, args = (websocket, q,))
        ws_tx_thread.start()
        try:
            while True:
                    data = await websocket.receive_text()
                    print(f"WS RX: {data}")
                    # data = q.get()
                    # print("WSGOTDATA",data)
                #await websocket.receive_text()
                # await websocket.send_text(
                #     f"Session cookie or query token value is: {cookie_or_token}"
                # )
                # data = {'high': 195, 
                #                     'low': 180,
                #                     'volume': 123,
                #                     'close': 185,
                #                     'hlcc4': 123,
                #                     'open': 190,
                #                     'time': "2019-05-25",
                #                     'trades':123,
                #                     'resolution':123,
                #                     'confirmed': 123,
                #                     'vwap': 123,
                #                     'updated': 123,
                #                     'index': 123}
                #print("WSRT received data", data)
                #await websocket.send_text(data)
        except WebSocketDisconnect:
            print("CLIENT DISCONNECTED for", runner_id)
        finally:
            q.put("break")
            await cs.runner_realtime_off(runner_id)

@app.get("/threads/", dependencies=[Depends(api_key_auth)])
def _get_all_threads():
    res, set =cs.get_all_threads()
    if res == 0:
        return set
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No data found")

@app.get("/runners/", dependencies=[Depends(api_key_auth)])
def _get_all_runners() -> list[RunnerView]:
    res, set =cs.get_all_runners()
    if res == 0:
        return set
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No data found")

@app.get("/runners/{runner_id}", dependencies=[Depends(api_key_auth)])
def _get_runner(runner_id) -> RunnerView:
    res, set = cs.get_runner(runner_id)
    if res == 0:
        return set
    else:
        raise HTTPException(status_code=404, detail=f"No runner with id: {runner_id} a {set}")


@app.get("/stratins/", dependencies=[Depends(api_key_auth)])
def _get_all_stratins() -> list[StrategyInstance]:
    res, set =cs.get_all_stratins()
    if res == 0:
        return set
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No data found")

@app.post("/stratins/", dependencies=[Depends(api_key_auth)], status_code=status.HTTP_200_OK)
def _create_stratin(new_stratin: StrategyInstance):
    res, id = cs.create_stratin(si=new_stratin)
    if res == 0: return id
    else:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f"Error not created: {res}:{id}")
 
@app.patch("/stratins/{stratin_id}", dependencies=[Depends(api_key_auth)])
def _modify_stratin(stratin: StrategyInstance, stratin_id: UUID):
    if cs.is_stratin_running(id=stratin_id):
        res,id = cs.modify_stratin_running(si=stratin, id=stratin_id)
    else: 
        res, id = cs.modify_stratin(si=stratin, id=stratin_id)
    if res == 0: return id
    elif res == -2:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Error not found: {res}:{id}")
    else:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f"Error not changed: {res}:{id}")
 
@app.get("/stratins/{stratin_id}", dependencies=[Depends(api_key_auth)])
def _get_stratin(stratin_id) -> StrategyInstance:
    res, set = cs.get_stratin(stratin_id)
    if res == 0:
        return set
    else:
        raise HTTPException(status_code=404, detail=f"No stratin with id: {stratin_id} a {set}")

@app.put("/stratins/{stratin_id}/run", dependencies=[Depends(api_key_auth)], status_code=status.HTTP_200_OK)
def _run_stratin(stratin_id: UUID, runReq: RunRequest):
    #print(runReq)
    if runReq.bt_from is not None and runReq.bt_from.tzinfo is None:
        runReq.bt_from = zonePRG.localize(runReq.bt_from)

    if runReq.bt_to is not None and runReq.bt_to.tzinfo is None:
        runReq.bt_to = zonePRG.localize(runReq.bt_to)  
    #pokud jedeme nad test intervaly anebo je požadováno více dní - pouštíme jako batch day by day
    #do budoucna dát na FE jako flag
    if runReq.test_batch_id is not None or (runReq.bt_from.date() != runReq.bt_to.date()):
        res, id = cs.run_batch_stratin(id=stratin_id, runReq=runReq)
    else:
        res, id = cs.run_stratin(id=stratin_id, runReq=runReq)
    if res == 0: return id
    elif res < 0:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f"Error: {res}:{id}")

@app.put("/runners/{runner_id}/pause", dependencies=[Depends(api_key_auth)], status_code=status.HTTP_200_OK)
def _pause_runner(runner_id):
    res, id = cs.pause_runner(id=runner_id)
    if res == 0: return id
    elif res < 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Error: {res}:{id}")

@app.put("/runners/{runner_id}/stop", dependencies=[Depends(api_key_auth)], status_code=status.HTTP_200_OK)
def _stop_runner(runner_id):
    res, id = cs.stop_runner(id=runner_id)
    if res == 0: return id
    elif res < 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Error: {res}:{id}")

@app.delete("/stratins/{stratin_id}", dependencies=[Depends(api_key_auth)], status_code=status.HTTP_200_OK)
def _delete_stratin(stratin_id):
    res, id = cs.delete_stratin(id=stratin_id)
    if res == 0: return id
    elif res < 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Error: {res}:{id}")

@app.put("/runners/stop", dependencies=[Depends(api_key_auth)], status_code=status.HTTP_200_OK)
def stop_all_runners():
    res, id = cs.stop_runner()
    if res == 0: return id
    elif res < 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Error: {res}:{id}")

@app.get("/tradehistory/{symbol}", dependencies=[Depends(api_key_auth)])
def get_trade_history(symbol: str, timestamp_from: float, timestamp_to:float) -> list[Trade]:
    res, set = cs.get_trade_history(symbol, timestamp_from, timestamp_to)
    if res == 0:
        return set
    else:
        raise HTTPException(status_code=404, detail=f"No trades found {res}")

@app.put("/migrate", dependencies=[Depends(api_key_auth)], status_code=status.HTTP_200_OK)
def migrate():
    lock_file = DATA_DIR + "/migr.lock"
    
    #if lock file not present, we can continue and create the file
    if not os.path.exists(lock_file):

        #migration code
        print("migration code STARTED")
        try:
            # Helper function to transform a row to a RunArchive object
            def row_to_object(row: dict) -> RunArchive:
                return RunArchive(
                    id=row.get('id'),
                    strat_id=row.get('strat_id'),
                    batch_id=row.get('batch_id'),
                    symbol=row.get('symbol'),
                    name=row.get('name'),
                    note=row.get('note'),
                    started=row.get('started'),
                    stopped=row.get('stopped'),
                    mode=row.get('mode'),
                    account=row.get('account'),
                    bt_from=row.get('bt_from'),
                    bt_to=row.get('bt_to'),
                    strat_json=row.get('strat_json'),
                    stratvars=row.get('stratvars'),
                    settings=row.get('settings'),
                    ilog_save=row.get('ilog_save'),
                    profit=row.get('profit'),
                    trade_count=row.get('trade_count'),
                    end_positions=row.get('end_positions'),
                    end_positions_avgp=row.get('end_positions_avgp'),
                    metrics=row.get('open_orders'),
                    #metrics=json.loads(row.get('metrics')) if row.get('metrics') else None,
                    stratvars_toml=row.get('stratvars_toml')
                )

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

            set = list[RunArchive]

            def migrate_to_columns(ra: RunArchive):
                conn = pool.get_connection()
                try:

                    c = conn.cursor()
                    # statement = f"""UPDATE runner_header SET
                    #     strat_id='{str(ra.strat_id)}',
                    #     batch_id='{ra.batch_id}',
                    #     symbol='{ra.symbol}',
                    #     name='{ra.name}',
                    #     note='{ra.note}',
                    #     started='{ra.started}',
                    #     stopped='{ra.stopped}',
                    #     mode='{ra.mode}',
                    #     account='{ra.account}',
                    #     bt_from='{ra.bt_from}',
                    #     bt_to='{ra.bt_to}',
                    #     strat_json='ra.strat_json)',
                    #     settings='{ra.settings}',
                    #     ilog_save='{ra.ilog_save}',
                    #     profit='{ra.profit}',
                    #     trade_count='{ra.trade_count}',
                    #     end_positions='{ra.end_positions}',
                    #     end_positions_avgp='{ra.end_positions_avgp}',
                    #     metrics='{ra.metrics}',
                    #     stratvars_toml="{ra.stratvars_toml}"
                    # WHERE runner_id='{str(ra.strat_id)}'
                    # """
                    # print(statement)

                    res = c.execute('''
                        UPDATE runner_header 
                        SET strat_id=?, batch_id=?, symbol=?, name=?, note=?, started=?, stopped=?, mode=?, account=?, bt_from=?, bt_to=?, strat_json=?, settings=?, ilog_save=?, profit=?, trade_count=?, end_positions=?, end_positions_avgp=?, metrics=?, stratvars_toml=?
                        WHERE runner_id=?
                        ''',
                        (str(ra.strat_id), ra.batch_id, ra.symbol, ra.name, ra.note, ra.started, ra.stopped, ra.mode, ra.account, ra.bt_from, ra.bt_to, json.dumps(ra.strat_json), json.dumps(ra.settings), ra.ilog_save, ra.profit, ra.trade_count, ra.end_positions, ra.end_positions_avgp, json.dumps(ra.metrics), ra.stratvars_toml, str(ra.id)))

                    conn.commit()
                finally:

                    pool.release_connection(conn)        
                return 0, res

            res, set = get_all_archived_runners()
            print(f"fetched {len(set)}")
            for row in set:
                ra: RunArchive = row_to_object(row)
                print(f"item {ra.id}")
                res, val = migrate_to_columns(ra)
                print(res,val)
                print("migrated", ra.id)




        finally:
            open(lock_file, 'w').close()

            return 0
             
        # res, set =cs.migrate_archived_runners()
        # if res == 0:
        #     open(lock_file, 'w').close()
        #     return set
        # else:
        #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No data found")


    else:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f"Migration lock file present {lock_file}")


#ARCHIVE RUNNERS SECTION
# region Archive runners

#get all archived runners headers - just RunArchiveView
@app.get("/archived_runners/", dependencies=[Depends(api_key_auth)])
def _get_all_archived_runners() -> list[RunArchiveView]:
    res, set =cs.get_all_archived_runners()
    if res == 0:
        return set
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No data found")

#get complete header data for specific archivedRunner = RunArchive
@app.get("/archived_runners/{runner_id}", dependencies=[Depends(api_key_auth)])
def _get_archived_runner_header_byID(runner_id: UUID) -> RunArchive:
    res, set =cs.get_archived_runner_header_byID(runner_id)
    if res == 0:
        return set
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No data found")

#delete archive runner from header and detail
@app.delete("/archived_runners/", dependencies=[Depends(api_key_auth)], status_code=status.HTTP_200_OK)
def _delete_archived_runners_byIDs(runner_ids: list[UUID]):
    res, id = cs.delete_archived_runners_byIDs(ids=runner_ids)
    if res == 0: return id
    elif res < 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Error: {res}:{id}")

#WIP - TOM indicator preview from frontend
#return indicator value for archived runner
@app.put("/archived_runners/{runner_id}/previewindicator", dependencies=[Depends(api_key_auth)], status_code=status.HTTP_200_OK)
def _preview_indicator_byTOML(runner_id: UUID, indicator: InstantIndicator) -> list[float]:
    #mozna pak pridat name
    res, vals = cs.preview_indicator_byTOML(id=runner_id, indicator=indicator)
    if res == 0: return vals
    elif res == -1:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Error: {res}:{vals}")
    else:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f"Error not changed: {res}:{runner_id}:{vals}")

#delete instant indicator from detail
@app.delete("/archived_runners/{runner_id}/previewindicator", dependencies=[Depends(api_key_auth)], status_code=status.HTTP_200_OK)
def _delete_indicator_byName(runner_id: UUID, indicator: InstantIndicator):
    #mozna pak pridat name
    res, vals = cs.delete_indicator_byName(id=runner_id, indicator=indicator)
    if res == 0: return vals
    elif res == -1:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Error: {res}:{vals}")
    else:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f"Error not changed: {res}:{runner_id}:{vals}")



#edit archived runner ("note",..)
@app.patch("/archived_runners/{runner_id}", dependencies=[Depends(api_key_auth)])
def _edit_archived_runners(archChange: RunArchiveChange, runner_id: UUID):
    res, id = cs.edit_archived_runners(runner_id=runner_id, archChange=archChange)
    if res == 0: return runner_id
    elif res == -1:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Error not found: {res}:{runner_id}")
    else:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f"Error not changed: {res}:{runner_id}:{id}")
    
#get all archived runners detail
@app.get("/archived_runners_detail/", dependencies=[Depends(api_key_auth)])
def _get_all_archived_runners_detail() -> list[RunArchiveDetail]:
    res, set =cs.get_all_archived_runners_detail()
    if res == 0:
        return set
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No data found")

#get archived runners detail by id
@app.get("/archived_runners_detail/{runner_id}", dependencies=[Depends(api_key_auth)])
def _get_archived_runner_details_byID(runner_id) -> RunArchiveDetail:
    res, set = cs.get_archived_runner_details_byID(runner_id)
    if res == 0:
        return set
    else:
        raise HTTPException(status_code=404, detail=f"No runner with id: {runner_id} a {set}")

#get archived runners detail by id
@app.get("/archived_runners_log/{runner_id}", dependencies=[Depends(api_key_auth)])
def _get_archived_runner_log_byID(runner_id: UUID, timestamp_from: float, timestamp_to: float) -> list[dict]:
    res = get_log_window(runner_id,timestamp_from, timestamp_to)
    if len(res) > 0:
        return res
    else:
        raise HTTPException(status_code=404, detail=f"No logs found with id: {runner_id} and between {timestamp_from} and {timestamp_to}")

# endregion 

#get alpaca history bars
@app.get("/history_bars/", dependencies=[Depends(api_key_auth)])
def _get_alpaca_history_bars(symbol: str, datetime_object_from: datetime, datetime_object_to: datetime, timeframe_amount: int, timeframe_unit: TimeFrameUnit) -> list[Bar]:
    print("Requested dates ",datetime_object_from,datetime_object_to)
    res, set =cs.get_alpaca_history_bars(symbol, datetime_object_from, datetime_object_to, TimeFrame(amount=timeframe_amount,unit=timeframe_unit))
    if res == 0:
        return set
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No data found {res} {set}")

#TestList APIS - do budoucna predelat SQL do separatnich funkci
@app.post('/testlists/', dependencies=[Depends(api_key_auth)])
def create_record(testlist: TestList):
    # Generate a new UUID for the record
    testlist.id = str(uuid4())[:8]

    # Insert the record into the database
    conn = pool.get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO test_list (id, name, dates) VALUES (?, ?, ?)", (testlist.id, testlist.name, json.dumps(testlist.dates, default=json_serial)))
    conn.commit()
    pool.release_connection(conn)
    return testlist


# API endpoint to retrieve all records
@app.get('/testlists/', dependencies=[Depends(api_key_auth)])
def get_testlists():
    res, sada = cs.get_testlists()
    if res == 0:
        return sada
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No data found")

# API endpoint to retrieve a single record by ID
@app.get('/testlists/{record_id}')
def get_testlist(record_id: str):
    res, testlist = cs.get_testlist_byID(record_id=record_id)

    if res == 0:
        return testlist
    elif res < 0:
        raise HTTPException(status_code=404, detail='Record not found')

# API endpoint to update a record
@app.put('/testlists/{record_id}')
def update_testlist(record_id: str, testlist: TestList):
    # Check if the record exists
    conn = pool.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM test_list WHERE id = ?", (record_id,))
    row = cursor.fetchone()
    
    if row is None:
        raise HTTPException(status_code=404, detail='Record not found')
    
    # Update the record in the database
    cursor.execute("UPDATE test_list SET name = ?, dates = ? WHERE id = ?", (testlist.name, json.dumps(testlist.dates, default=json_serial), record_id))
    conn.commit()
    pool.release_connection(conn)
    
    testlist.id = record_id
    return testlist

# API endpoint to delete a record
@app.delete('/testlists/{record_id}')
def delete_testlist(record_id: str):
    # Check if the record exists
    conn = pool.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM test_list WHERE id = ?", (record_id,))
    row = cursor.fetchone()
    
    if row is None:
        raise HTTPException(status_code=404, detail='Record not found')
    
    # Delete the record from the database
    cursor.execute("DELETE FROM test_list WHERE id = ?", (record_id,))
    conn.commit()
    pool.release_connection(conn)
    
    return {'message': 'Record deleted'}

# region CONFIG APIS

# Get all config items
@app.get("/config-items/", dependencies=[Depends(api_key_auth)])
def get_all_items() -> list[ConfigItem]:
    res, sada = cs.get_all_config_items()
    if res == 0:
        return sada
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No data found")


# Get a config item by ID
@app.get("/config-items/{item_id}", dependencies=[Depends(api_key_auth)])
def get_item(item_id: int)-> ConfigItem:
    res, sada = cs.get_config_item_by_id(item_id)
    if res == 0:
        return sada
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No data found")

# Get a config item by Name
@app.get("/config-items-by-name/", dependencies=[Depends(api_key_auth)])
def get_item(item_name: str)-> ConfigItem:
    res, sada = cs.get_config_item_by_name(item_name)
    if res == 0:
        return sada
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No data found")

# Create a new config item
@app.post("/config-items/", dependencies=[Depends(api_key_auth)], status_code=status.HTTP_200_OK)
def create_item(config_item: ConfigItem) -> ConfigItem:
    res, sada = cs.create_config_item(config_item)
    if res == 0: return sada
    else:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f"Error not created: {res}:{id} {sada}")
 

# Update a config item by ID
@app.put("/config-items/{item_id}", dependencies=[Depends(api_key_auth)])
def update_item(item_id: int, config_item: ConfigItem) -> ConfigItem:
    res, sada = cs.get_config_item_by_id(item_id)
    if res != 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No data found")

    res, sada = cs.update_config_item(item_id, config_item)
    if res == 0: return sada
    else:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f"Error not created: {res}:{id}")


# Delete a config item by ID
@app.delete("/config-items/{item_id}", dependencies=[Depends(api_key_auth)])
def delete_item(item_id: int) -> dict:
    res, sada = cs.get_config_item_by_id(item_id)
    if res != 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No data found")

    res, sada = cs.delete_config_item(item_id)
    if res == 0: return sada
    else:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f"Error not created: {res}:{id}")

# endregion


# Thread function to insert data from the queue into the database
def insert_queue2db():
    print("starting insert_queue2db thread")
    while True:
        # Retrieve data from the queue
        data = insert_queue.get()

        try:
            # Unpack the data
            runner_id, loglist = data
            c = insert_conn.cursor()
            insert_data = []
            for i in loglist:
                row = (str(runner_id), i["time"], json.dumps(i, default=json_serial))
                insert_data.append(row)
            c.executemany("INSERT INTO runner_logs VALUES (?,?,?)", insert_data)
            insert_conn.commit()
            # Mark the task as done in the queue
        except OperationalError as e:
            send_to_telegram("insert logs daemon returned" + str(e) + "RETRYING")
            if "database is locked" in str(e):
                # Database is locked, wait for a while and retry
                insert_queue.put(data)  # Put the data back into the queue for retry
                sleep(1)  # You can adjust the sleep duration
            else:
                raise  # If it's another error, raise it     

#join cekej na dokonceni vsech
for i in cs.db.runners:
    i.run_thread.join()

if __name__ == "__main__":
    try:
        #TOTO predelat na samostatnou tridu typu vlakna a dat do separatniho souboru, draft jiz na chatgpt
        #spusteni vlakna pro zapis logů (mame single write vlakno, thready dodávají pres queue)
        insert_thread = Thread(target=insert_queue2db)
        insert_thread.start()

        uvicorn.run("__main__:app", host="0.0.0.0", port=8000, reload=False)
    finally:
        print("closing insert_conn connection")
        insert_conn.close()
        print("closed")
##TODO pridat moznost behu na PAPER a LIVE per strategie

# zjistit zda order notification websocket muze bezet na obou soucasne
# pokud ne, mohl bych vyuzivat jen zive data
# a pro paper trading(live interface) a notifications bych pouzival separatni paper ucet
# to by asi slo

