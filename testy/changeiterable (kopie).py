from uuid import UUID, uuid4
from alpaca.trading.enums import OrderSide, OrderStatus, TradeEvent, OrderClass, OrderType, TimeInForce
#from utils import AttributeDict
from rich import print
from typing import Any, Optional, List, Union
from datetime import datetime, date
from pydantic import BaseModel
from common.model import Order
# to test change iterable (adding items) while iterating
import asyncio

class Notif:
    def __init__(self,time):
        self.time = time

open_orders: list = []

for i in range(1,10):
    open_orders.append(Order(id=uuid4(),
                       submitted_at = datetime.utcnow(),
                       qty=1,
                       order_type=OrderType.MARKET,
                       symbol = "BAC",
                       status = OrderStatus.ACCEPTED,
                       side = OrderSide.BUY))

print("cele pole objektu",open_orders)

# Here, 'reversed' returns a lazy iterator, so it's performant! reversed(l):

#musi fungovat removing stare a pridavani novych

#this list contains all not processed notification, that we try to process during this iteration
#if time is not right we leave the message for next iter
#if time is right we process the message (- note it can trigger additional open_orders, that are added to queue)

async def apenduj():
    global open_orders
    open_orders.append("cago")
    # if notif.time % 2 == 0 and notif.time < 300:
    #     open_orders.append(Notif(notif.time+50))
        
todel = []
for i in open_orders:
    #print("*******start iterace polozky", i.time)
    print(i)
    print("removing element",i)
    res = asyncio.run(apenduj())
    todel.append(i)
    print("*****konec iterace", i)
    print()

print("to del", todel)
#removing processed from the list
for i in todel:
    open_orders.remove(i)


print("cely list po skonceni vseho")
for i in open_orders: print(i.id)



""""
pred iteraci se zavola synchroné
EXECUTE open orders(time)
    - pokusi se vytvorit vsechny otevrene ordery do daneho casu (casu dalsi iterace)
    - podporuje i volani callbacku a to vcetne pokynu vytvoreneho z pokynu
    - tento novy pokyn muze byt i take exekuovan pokud se vcetne roundtripu vejde do daneho casu
    pripadne soucasne vytvoreni i exekuci pokynu


"""

