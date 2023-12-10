
from typing import Any, List
from uuid import UUID, uuid4
import pickle
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockTradesRequest, StockBarsRequest
from alpaca.data.enums import DataFeed
from alpaca.data.timeframe import TimeFrame
from v2realbot.enums.enums import RecordType, StartBarAlign, Mode, Account
from v2realbot.common.model import StrategyInstance, Runner, RunRequest, RunArchive, RunArchiveDetail, RunArchiveChange
from v2realbot.utils.utils import AttributeDict, zoneNY, dict_replace_value, Store, parse_toml_string, json_serial
from datetime import datetime
from threading import Thread, current_thread, Event, enumerate
from v2realbot.config import STRATVARS_UNCHANGEABLES, ACCOUNT1_LIVE_API_KEY, ACCOUNT1_LIVE_SECRET_KEY, DATA_DIR
import importlib
from queue import Queue
#from tinydb import TinyDB, Query, where
#from tinydb.operations import set
import orjson
from rich import print
from tinyflux import Point, TinyFlux


runner_log_file = DATA_DIR + "/runner_flux__log.json"
#db layer to store runner archive
db_runner_log = TinyFlux(runner_log_file)

insert_dict = {'datum': datetime.now(), 'side': "dd", 'name': 'david','id': uuid4(), 'order': "neco"}
#orjson.dumps(insert_dict, default=json_serial, option=orjson.OPT_PASSTHROUGH_DATETIME)
p1 = Point(time=datetime.now(), tags=insert_dict)

db_runner_log.insert(p1)

res=db_runner_log.all()
print(res)


# #db_runner_log.drop_table('hash')
# res = runner_table.get(where('side') == "dd")
# print(res)
# # res = db_arch_h.update(set('note', "ahoj"), where('id') == "74aa524e-3ed4-41fb-8166-f20946520344")
# # print(res)
# res = runner_table.all()
# print(res)
