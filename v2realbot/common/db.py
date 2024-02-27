import sqlite3
import queue
import threading
import time
from v2realbot.common.model import RunArchive, RunArchiveView, RunManagerRecord
from datetime import datetime
import orjson
from v2realbot.utils.utils import json_serial, send_to_telegram, zoneNY
import v2realbot.controller.services as cs
from uuid import UUID
from v2realbot.config import DATA_DIR

sqlite_db_file = DATA_DIR + "/v2trading.db"
# Define the connection pool
class ConnectionPool:
    def __init__(self, max_connections):
        self.max_connections = max_connections
        self.connections = queue.Queue(max_connections)
        self.lock = threading.Lock()

    def get_connection(self):
        with self.lock:
            if self.connections.empty():
                return self.create_connection()
            else:
                return self.connections.get()

    def release_connection(self, connection):
        with self.lock:
            self.connections.put(connection)

    def create_connection(self):
        connection = sqlite3.connect(sqlite_db_file, check_same_thread=False)
        return connection


def execute_with_retry(cursor: sqlite3.Cursor, statement: str, params = None, retry_interval: int = 2) -> sqlite3.Cursor:
    """get connection from pool and execute SQL statement with retry logic if required.

    Args:
        cursor: The database cursor to use.
        statement: The SQL statement to execute.
        retry_interval: The number of seconds to wait before retrying the statement.

    Returns:
        The database cursor.
    """
    while True:
        try:
            if params is None:
                return cursor.execute(statement)
            else:
                return cursor.execute(statement, params)
        except sqlite3.OperationalError as e:
            if str(e) == "database is locked":
                print("database retry in 1s." + str(e))
                time.sleep(retry_interval)
                continue
            else:
                raise e

#for pool of connections if necessary
pool = ConnectionPool(10)
#for one shared connection (used for writes only in WAL mode)
insert_conn = sqlite3.connect(sqlite_db_file, check_same_thread=False)
insert_queue = queue.Queue()

#prevede dict radku zpatky na objekt vcetme retypizace
def row_to_runmanager(row: dict) -> RunManagerRecord:

    is_running = cs.is_runner_running(row['runner_id']) if row['runner_id'] else False

    res = RunManagerRecord(
        moddus=row['moddus'],
        id=row['id'],
        strat_id=row['strat_id'],
        symbol=row['symbol'],
        mode=row['mode'],
        account=row['account'],
        note=row['note'],
        ilog_save=bool(row['ilog_save']),
        bt_from=datetime.fromisoformat(row['bt_from']) if row['bt_from'] else None,
        bt_to=datetime.fromisoformat(row['bt_to']) if row['bt_to'] else None,
        weekdays_filter=[int(x) for x in row['weekdays_filter'].split(',')] if row['weekdays_filter'] else [],
        batch_id=row['batch_id'],
        testlist_id=row['testlist_id'],
        start_time=row['start_time'],
        stop_time=row['stop_time'],
        status=row['status'],
        #last_started=zoneNY.localize(datetime.fromisoformat(row['last_started'])) if row['last_started'] else None,
        last_processed=datetime.fromisoformat(row['last_processed']) if row['last_processed'] else None,
        history=row['history'],
        valid_from=datetime.fromisoformat(row['valid_from']) if row['valid_from'] else None,
        valid_to=datetime.fromisoformat(row['valid_to']) if row['valid_to'] else None,
        runner_id = row['runner_id'] if row['runner_id'] and is_running else None,  #runner_id is only present if it is running
        strat_running = is_running) #cant believe this when called from separate process  as not current
    return res

#prevede dict radku zpatky na objekt vcetme retypizace
def row_to_runarchiveview(row: dict) -> RunArchiveView:
    a =  RunArchiveView(
        id=row['runner_id'],
        strat_id=row['strat_id'],
        batch_id=row['batch_id'],
        symbol=row['symbol'],
        name=row['name'],
        note=row['note'],
        started=datetime.fromisoformat(row['started']) if row['started'] else None,
        stopped=datetime.fromisoformat(row['stopped']) if row['stopped'] else None,
        mode=row['mode'],
        account=row['account'],
        bt_from=datetime.fromisoformat(row['bt_from']) if row['bt_from'] else None,
        bt_to=datetime.fromisoformat(row['bt_to']) if row['bt_to'] else None,
        ilog_save=bool(row['ilog_save']),
        profit=float(row['profit']),
        trade_count=int(row['trade_count']),
        end_positions=int(row['end_positions']),
        end_positions_avgp=float(row['end_positions_avgp']),
        metrics=orjson.loads(row['metrics']) if row['metrics'] else None,
        batch_profit=int(row['batch_profit']) if row['batch_profit'] and row['batch_id'] else 0,
        batch_count=int(row['batch_count']) if row['batch_count'] and row['batch_id'] else 0,
    )
    return a

#prevede dict radku zpatky na objekt vcetme retypizace
def row_to_runarchive(row: dict) -> RunArchive:
    return RunArchive(
        id=row['runner_id'],
        strat_id=row['strat_id'],
        batch_id=row['batch_id'],
        symbol=row['symbol'],
        name=row['name'],
        note=row['note'],
        started=datetime.fromisoformat(row['started']) if row['started'] else None,
        stopped=datetime.fromisoformat(row['stopped']) if row['stopped'] else None,
        mode=row['mode'],
        account=row['account'],
        bt_from=datetime.fromisoformat(row['bt_from']) if row['bt_from'] else None,
        bt_to=datetime.fromisoformat(row['bt_to']) if row['bt_to'] else None,
        strat_json=orjson.loads(row['strat_json']),
        settings=orjson.loads(row['settings']),
        ilog_save=bool(row['ilog_save']),
        profit=float(row['profit']),
        trade_count=int(row['trade_count']),
        end_positions=int(row['end_positions']),
        end_positions_avgp=float(row['end_positions_avgp']),
        metrics=orjson.loads(row['metrics']),
        stratvars_toml=row['stratvars_toml']
    )