from uuid import UUID, uuid4
from alpaca.trading.enums import OrderSide, OrderStatus, TradeEvent, OrderClass, OrderType, TimeInForce
#from utils import AttributeDict
from rich import print
from typing import Any, Optional, List, Union
from datetime import datetime, date
from pydantic import BaseModel
from v2realbot.enums.enums import Mode, Account

#tu samou variantu pak UpdateStrategyInstanceWhileRunning

#only those that can be changed UUID id prijde v parametru
# @app.put("/api/v1/users/{id}")
# async def update_user(user_update: UpdateUser, id: UUID):
#  for user in db:
#  if user.id == id:
#  if user_update.first_name is not None:
#  user.first_name = user_update.first_name
#  if user_update.last_name is not None:
#  user.last_name = user_update.last_name
#  if user_update.roles is not None:
#  user.roles = user_update.roles
#  return user.id
#  raise HTTPException(status_code=404, detail=f"Could not find user with id: {id}")

#persisted object in pickle
class StrategyInstance(BaseModel):
    id: Optional[UUID | str | None] = None
    id2: int
    name: str
    symbol: str
    class_name: str
    script: str
    open_rush: int = 0
    close_rush: int = 0
    stratvars_conf: str
    add_data_conf: str
    note: Optional[str] 
    history: Optional[str]

class RunRequest(BaseModel):
    id: UUID
    account: Account
    mode: Mode
    debug: bool = False
    bt_from: datetime = None
    bt_to: datetime = None
    cash: int = 100000

class RunnerView(BaseModel):
    id: UUID
    run_started: Optional[datetime] = None
    run_mode: Mode
    run_account: Account
    run_stopped: Optional[datetime] = None
    run_paused: Optional[datetime] = None    
 
#Running instance - not persisted
class Runner(BaseModel):
    id: UUID
    run_started: Optional[datetime] = None
    run_mode: Mode
    run_account: Account
    run_stopped: Optional[datetime] = None
    run_paused: Optional[datetime] = None   
    run_thread: Optional[object] = None
    run_instance: Optional[object] = None
    run_pause_ev: Optional[object] = None
    run_stop_ev: Optional[object] = None

class Order(BaseModel):
    id: UUID
    submitted_at: datetime
    filled_at: Optional[datetime]
    canceled_at: Optional[datetime]
    symbol: str
    qty: int
    status: OrderStatus
    order_type: OrderType
    filled_qty: Optional[int]
    filled_avg_price: Optional[float]
    side: OrderSide
    limit_price: Optional[float]

class TradeUpdate(BaseModel):
    event: Union[TradeEvent, str]
    execution_id: Optional[UUID]
    order: Order
    timestamp: datetime
    position_qty: Optional[float]
    price: Optional[float]
    qty: Optional[float]
    value: Optional[float]
    cash: Optional[float]
    pos_avg_price: Optional[float]

# class Trade(BaseModel):
#     order: Order
#     value: float

