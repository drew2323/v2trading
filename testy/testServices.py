from v2realbot.utils.utils import AttributeDict, zoneNY, dict_replace_value, Store, parse_toml_string
import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v2realbot.enums.enums import Mode, Account
from v2realbot.config import WEB_API_KEY
from datetime import datetime
from icecream import install, ic
import os
from rich import print
from threading import current_thread
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
import uvicorn
from uuid import UUID
import controller.services as cs
from v2realbot.common.model import StrategyInstance, RunnerView

d = "[stratvars]    maxpozic = 205    chunk = 114    MA = 2    Trend = 3    profit = 0.02    lastbuyindex=-6    pendingbuys={}    limitka = 'None'    jevylozeno=0    vykladka=5    curve = [0.01, 0.01, 0.01, 0.0, 0.02, 0.02, 0.01,0.01, 0.01,0.03, 0.01, 0.01, 0.01,0.04, 0.01,0.01, 0.01,0.05, 0.01,0.01, 0.01,0.01, 0.06,0.01, 0.01,0.01, 0.01]    blockbuy = 0    ticks2reset = 0.04"
d='[stratvars]\r\n    maxpozic = 200\r\n    chunk = 111\r\n    MA = 2\r\n    Trend = 3\r\n    profit = 0.02\r\n    lastbuyindex=-6\r\n    pendingbuys={}\r\n    limitka = "None"\r\n    jevylozeno=0\r\n    vykladka=5\r\n    curve = [0.01, 0.01, 0.01, 0.0, 0.02, 0.02, 0.01,0.01, 0.01,0.03, 0.01, 0.01, 0.01,0.04, 0.01,0.01, 0.01,0.05, 0.01,0.01, 0.01,0.01, 0.06,0.01, 0.01,0.01, 0.01]\r\n    blockbuy = 0\r\n    ticks2reset = 0.04'
print(d)
a,b = parse_toml_string(d)
print(a,b)