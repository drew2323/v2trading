import numpy as np
import matplotlib.pyplot as plt
from v2realbot.controller.services import get_archived_runner_details_byID
from v2realbot.common.model import RunArchiveDetail
# Generate sample price data
timestamps = np.arange('2023-10-27', '2023-10-28', dtype='datetime64[s]')
price = 100 + np.arange(100) * 0.5

id = "e74b5d35-6552-4dfc-ba59-2eda215af292"

res, val = get_archived_runner_details_byID(id)
if res < 0:
    print(res)

detail = RunArchiveDetail(**val)
# detail.indicators[0]
price = detail.bars["vwap"]
timestamps = detail.bars["time"]

