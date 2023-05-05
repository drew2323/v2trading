from tinydb import TinyDB, Query, where
from tinydb.operations import set
from tinydb.storages import JSONStorage
from tinydb_serialization import SerializationMiddleware, Serializer
from tinydb_serialization.serializers import DateTimeSerializer
from v2realbot.common.model import Trade
from v2realbot.utils.utils import parse_toml_string, zoneNY, json_serial
from v2realbot.config import DATA_DIR
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum
from v2realbot.common.model import Order, TradeUpdate as btTradeUpdate
from alpaca.trading.models import TradeUpdate
from alpaca.trading.enums import TradeEvent, OrderType, OrderSide, OrderType, OrderStatus
from rich import print
import json

#storage_with_injected_serialization = JSONStorage()

serialization = SerializationMiddleware(JSONStorage)

#builtin DateTimeSerializer

#customer DateTime2TimestampSerializer
class DateTime2TimestampSerializer(Serializer):
    OBJ_CLASS = datetime  # The class this serializer handles

    def encode(self, obj):
        return str(obj.timestamp())

    def decode(self, s):
        return s
        #return datetime.fromtimestamp(s)

class EnumSerializer(Serializer):
    OBJ_CLASS = Enum  # The class this serializer handles

    def encode(self, obj):
        return str(obj)

    def decode(self, s):
        return s

class UUIDSerializer(Serializer):
    OBJ_CLASS = UUID  # The class this serializer handles

    def encode(self, obj):
        return str(obj)

    def decode(self, s):
        return s

class TradeUpdateSerializer(Serializer):
    OBJ_CLASS = TradeUpdate  # The class this serializer handles

    def encode(self, obj):
        return obj.__dict__

    def decode(self, s):
        return str(s)
    
class btTradeUpdateSerializer(Serializer):
    OBJ_CLASS = btTradeUpdate  # The class this serializer handles

    def encode(self, obj):
        return obj.__dict__

    def decode(self, s):
        return str(s)

class OrderSerializer(Serializer):
    OBJ_CLASS = Order  # The class this serializer handles

    def encode(self, obj):
        return obj.__dict__

    def decode(self, s):
        return s

orderList =[Order(id=uuid4(),
                                submitted_at = datetime(2023, 3, 17, 9, 30, 0, 0, tzinfo=zoneNY),
                                symbol = "BAC",
                                qty = 1,
                                status = OrderStatus.ACCEPTED,
                                order_type = OrderType.LIMIT,
                                side = OrderSide.BUY,
                                limit_price=22.4),
                Order(id=uuid4(),
                                submitted_at = datetime(2023, 3, 17, 9, 30, 0, 0, tzinfo=zoneNY),
                                symbol = "BAC",
                                qty = 1,
                                status = OrderStatus.ACCEPTED,
                                order_type = OrderType.LIMIT,
                                side = OrderSide.BUY,
                                limit_price=22.4)]
                                  
# serialization.register_serializer(DateTime2TimestampSerializer(), 'TinyDate')
# serialization.register_serializer(UUIDSerializer(), 'TinyUUID')
# serialization.register_serializer(TradeUpdateSerializer(), 'TinyTradeUpdate')
# serialization.register_serializer(btTradeUpdateSerializer(), 'TinybtTradeUpdate')
# serialization.register_serializer(OrderSerializer(), 'TinyOrder')

a = Order(id=uuid4(),
                                submitted_at = datetime(2023, 3, 17, 9, 30, 0, 0, tzinfo=zoneNY),
                                symbol = "BAC",
                                qty = 1,
                                status = OrderStatus.ACCEPTED,
                                order_type = OrderType.LIMIT,
                                side = OrderSide.BUY,
                                limit_price=22.4)

db_file = DATA_DIR + "/db.json"
db = TinyDB(db_file, default=json_serial)
db.truncate()
insert = {'datum': datetime.now(), 'side': OrderSide.BUY, 'name': 'david','id': uuid4(), 'order': orderList}





#insert record
db.insert(a.__dict__)

#get records by id
#res = db.search(where('id') == "0a9da064-708c-4645-8a07-e749d93a213d")
#or get one:
res = db.get(where('id') == "0a9da064-708c-4645-8a07-e749d93a213d")


#update one document
#db.update(set('name', "nove jmeno1"), where('id') == "0a9da064-708c-4645-8a07-e749d93a213d")


#get all documents
res = db.all()
print("vsechny zaznamy, res)", res)

#fetch one docuemnt
# >>> db.get(User.name == 'John')
# {'name': 'John', 'age': 22}
# >>> db.get(User.name == 'Bobby')
# None


#delete record by id
#res = db.remove(where('id') == "0a9da064-708c-4645-8a07-e749d93a213d")
#print("removed", res)

#res = db.search(qorder.order.id == "af447235-c01a-4c88-9f85-f3c267d2e2e1")
#res = db.search(qorder.orderList.side == "<OrderSide.BUY: 'buy'>")
#print(res)


#print(db.all())


