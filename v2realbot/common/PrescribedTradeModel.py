from enum import Enum
from datetime import datetime
from pydantic import BaseModel
from typing import Any, Optional, List, Union
from uuid import UUID
class TradeStatus(str, Enum):
    READY = "ready"
    ACTIVATED = "activated"
    CLOSED = "closed"
    #FINISHED = "finished"

class TradeDirection(str, Enum):
    LONG = "long"
    SHORT = "short"

class TradeStoplossType(str, Enum):
    FIXED = "fixed"
    TRAILING = "trailing"

#Predpis obchodu vygenerovany signalem, je to zastresujici jednotka
#ke kteremu jsou pak navazany jednotlivy FILLy (reprezentovany model.TradeUpdate) - napr. castecne exity atp.
class Trade(BaseModel):
    id: UUID
    last_update: datetime
    entry_time: Optional[datetime] = None
    exit_time: Optional[datetime] = None
    status: TradeStatus
    generated_by: Optional[str] = None
    direction: TradeDirection
    entry_price: Optional[float] = None
    goal_price: Optional[float] = None
    size: Optional[int] = None
    # size_multiplier je pomocna promenna pro pocitani relativniho denniho profit
    size_multiplier: Optional[float] = None    
    # stoploss_type: TradeStoplossType
    stoploss_value: Optional[float] = None
    profit: Optional[float] = 0
    profit_sum: Optional[float] = 0
    rel_profit: Optional[float] = 0
    rel_profit_cum: Optional[float] = 0
    
