import pickle
import os
from v2realbot.config import STRATVARS_UNCHANGEABLES, ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY, ACCOUNT1_LIVE_API_KEY, ACCOUNT1_LIVE_SECRET_KEY, DATA_DIR,BT_FILL_CONS_TRADES_REQUIRED,BT_FILL_LOG_SURROUNDING_TRADES,BT_FILL_CONDITION_BUY_LIMIT,BT_FILL_CONDITION_SELL_LIMIT, GROUP_TRADES_WITH_TIMESTAMP_LESS_THAN, MEDIA_DIRECTORY, RUNNER_DETAIL_DIRECTORY

# #class to persist
# class Store:
#     stratins : List[StrategyInstance]  = []
#     runners: List[Runner] = []
#     def __init__(self) -> None:
#         self.db_file = DATA_DIR + "/strategyinstances.cache"
#         if os.path.exists(self.db_file):
#             with open (self.db_file, 'rb') as fp:
#                 self.stratins = pickle.load(fp)

#     def save(self):
#         with open(self.db_file, 'wb') as fp:
#             pickle.dump(self.stratins, fp)


#db = Store()

def try_reading_after_skipping_bytes(file_path, skip_bytes, chunk_size=1024):
    with open(file_path, 'rb') as file:
        file.seek(skip_bytes)  # Skip initial bytes
        while True:
            try:
                data = pickle.load(file)
                print("Recovered data:", data)
                break  # Exit loop if successful
            except EOFError:
                print("Reached end of file without recovering data.")
                break
            except pickle.UnpicklingError:
                # Move ahead in file by chunk_size bytes and try again
                file.seek(file.tell() + chunk_size, os.SEEK_SET)


file_path = DATA_DIR + "/strategyinstances.cache"
try_reading_after_skipping_bytes(file_path,1)