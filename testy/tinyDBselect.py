
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
from tinydb import TinyDB, Query, where
from tinydb.operations import set
import orjson
from rich import print



#vyzkouset https://github.com/MrPigss/BetterJSONStorage


insert = {'datum': datetime.now(), 'side': "dd", 'name': 'david','id': uuid4(), 'order': "neco"}
class RunnerLogger:
    def __init__(self, runner_id: UUID) -> None:
        self.runner_id = runner_id
        runner_log_file = DATA_DIR + "/runner_log.json"
        db_runner_log = TinyDB(runner_log_file, default=json_serial, option=orjson.OPT_PASSTHROUGH_DATETIME)

def insert_log_multiple(runner_id: UUID, logList: list):
    runner_table = db_runner_log.table(str(runner_id))
    res = runner_table.insert_multiple(logList)
    return res

def insert_log(runner_id: UUID, logdict: dict):
    runner_table = db_runner_log.table(str(runner_id))
    res = runner_table.insert(logdict)
    return res
    

def read_log_window(runner_id: UUID, timestamp_from: float, timestamp_to: float):
    runner_table = db_runner_log.table(str(runner_id))
    res = runner_table.search((where('datum') >= timestamp_from) & (where('datum') <= timestamp_to))
    if len(res) == 0:
        return -1, "not found"
    return 0, res

def delete_log(runner_id: UUID):
    res = db_runner_log.drop_table(str(runner_id))
    if res is None:
        return -1, "not found"
    return 0, runner_id

# runner_id = uuid4()
# for i in range(0,10):
#     print(insert_log(runner_id, insert))

print(delete_log(runner_id="2459a6ff-a350-44dc-9c14-11cfae07f7e9"))

print(read_log_window("ae9cdf8f-5cd0-4a49-8cfe-c486e21cb4fa",1,99999999999999))


#2459a6ff-a350-44dc-9c14-11cfae07f7e9
#ae9cdf8f-5cd0-4a49-8cfe-c486e21cb4fa


#db_runner_log.drop_tables()
print(db_runner_log.tables())
# res = db_arch_h.update(set('note', "ahoj"), where('id') == "74aa524e-3ed4-41fb-8166-f20946520344")
# print(res)
#res = db_runner_log.all()
#print(res)
