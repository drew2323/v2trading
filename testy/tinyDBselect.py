
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
import json
from rich import print

arch_header_file = DATA_DIR + "/arch_header.json"
arch_detail_file = DATA_DIR + "/arch_detail.json"
#db layer to store runner archive
db_arch_h = TinyDB(arch_header_file, default=json_serial)
db_arch_d = TinyDB(arch_detail_file, default=json_serial)


# res = db_arch_h.update(set('note', "ahoj"), where('id') == "74aa524e-3ed4-41fb-8166-f20946520344")
# print(res)
res = db_arch_d.all()
print(res)