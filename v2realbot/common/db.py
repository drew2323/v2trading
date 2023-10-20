from v2realbot.config import DATA_DIR
import sqlite3
import queue
import threading
import time
from v2realbot.common.model import RunArchive, RunArchiveView
from datetime import datetime
import json

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


def execute_with_retry(cursor: sqlite3.Cursor, statement: str, retry_interval: int = 1) -> sqlite3.Cursor:
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
            return cursor.execute(statement)
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
def row_to_runarchiveview(row: dict) -> RunArchiveView:
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
        ilog_save=bool(row['ilog_save']),
        profit=float(row['profit']),
        trade_count=int(row['trade_count']),
        end_positions=int(row['end_positions']),
        end_positions_avgp=float(row['end_positions_avgp']),
        metrics=json.loads(row['metrics']) if row['metrics'] else None
    )

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
        strat_json=json.loads(row['strat_json']),
        settings=json.loads(row['settings']),
        ilog_save=bool(row['ilog_save']),
        profit=float(row['profit']),
        trade_count=int(row['trade_count']),
        end_positions=int(row['end_positions']),
        end_positions_avgp=float(row['end_positions_avgp']),
        metrics=json.loads(row['metrics']),
        stratvars_toml=row['stratvars_toml']
    )