

import v2realbot.controller.services as cs

#[stratvars.indicators.vwma]
runner_id = "b44d6d8f-b44d-45b1-ad7a-7ee8b0facead"
toml = """
    type = "custom"
    subtype = "vwma"
    on_confirmed_only = true
    cp.source = "vwap"
    cp.ref_source = "volume"
    cp.lookback = 50
"""

res, vals = cs.preview_indicator_byTOML(id=runner_id, toml=toml)

print(res)
print(vals)
