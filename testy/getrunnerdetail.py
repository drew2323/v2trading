
from v2realbot.common.model import RunDay, StrategyInstance, Runner, RunRequest, RunArchive, RunArchiveView, RunArchiveViewPagination, RunArchiveDetail, RunArchiveChange, Bar, TradeEvent, TestList, Intervals, ConfigItem, InstantIndicator, DataTablesRequest
import v2realbot.controller.services as cs
from v2realbot.utils.utils import slice_dict_lists,zoneUTC,safe_get, AttributeDict
id = "b11c66d9-a9b6-475a-9ac1-28b11e1b4edf"
state = AttributeDict(vars={})

##základ pro init_attached_data in strategy.init

# def get_previous_runner(state):
#     runner : Runner
#     res, runner = cs.get_runner(state.runner_id)
#     if res < 0:
#         print(f"Not running {id}")
#         return 0, None
    
#     return 0, runner.batch_id

def attach_previous_data(state):
    runner : Runner
    #get batch_id of current runer
    res, runner = cs.get_runner(state.runner_id)
    if res < 0 or runner.batch_id is None:
        print(f"Couldnt get previous runner {val}")
        return None
    
    batch_id = runner.batch_id
    #batch_id = "6a6b0bcf"

    res, runner_ids =cs.get_archived_runnerslist_byBatchID(batch_id, "desc")
    if res < 0:
        msg = f"error whne fetching runners of batch {batch_id} {runner_ids}"
        print(msg)
        return None
    
    if runner_ids is None or len(runner_ids) == 0:
        print(f"no runners found for batch {batch_id} {runner_ids}")
        return None
    
    last_runner = runner_ids[0]
    print("Previous runner identified:", last_runner)

    #get details from the runner
    res, val = cs.get_archived_runner_details_byID(last_runner)
    if res < 0:
        print(f"no archived runner {last_runner}")

    detail = RunArchiveDetail(**val)
    #print("toto jsme si dotahnuli", detail.bars)

    # from stratvars directives 
    attach_previous_bars_indicators = safe_get(state.vars, "attach_previous_bars_indicators", 50)
    attach_previous_cbar_indicators = safe_get(state.vars, "attach_previous_cbar_indicators", 50)
    # [stratvars]
    #     attach_previous_bars_indicators = 50
    #     attach_previous_cbar_indicators = 50

    #indicators datetime utc
    indicators = slice_dict_lists(d=detail.indicators[0],last_item=attach_previous_bars_indicators, time_to_datetime=True)

    #time -datetime utc, updated - timestamp float
    bars = slice_dict_lists(d=detail.bars, last_item=attach_previous_bars_indicators, time_to_datetime=True)

    #cbar_indicatzors #float
    cbar_inds = slice_dict_lists(d=detail.indicators[1],last_item=attach_previous_cbar_indicators)

    #USE these as INITs - TADY SI TO JESTE ZASTAVIT a POROVNAT
    print(f"{state.indicators=} NEW:{indicators=}")
    state.indicators = indicators
    print(f"{state.bars=} NEW:{bars=}")
    state.bars = bars
    print(f"{state.cbar_indicators=} NEW:{cbar_inds=}")
    state.cbar_indicators = cbar_inds

    print("BARS and INDS INITIALIZED")
    #bars


    #tady budou pripadne dalsi inicializace, z ext_data
    print("EXT_DATA", detail.ext_data)
    #podle urciteho nastaveni napr.v konfiguraci se pouziji urcite promenne

    #pridavame dailyBars z extData
    # if hasattr(detail, "ext_data") and "dailyBars" in detail.ext_data:
    #     state.dailyBars = detail.ext_data["dailyBars"]


if __name__ == "__main__":
    attach_previous_data(state)