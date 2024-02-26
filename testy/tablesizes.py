import queue
import sqlite3
import threading
from appdirs import user_data_dir

DATA_DIR = user_data_dir("v2realbot")
sqlite_db_file = DATA_DIR + "/v2trading.db"

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


pool = ConnectionPool(10)

def get_table_sizes_in_mb():
    # Connect to the SQLite database
    conn = pool.get_connection()
    cursor = conn.cursor()

    # Get the list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    # Dictionary to store table sizes
    table_sizes = {}

    for table in tables:
        table_name = table[0]

        # Get total number of rows in the table
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        row_count = cursor.fetchone()[0]

        if row_count > 0:
            # Sample a few rows (e.g., 10 rows) and calculate average row size
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 10;")
            sample_rows = cursor.fetchall()
            total_sample_size = sum(sum(len(str(cell)) for cell in row) for row in sample_rows)
            avg_row_size = total_sample_size / len(sample_rows)

            # Estimate table size in megabytes
            size_in_mb = (avg_row_size * row_count) / (1024 * 1024)
        else:
            size_in_mb = 0

        table_sizes[table_name] = {'size_mb': size_in_mb, 'rows': row_count}

    conn.close()
    return table_sizes

# Usage example
db_path = 'path_to_your_database.db'
table_sizes = get_table_sizes_in_mb()
for table, info in table_sizes.items():
    print(f"Table: {table}, Size: {info['size_mb']} MB, Rows: {info['rows']}")

