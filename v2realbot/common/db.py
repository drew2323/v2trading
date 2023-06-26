from v2realbot.config import DATA_DIR
import sqlite3

sqlite_db_file = DATA_DIR + "/v2trading.db"
conn = sqlite3.connect(sqlite_db_file, check_same_thread=False, isolation_level=None)