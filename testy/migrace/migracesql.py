import sqlite3
from v2realbot.config import DATA_DIR
from v2realbot.utils.utils import json_serial
from uuid import UUID, uuid4
import json
from datetime import datetime
from v2realbot.enums.enums import RecordType, StartBarAlign, Mode, Account
from v2realbot.common.model import RunArchiveDetail
from tinydb import TinyDB, Query, where

sqlite_db_file = DATA_DIR + "/v2trading.db"
conn = sqlite3.connect(sqlite_db_file)
#standardne vraci pole tuplů, kde clen tuplu jsou sloupce
#conn.row_factory = lambda c, r: json.loads(r[0])
#conn.row_factory = lambda c, r: r[0]
#conn.row_factory = sqlite3.Row

#CREATE TABLE
# c = conn.cursor()
# createTable= "CREATE TABLE runner_logs (runner_id varchar(32) NOT NULL, time real NOT NULL, data json NOT NULL);"
# print(c.execute(createTable))
# sql = ("CREATE INDEX index_runner_logs ON runner_logs (runner_id, time);")
# print(c.execute(sql))

#testovaci objekty
insert = dict(time=datetime.now(), side="ddd", rectype=RecordType.BAR, id=uuid4())
insert_list = [dict(time=datetime.now().timestamp(), side="ddd", rectype=RecordType.BAR, id=uuid4()),dict(time=datetime.now().timestamp(), side="ddd", rectype=RecordType.BAR, id=uuid4()),dict(time=datetime.now().timestamp(), side="ddd", rectype=RecordType.BAR, id=uuid4()),dict(time=datetime.now().timestamp(), side="ddd", rectype=RecordType.BAR, id=uuid4())]

def insert_log(runner_id: UUID, time: float, logdict: dict):
    c = conn.cursor()
    json_string = json.dumps(logdict, default=json_serial)
    res = c.execute("INSERT INTO runner_logs VALUES (?,?,?)",[str(runner_id), time, json_string])
    conn.commit()
    return res.rowcount

def insert_log_multiple(runner_id: UUID, loglist: list):
    c = conn.cursor()
    insert_data = []
    for i in loglist:
        row = (str(runner_id), i["time"], json.dumps(i, default=json_serial))
        insert_data.append(row)
    c.executemany("INSERT INTO runner_logs VALUES (?,?,?)", insert_data)
    conn.commit()
    return c.rowcount
    
    # c = conn.cursor()
    # json_string = json.dumps(logdict, default=json_serial)
    # res = c.execute("INSERT INTO runner_logs VALUES (?,?,?)",[str(runner_id), time, json_string])
    # print(res)
    # conn.commit()
    # return res

#returns list of ilog jsons
def read_log_window(runner_id: UUID, timestamp_from: float, timestamp_to: float):
    conn.row_factory = lambda c, r: json.loads(r[0])
    c = conn.cursor()
    res = c.execute(f"SELECT data FROM runner_logs WHERE runner_id='{str(runner_id)}' AND time >={ts_from} AND time <={ts_to}")
    return res.fetchall()

#returns number of deleted elements
def delete_logs(runner_id: UUID):
    c = conn.cursor()
    res = c.execute(f"DELETE from runner_logs WHERE runner_id='{str(runner_id)}';")
    print(res.rowcount)
    conn.commit()
    return res.rowcount

# print(insert_log(str(uuid4()), datetime.now().timestamp(), insert))
# c = conn.cursor()
# ts_from = 1683108821.08872
# ts_to = 1683108821.08874
# # res = c.execute(f"SELECT runner_id, time, data FROM runner_logs where time > {ts_from} and time <{ts_to}")
# # result = res.fetchall()

# # res= delete_logs("7f9866ac-c742-47f4-a329-1d2b6721e781")
# # print(res)

# # res = read_log_window(runner_id="33", timestamp_from=11 , timestamp_to=22)
# # print(res)

# res = insert_log_multiple(uuid4(), insert_list)
# print(res)

# res = read_log_window("3340e257-d19a-4179-baf3-3b39190acde3", ts_from, ts_to)

# print(res)

# for r in res.fetchall():
#     print(dict(r))


#print(res.description)
#print(result)

def insert_archive_detail(archdetail: RunArchiveDetail):
    c = conn.cursor()
    json_string = json.dumps(archdetail, default=json_serial)
    res = c.execute("INSERT INTO runner_detail VALUES (?,?)",[str(archdetail["id"]), json_string])
    conn.commit()
    return res.rowcount

#returns list of details
def get_all_archive_detail():
    conn.row_factory = lambda c, r: json.loads(r[0])
    c = conn.cursor()
    res = c.execute(f"SELECT data FROM runner_detail")
    return res.fetchall()

#vrátí konkrétní
def get_archive_detail_byID(runner_id: UUID):
    conn.row_factory = lambda c, r: json.loads(r[0])
    c = conn.cursor()
    res = c.execute(f"SELECT data FROM runner_detail WHERE runner_id='{str(runner_id)}'")
    return res.fetchone()

#returns number of deleted elements
def delete_archive_detail(runner_id: UUID):
    c = conn.cursor()
    res = c.execute(f"DELETE from runner_detail WHERE runner_id='{str(runner_id)}';")
    print(res.rowcount)
    conn.commit()
    return res.rowcount

def get_all_archived_runners_detail():
    arch_detail_file = DATA_DIR + "/arch_detail.json"
    db_arch_d = TinyDB(arch_detail_file, default=json_serial)
    res = db_arch_d.all()
    return 0, res

def migrate():
    set = list[RunArchiveDetail]
    res, set = get_all_archived_runners_detail()
    print(f"fetched {len(set)}")
    for row in set:
        insert_archive_detail(row)
        print(f"inserted {row['id']}")

bars = {'high': [], 
                        'low': [],
                        'volume': [],
                        'close': [],
                        'hlcc4': [],
                        'open': [],
                        'time': [],
                        'trades':[],
                        'resolution':[],
                        'confirmed': [],
                        'vwap': [],
                        'updated': [],
                        'index': []}

idecko = uuid4()

runArchiveDetail: RunArchiveDetail = RunArchiveDetail(id = idecko,
                                                    name="nazev runneru",
                                                    bars=bars,
                                                    indicators=[dict(time=[])],
                                                    statinds=dict(neco=233,zase=333),
                                                    trades=list(dict()))

# insert_archive_detail(runArchiveDetail)
migrate()
# res = get_archive_detail_byID(idecko)
# print("byID",res)
res = get_all_archive_detail()
print("finished: all",len(res))
# delete_archive_detail(idecko)
# res = get_archive_detail_byID(idecko)
# print("byID",res)
# res = get_all_archive_detail()
# print("all",res)