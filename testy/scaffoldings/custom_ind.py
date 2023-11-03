import numpy as np
import matplotlib.pyplot as plt
from v2realbot.controller.services import get_archived_runner_details_byID, preview_indicator_byTOML
from v2realbot.common.model import RunArchiveDetail, InstantIndicator
from scipy.signal import argrelextrema
from v2realbot.utils.utils import AttributeDict, zoneNY, zonePRG, safe_get, dict_replace_value, Store, parse_toml_string, json_serial, is_open_hours, send_to_telegram

##SCAFFOLDING for development of new indicator

runner_id = "7512b097-1f29-4c61-a331-2b1a40fd3f91"

toml = """
#[stratvars.indicators.local_maxik]
type = 'custom'
subtype = 'basestats'
on_confirmed_only = true
cp.lookback = 30
cp.source = 'vwap'
cp.function = 'maxima'
"""

toml = """
type = 'custom'
subtype = 'expression'
on_confirmed_only = true
cp.expression = 'int(utls.is_pivot(high,3))'
"""

toml = """
type = 'custom'
subtype = 'expression'
on_confirmed_only = true
cp.expression = 'int(utls.is_pivot(high,3))'
"""


res, val = get_archived_runner_details_byID(runner_id)
if res < 0:
    print("error fetching runner")
    print(res)

detail = RunArchiveDetail(**val)

res, toml_parsed = parse_toml_string(toml)
if res < 0:
    print("invalid tml",res, toml)
print(toml_parsed)
#toml_parsed = AttributeDict(**toml_parsed)
# for i in toml_parsed["stratvars"]["indicators"]:
#     break

ind: InstantIndicator = InstantIndicator(name="testind", toml=toml)

result, new_ind_values = preview_indicator_byTOML(id=runner_id, indicator=ind)
if result < 0:
    print("error", result, val)

# detail.indicators[0]
price_series = np.array(detail.bars["vwap"])
new_ind_value = np.array(new_ind_values)
#price_series = detail.bars["vwap"]
#timestamps = detail.bars["time"]

# Plot the price series with local maxima and minima
plt.figure(figsize=(10, 6))
plt.plot(range(len(price_series)), price_series, label='Price')
plt.plot(range(len(new_ind_value)), new_ind_value, label='Indicator')
plt.xlabel('Time')
plt.ylabel('Price')
plt.title('Price Series with Local Maxima and Minima')
plt.legend()
plt.show()


