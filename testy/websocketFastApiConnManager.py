from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
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
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
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
 
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()
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

@app.get("/")
async def get(username: Annotated[str, Depends(get_current_username)]):
    return HTMLResponse(html)


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
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
            # data = {'high': 123, 
            #                     'low': 123,
            #                     'close': 123,
            #                     'open': 123,
            #                     'time': "2019-05-25"}
            await manager.send_personal_message(orjson.dumps(data), websocket)
            #await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")

if __name__ == "__main__":
    uvicorn.run("__main__:app", host="0.0.0.0", port=8000, reload=False)
