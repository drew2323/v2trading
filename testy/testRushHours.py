from v2realbot.utils.utils import is_open_rush, zoneNY
from datetime import datetime, date, timedelta, time

ted = datetime.now().astimezone(zoneNY)

ted = datetime(year=2023, month=5, day=9, hour=9, minute=35, tzinfo=zoneNY)
print(ted)

rush = is_open_rush(ted, 30)

print(rush)
business_hours = {
    "from": time(hour=9, minute=30),
    "to": time(hour=16, minute=0)
}
rushtime = (datetime.combine(date.today(), business_hours["from"]) + timedelta(minutes=30)).time()
print(rushtime)