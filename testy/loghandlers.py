from v2realbot.enums.enums import Mode, Account
from v2realbot.config import get_key
import structlog
from rich import print
from datetime import datetime
from v2realbot.utils.utils import zoneNY

def timestamper(_, __, event_dict):
    event_dict["time"] = datetime.now().isoformat()
    return event_dict

#structlog.configure(processors=[timestamper, structlog.processors.KeyValueRenderer()])

log = structlog.get_logger()

def neco(arg: int):
    log.bind(arg=arg)
    log.info("neco funkce")
    arg = arg + 2
    return arg

def neco2(kwargs):
    print("neco 2")
    for i in 12:
        print(i)

ted = datetime.now().astimezone(zoneNY)
promena = [1,2]

log.bind(ted=ted, promena=promena)

d = dict(a=2,b="33",dalsiklic=4432, pole=[2,3,4])
log.info("beforeprint")
print(d)
d = neco(3)
log.info("udalost")


log.info("incoming",d=d)










