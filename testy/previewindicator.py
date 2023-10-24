

import v2realbot.controller.services as cs
from v2realbot.common.model import RunDay, StrategyInstance, Runner, RunRequest, RunArchive, RunArchiveView, RunArchiveDetail, RunArchiveChange, Bar, TradeEvent, TestList, Intervals, ConfigItem, InstantIndicator
#[stratvars.indicators.vwma]
runner_id = "1ac42f29-b902-44df-9bd6-e2a430989705"
toml = """
#[stratvars.indicators.cross]
type = 'custom'
subtype = 'conditional'
on_confirmed_only = true
[cp.conditions.crossdown]
vwap.change_val_if_crossed_down = 'emaSlow'
true_val = -1
[cp.conditions.crossup]
vwap.change_val_if_crossed_up = 'emaSlow'
true_val = 1
"""

toml = """
#[stratvars.indicators.rsi14]
type = 'RSI'
source = 'vwap'
length = 14
on_confirmed_only = true
"""
indicator = InstantIndicator(name="rsi14alt", toml=toml)

res, vals = cs.preview_indicator_byTOML(id=runner_id, indicator=indicator)

print(res)
print(vals)
