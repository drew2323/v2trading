from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, WebSocketException, Cookie, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from typing import Annotated
import os
import uvicorn
import orjson
from datetime import datetime
from v2realbot.utils.utils import zoneNY

app = FastAPI()

root = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(root, 'static')), name="static")


html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
        <script type="text/javascript" src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"
></script>
    </head>
    <body>
        <h1>Realtime chart</h1>
        <h2>Your ID: <span id="ws-id"></span></h2>
        <h3>Status: <span id="status">Not connected</span></h3>
        <form action="" onsubmit="sendMessage(event)">
            <label>Runner ID: <input type="text" id="runnerId" autocomplete="off" value="foo"/></label>
            <label>Token: <input type="text" id="token" autocomplete="off" value="some-key-token"/></label>
            <button onclick="connect(event)" id="bt-conn">Connect</button>
            <button onclick="disconnect(event)" id="bt-disc" style="display: None">Disconnect</button>
            <hr>
            <label>Message: <input type="text" id="messageText" autocomplete="off"/></label>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <div id="chart"></div>
        <div id="conteiner"></div>
        <script src="/static/js/mywebsocket.js"></script>
        <script src="/static/js/mychart.js"></script>
    </body>
</html>
"""
 
security = HTTPBasic()

async def get_cookie_or_token(
    websocket: WebSocket,
    session: Annotated[str | None, Cookie()] = None,
    token: Annotated[str | None, Query()] = None,
):
    if session is None and token is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    return session or token

def get_current_username(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)]
):
    if not (credentials.username == "david") or not (credentials.password == "david"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )

@app.get("/")
async def get(username: Annotated[str, Depends(get_current_username)]):
    return HTMLResponse(html)


@app.websocket("/runners/{runner_id}/ws")
async def websocket_endpoint(
    *,
    websocket: WebSocket,
    runner_id: str,
    q: int | None = None,
    cookie_or_token: Annotated[str, Depends(get_cookie_or_token)],
):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(
                f"Session cookie or query token value is: {cookie_or_token}"
            )
            if q is not None:
                await websocket.send_text(f"Query parameter q is: {q}")
            data = {'high': 195, 
                                'low': 180,
                                'volume': 123,
                                'close': 185,
                                'hlcc4': 123,
                                'open': 190,
                                'time': "2019-05-25",
                                'trades':123,
                                'resolution':123,
                                'confirmed': 123,
                                'vwap': 123,
                                'updated': 123,
                                'index': 123}
            await websocket.send_text(orjson.dumps(data))
    except WebSocketDisconnect:
        print("CLIENT DISCONNECTED for", runner_id)

if __name__ == "__main__":
    uvicorn.run("__main__:app", host="0.0.0.0", port=8000, reload=False)
