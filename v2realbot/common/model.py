from uuid import UUID, uuid4
from alpaca.trading.enums import OrderSide, OrderStatus, TradeEvent, OrderClass, OrderType, TimeInForce
#from utils import AttributeDict
from rich import print
from typing import Any, Optional, List, Union
from datetime import datetime, date
from pydantic import BaseModel
from v2realbot.enums.enums import Mode, Account
from alpaca.data.enums import Exchange

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


#for GUI to fetch historical trades on given symbol
class Trade(BaseModel):
    symbol: str
    timestamp: datetime
    exchange: Optional[Union[Exchange, str]]
    price: float
    size: float
    id: int
    conditions: Optional[List[str]]
    tape: Optional[str]


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
    note: Optional[str] = None
    debug: bool = False
    ilog_save: bool = False
    bt_from: datetime = None
    bt_to: datetime = None
    cash: int = 100000


class RunnerView(BaseModel):
    id: UUID
    strat_id: UUID
    run_started: Optional[datetime] = None
    run_mode: Mode
    run_name: Optional[str] = None
    run_note: Optional[str] = None
    run_account: Account
    run_ilog_save: Optional[bool] = False
    run_symbol: Optional[str] = None
    run_trade_count: Optional[int] = 0
    run_profit: Optional[float] = 0
    run_positions: Optional[int] = 0
    run_avgp: Optional[float] = 0
    run_stopped: Optional[datetime] = None
    run_paused: Optional[datetime] = None    
 
#Running instance - not persisted
class Runner(BaseModel):
    id: UUID
    strat_id: UUID
    run_started: Optional[datetime] = None
    run_mode: Mode
    run_account: Account
    run_symbol: Optional[str] = None
    run_name: Optional[str] = None
    run_note: Optional[str] = None
    run_ilog_save: Optional[bool] = False
    run_trade_count: Optional[int]
    run_profit: Optional[float]
    run_positions: Optional[int]
    run_avgp: Optional[float]
    run_stopped: Optional[datetime] = None
    run_paused: Optional[datetime] = None   
    run_thread: Optional[object] = None
    run_instance: Optional[object] = None
    run_pause_ev: Optional[object] = None
    run_stop_ev: Optional[object] = None


class Bar(BaseModel):
    """Represents one bar/candlestick of aggregated trade data over a specified interval.

    Attributes:
        symbol (str): The ticker identifier for the security whose data forms the bar.
        timestamp (datetime): The closing timestamp of the bar.
        open (float): The opening price of the interval.
        high (float): The high price during the interval.
        low (float): The low price during the interval.
        close (float): The closing price of the interval.
        volume (float): The volume traded over the interval.
        trade_count (Optional[float]): The number of trades that occurred.
        vwap (Optional[float]): The volume weighted average price.
        exchange (Optional[float]): The exchange the bar was formed on.
    """

    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    trade_count: Optional[float]
    vwap: Optional[float]

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


class RunArchiveChange(BaseModel):
    id: UUID
    note: str

#Contains archive of running strategies (runner) - master
class RunArchive(BaseModel):
    #unique id of algorun
    id: UUID
    #id of running strategy (stratin/runner)
    strat_id: UUID
    symbol: str
    name: str
    note: Optional[str] = None
    started: datetime
    stopped: Optional[datetime] = None
    mode: Mode
    account: Account
    bt_from: Optional[datetime] = None
    bt_to: Optional[datetime] = None
    stratvars: Optional[dict] = None
    settings: Optional[dict] = None
    ilog_save: Optional[bool] = False
    profit: float = 0
    trade_count: int = 0
    end_positions: int = 0
    end_positions_avgp: float = 0
    open_orders: int = 0

#Contains archive of running strategies (runner) - detail data
class RunArchiveDetail(BaseModel):
    id: UUID
    name: str
    bars: dict
    #trades: Optional[dict]
    indicators: dict
    statinds: dict
    trades: List[TradeUpdate]

# class Trade(BaseModel):
#     order: Order
#     value: float

