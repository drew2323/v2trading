from v2realbot.config import DATA_DIR
import sqlite3
import queue
import threading
from datetime import time

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
                time.sleep(retry_interval)
                continue
            else:
                raise e


#for pool of connections if necessary
pool = ConnectionPool(10)
#for one shared connection (used for writes only in WAL mode)
insert_conn = sqlite3.connect(sqlite_db_file, check_same_thread=False)
insert_queue = queue.Queue()