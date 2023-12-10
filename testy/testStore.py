import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pickle
from v2realbot.common.model import StrategyInstance
from typing import List, Self

#class to persist
class Store:
    def __init__(self) -> None:
        self.silist : List[StrategyInstance]  = None
        self.db_file ="cache/strategyinstances.cache"
        if os.path.exists(self.db_file):
            with open (self.db_file, 'rb') as fp:
                self.silist = pickle.load(fp)

    def save(self):
        with open(self.db_file, 'wb') as fp:
            pickle.dump(self.silist, fp)

db = Store()
print(db.silist)
db.silist.append(StrategyInstance(
                            id2=1,
                            name="DD",
                            symbol="DD",
                            class_name="DD",
                            script="DD",
                            open_rush=1,
                            close_rush=1,
                            stratvars_conf="DD",
                            add_data_conf="DD"))

print(db.silist)
db.silist = []
print(len(db.silist))
db.save()





# class Neco:
#     def __init__(self) -> None:
#         pass
#     a = 1
#     b = 2

#     def toJson(self):
#         return orjson.dumps(self, default=lambda o: o.__dict__)

# db.append(Neco.a)

# db.append(Neco.b)

# db.append(Neco)

# print(Neco)