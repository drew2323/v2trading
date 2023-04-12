from uuid import UUID, uuid4
from alpaca.trading.enums import OrderSide, OrderStatus, TradeEvent, OrderClass, OrderType, TimeInForce
#from utils import AttributeDict
from rich import print
import threading
#import utils
import asyncio

from typing import Any, Optional, List, Union
from datetime import datetime, date
from pydantic import BaseModel

class Order(BaseModel):
    id: UUID
    submitted_at: datetime
    filled_at: Optional[datetime]
    symbol: str
    qty: Optional[str]
    filled_qty: Optional[str]
    filled_avg_price: Optional[str]
    side: OrderSide
    limit_price: Optional[str]

class TradeUpdate(BaseModel):
    event: Union[TradeEvent, str]
    execution_id: Optional[UUID]
    order: Order
    timestamp: datetime
    position_qty: Optional[float]
    price: Optional[float]
    qty: Optional[float]

class User(BaseModel):
    id: int
    name = "Jana"
    
a = Order(id = uuid4(), submitted_at= datetime.now(), symbol = "BAC", side=OrderSide.BUY)
print(a)
