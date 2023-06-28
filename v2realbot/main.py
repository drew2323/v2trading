import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v2realbot.enums.enums import Mode, Account
from v2realbot.config import WEB_API_KEY
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from datetime import datetime
#from icecream import install, ic
import os
from rich import print
from threading import current_thread
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
import uvicorn
from uuid import UUID
import v2realbot.controller.services as cs
from v2realbot.utils.ilog import get_log_window
from v2realbot.common.model import StrategyInstance, RunnerView, RunRequest, Trade, RunArchive, RunArchiveDetail, Bar, RunArchiveChange
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, WebSocketException, Cookie, Query
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Annotated
import os
import uvicorn
import json
from queue import Queue, Empty
from threading import Thread
import asyncio
from v2realbot.common.db import insert_queue, insert_conn
from v2realbot.utils.utils import json_serial
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

#ARCHIVE RUNNERS SECTION

#get all archived runners header
@app.get("/archived_runners/", dependencies=[Depends(api_key_auth)])
def _get_all_archived_runners() -> list[RunArchive]:
    res, set =cs.get_all_archived_runners()
    if res == 0:
        return set
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No data found")

#delete archive runner from header and detail
@app.delete("/archived_runners/{runner_id}", dependencies=[Depends(api_key_auth)], status_code=status.HTTP_200_OK)
def _delete_archived_runners_byID(runner_id):
    res, id = cs.delete_archived_runners_byID(id=runner_id)
    if res == 0: return id
    elif res < 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Error: {res}:{id}")

#edit archived runner ("note",..)
@app.patch("/archived_runners/{runner_id}", dependencies=[Depends(api_key_auth)])
def _edit_archived_runners(archChange: RunArchiveChange, runner_id: UUID):
    res, id = cs.edit_archived_runners(runner_id=runner_id, archChange=archChange)
    if res == 0: return runner_id
    elif res == -1:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Error not found: {res}:{runner_id}")
    else:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f"Error not changed: {res}:{runner_id}")
    
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

#get alpaca history bars
@app.get("/history_bars/", dependencies=[Depends(api_key_auth)])
def _get_alpaca_history_bars(symbol: str, datetime_object_from: datetime, datetime_object_to: datetime, timeframe_amount: int, timeframe_unit: TimeFrameUnit) -> list[Bar]:
    res, set =cs.get_alpaca_history_bars(symbol, datetime_object_from, datetime_object_to, TimeFrame(amount=timeframe_amount,unit=timeframe_unit))
    if res == 0:
        return set
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No data found {res} {set}")

# Thread function to insert data from the queue into the database
def insert_queue2db():
    print("starting insert_queue2db thread")
    while True:
        # Retrieve data from the queue
        data = insert_queue.get()

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

