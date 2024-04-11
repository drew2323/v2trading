from uuid import UUID, uuid4
from alpaca.trading.enums import OrderSide, OrderStatus, TradeEvent,OrderType
#from utils import AttributeDict
from rich import print
from typing import Any, Optional, List, Union
from datetime import datetime, date
from pydantic import BaseModel, Field
from v2realbot.enums.enums import Mode, Account, SchedulerStatus, Moddus, Market
from alpaca.data.enums import Exchange




#models for server side datatables
# Model for individual column data
class ColumnData(BaseModel):
    data: str
    name: str
    searchable: bool
    orderable: bool
    search: dict

# Model for the search value
class SearchValue(BaseModel):
    value: str
    regex: bool

class OrderValue(BaseModel):
    column: int
    dir: str

# Model for incoming DataTables request
class DataTablesRequest(BaseModel):
    draw: int
    start: int
    length: int
    search: SearchValue
    order: List[OrderValue]
    columns: List[ColumnData]

#tu samou variantu pak UpdateStrategyInstanceWhileRunning

#only those that can be changed UUID id prijde v parametru
# @app.put("/api/v1/users/{id}")
# async def update_user(user_update: UpdateUser, id: UUID):
#  for user in db:
#  if user.id == id:
#  if user_update.first_name is not None:
#  user.first_name = user_update.first_name
#  if user_update.last_name is not None:
#  userbase.last_name = user_update.last_name
#  if user_update.roles is not None:
#  user.roles = user_update.roles
#  return user.id
#  raise HTTPException(status_code=404, detail=f"Could not find user with id: {id}")


#obecny vstup pro analyzera (vstupem muze byt bud batch_id nebo seznam runneru)
class AnalyzerInputs(BaseModel):
    function: str
    batch_id: Optional[str] = None
    runner_ids: Optional[List[UUID]] = None
    #additional parameter
    params: Optional[dict] = {}

class RunDay(BaseModel):
    """
    Helper object for batch run - carries list of days in format required by run batch manager
    """
    start: datetime
    end: datetime
    name: Optional[str] = None
    note: Optional[str] = None
    id: Optional[str] = None

# Define a Pydantic model for input data
class ConfigItem(BaseModel):
    id: Optional[int] = None
    item_name: str
    json_data: str

class Intervals(BaseModel):
    start: str
    end: str
    note: Optional[str] = None

# Define the data model for the TestLists
class TestList(BaseModel):
    id: Optional[UUID | str | None] = None
    name: str
    dates: List[Intervals]

#for GUI to fetch historical trades on given symbol
class Trade(BaseModel):
    symbol: str
    timestamp: datetime
    exchange: Optional[Union[Exchange, str]] = None
    price: float
    size: float
    id: int
    conditions: Optional[List[str]] = None
    tape: Optional[str] = None


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
    note: Optional[str]  = None
    history: Optional[str] = None

    def __setstate__(self, state: dict[Any, Any]) -> None:
        """
        Hack to allow unpickling models stored from pydantic V1
        """
        state.setdefault("__pydantic_extra__", {})
        state.setdefault("__pydantic_private__", {})

        if "__pydantic_fields_set__" not in state:
            state["__pydantic_fields_set__"] = state.get("__fields_set__")

        super().__setstate__(state)

class RunRequest(BaseModel):
    id: UUID
    account: Account
    mode: Mode
    note: Optional[str] = None
    debug: bool = False
    strat_json: Optional[str] = None
    ilog_save: bool = False
    bt_from: Optional[datetime] = None
    bt_to: Optional[datetime] = None
    #weekdays filter
    #pokud je uvedeny filtrujeme tyto dny
    weekdays_filter: Optional[list] = None
    #id testovaciho intervalu TODO prejmenovat
    test_batch_id: Optional[str] = None
    #GENERATED ID v ramci runu, vaze vsechny runnery v batchovem behu
    batch_id: Optional[str] = None
    cash: int = 100000
    skip_cache: Optional[bool] = False

#Trida, která je nadstavbou runrequestu a pouzivame ji v scheduleru, je zde navic jen par polí
class RunManagerRecord(BaseModel):
    moddus: Moddus
    id: UUID = Field(default_factory=uuid4) 
    strat_id: UUID
    symbol: Optional[str] = None
    account: Account
    mode: Mode
    note: Optional[str] = None
    ilog_save: bool = False
    market: Optional[Market] = Market.CRYPTO
    bt_from: Optional[datetime] = None
    bt_to: Optional[datetime] = None
    #weekdays filter
    #pokud je uvedeny filtrujeme tyto dny
    weekdays_filter: Optional[list] = None #list of strings 0-6 representing days to run
    #GENERATED ID v ramci runu, vaze vsechny runnery v batchovem behu
    batch_id: Optional[str] = None
    testlist_id: Optional[str] = None
    start_time: str #time (HH:MM) that start function is called
    stop_time: Optional[str] = None #time  (HH:MM) that stop function is called
    status: SchedulerStatus
    last_processed: Optional[datetime] = None
    history: Optional[str] = None
    valid_from: Optional[datetime] = None # US East time zone daetime
    valid_to: Optional[datetime] = None # US East time zone daetime
    runner_id: Optional[UUID] = None #last runner_id from scheduler after stratefy is started
    strat_running: Optional[bool] = None #automatically updated field based on status of runner_id above, it is added by row_to_RunManagerRecord
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
    batch_id: Optional[str] = None
    run_started: Optional[datetime] = None
    run_mode: Mode
    run_account: Account
    run_symbol: Optional[str] = None
    run_name: Optional[str] = None
    run_note: Optional[str] = None
    run_ilog_save: Optional[bool] = False
    run_trade_count: Optional[int] = None
    run_profit: Optional[float] = None
    run_positions: Optional[int] = None
    run_avgp: Optional[float] = None
    run_strat_json: Optional[str] = None
    run_stopped: Optional[datetime] = None
    run_paused: Optional[datetime] = None   
    run_thread: Optional[object] = None
    run_instance: Optional[object] = None
    run_pause_ev: Optional[object] = None
    run_stop_ev: Optional[object] = None
    run_stratvars_toml: Optional[str] = None


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
    trade_count: Optional[float] = 0
    vwap: Optional[float] = 0

class Order(BaseModel):
    id: UUID
    submitted_at: datetime
    filled_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    symbol: str
    qty: int
    status: OrderStatus
    order_type: OrderType
    filled_qty: Optional[int] = None
    filled_avg_price: Optional[float] = None
    side: OrderSide
    limit_price: Optional[float] = None

#entita pro kazdy kompletni FILL, je navazana na prescribed_trade 
class TradeUpdate(BaseModel):
    event: Union[TradeEvent, str]
    execution_id: Optional[UUID] = None
    order: Order
    timestamp: datetime
    position_qty: Optional[float] = None
    price: Optional[float] = None
    qty: Optional[float] = None
    value: Optional[float] = None
    cash: Optional[float] = None
    pos_avg_price: Optional[float] = None
    profit: Optional[float] = None
    profit_sum: Optional[float] = None
    rel_profit: Optional[float] = None
    rel_profit_cum: Optional[float] = None
    signal_name: Optional[str] = None
    prescribed_trade_id: Optional[str] = None


class RunArchiveChange(BaseModel):
    id: UUID
    note: str

#do budoucna pouzit SQLAlchemy
#Contains archive of running strategies (runner) - master
class RunArchive(BaseModel):
    #unique id of algorun
    id: UUID
    #id of running strategy (stratin/runner)
    strat_id: UUID
    batch_id: Optional[str] = None
    symbol: str
    name: str
    note: Optional[str] = None
    started: datetime
    stopped: Optional[datetime] = None
    mode: Mode
    account: Account
    bt_from: Optional[datetime] = None
    bt_to: Optional[datetime] = None
    strat_json: Optional[str] = None
    transferables: Optional[dict] = None #varaibles that are transferrable to next run
    settings: Optional[dict] = None
    ilog_save: Optional[bool] = False
    profit: float = 0
    trade_count: int = 0
    end_positions: int = 0
    end_positions_avgp: float = 0
    metrics: Union[dict, str] = None
    stratvars_toml: Optional[str] = None

#For gui view master table
class RunArchiveView(BaseModel):
    id: UUID
    strat_id: UUID
    batch_id: Optional[str] = None
    symbol: str
    name: str
    note: Optional[str] = None
    started: datetime
    stopped: Optional[datetime] = None
    mode: Mode
    account: Account
    bt_from: Optional[datetime] = None
    bt_to: Optional[datetime] = None
    ilog_save: Optional[bool] = False
    profit: float = 0
    trade_count: int = 0
    end_positions: int = 0
    end_positions_avgp: float = 0
    metrics: Union[dict, str] = None
    batch_profit: float = 0  # Total profit for the batch - now calculated during query
    batch_count: int = 0  # Count of runs in the batch - now calculated during query

#same but with pagination
class RunArchiveViewPagination(BaseModel):
    draw: int
    recordsTotal: int
    recordsFiltered: int
    data: List[RunArchiveView]

#trida pro ukladani historie stoplossy do ext_data
class SLHistory(BaseModel):
    id: Optional[UUID] = None
    time: datetime
    sl_val: float

#Contains archive of running strategies (runner) - detail data
class RunArchiveDetail(BaseModel):
    id: UUID
    name: str
    bars: dict
    #trades: Optional[dict]
    indicators: List[dict]
    statinds: dict
    trades: List[TradeUpdate]
    ext_data: Optional[dict] = None
    

class InstantIndicator(BaseModel):
    name: str
    toml: str


