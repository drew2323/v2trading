from v2realbot.config import DATA_DIR
from v2realbot.utils.utils import json_serial
from uuid import UUID, uuid4
import orjson
import json
from datetime import datetime
from v2realbot.enums.enums import RecordType, StartBarAlign, Mode, Account
from v2realbot.common.db import pool, insert_queue



#standardne vraci pole tuplů, kde clen tuplu jsou sloupce
#conn.row_factory = lambda c, r: orjson.loads(r[0])
#conn.row_factory = lambda c, r: r[0]
#conn.row_factory = sqlite3.Row

#CREATE TABLE
# c = conn.cursor()
# createTable= "CREATE TABLE runner_logs (runner_id varchar(32) NOT NULL, time real NOT NULL, data json NOT NULL);"
# print(c.execute(createTable))
# sql = ("CREATE INDEX index_runner_logs ON runner_logs (runner_id, time);")
# print(c.execute(sql))

#testovaci objekty
#insert = dict(time=datetime.now(), side="ddd", rectype=RecordType.BAR, id=uuid4())
#insert_list = [dict(time=datetime.now().timestamp(), side="ddd", rectype=RecordType.BAR, id=uuid4()),dict(time=datetime.now().timestamp(), side="ddd", rectype=RecordType.BAR, id=uuid4()),dict(time=datetime.now().timestamp(), side="ddd", rectype=RecordType.BAR, id=uuid4()),dict(time=datetime.now().timestamp(), side="ddd", rectype=RecordType.BAR, id=uuid4())]


#TOTO PREDELAT NA OBJEKT, který bude mít per thread svoji connectionu

#returns rowcount of inserted rows
def insert_log(runner_id: UUID, time: float, logdict: dict):
    conn = pool.get_connection()
    try:
        c = conn.cursor()
        json_string = orjson.dumps(logdict, default=json_serial, option=orjson.OPT_PASSTHROUGH_DATETIME).decode('utf-8')
        res = c.execute("INSERT INTO runner_logs VALUES (?,?,?)",[str(runner_id), time, json_string])
        conn.commit()
    finally:
        pool.release_connection(conn)
    return res.rowcount

#returns rowcount of inserted rows
#single connection in WAL mode
def insert_log_multiple_queue(runner_id:UUID, loglist: list):
    insert_queue.put((runner_id, loglist))

# def insert_log_multiple(runner_id: UUID, loglist: list):
#     conn = sqlite3.connect(sqlite_db_file, check_same_thread=False)
#     c = conn.cursor()
#     insert_data = []
#     for i in loglist:
#         row = (str(runner_id), i["time"], orjson.dumps(i, default=json_serial, option=orjson.OPT_PASSTHROUGH_DATETIME))
#         insert_data.append(row)
#     c.executemany("INSERT INTO runner_logs VALUES (?,?,?)", insert_data)
#     conn.commit()
#     return c.rowcount

#returns list of ilog jsons
def get_log_window(runner_id: UUID, timestamp_from: float = 0, timestamp_to: float = 9682851459):
    conn = pool.get_connection()
    try:
        conn.row_factory = lambda c, r: json.loads(r[0])
        c = conn.cursor()
        res = c.execute(f"SELECT data FROM runner_logs WHERE runner_id='{str(runner_id)}' AND time >={timestamp_from} AND time <={timestamp_to} ORDER BY time")
    finally:
        conn.row_factory = None
        pool.release_connection(conn)
    return res.fetchall()

#returns number of deleted elements
def delete_logs(runner_id: UUID):
    conn = pool.get_connection()
    try:
        c = conn.cursor()
        res = c.execute(f"DELETE from runner_logs WHERE runner_id='{str(runner_id)}';")
        print(res.rowcount)
        conn.commit()
    finally:
        pool.release_connection(conn)
    return res.rowcount


# print(insert_log(str(uuid4()), datetime.now().timestamp(), insert))
# c = conn.cursor()
# ts_from = 1683108821.08872
# ts_to = 1683108821.08874
# res = c.execute(f"SELECT runner_id, time, data FROM runner_logs where time > {ts_from} and time <{ts_to}")
# result = res.fetchall()

# res= delete_logs("7f9866ac-c742-47f4-a329-1d2b6721e781")
# print(res)

# res = read_log_window(runner_id="33", timestamp_from=11 , timestamp_to=22)
# print(res)

# res = insert_log_multiple(uuid4(), insert_list)
# print(res)

# res = read_log_window("3340e257-d19a-4179-baf3-3b39190acde3", ts_from, ts_to)

# print(res)

# for r in res.fetchall():
#     print(dict(r))


#print(res.description)
#print(result)






