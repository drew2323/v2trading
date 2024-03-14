
from v2realbot.common.model import RunDay, StrategyInstance, Runner, RunRequest, RunArchive, RunArchiveView, RunArchiveViewPagination, RunArchiveDetail, RunArchiveChange, Bar, TradeEvent, TestList, Intervals, ConfigItem, InstantIndicator, DataTablesRequest
import v2realbot.controller.services as cs
from v2realbot.utils.utils import slice_dict_lists,zoneUTC,safe_get, AttributeDict, filter_timeseries_by_timestamp
#id = "b11c66d9-a9b6-475a-9ac1-28b11e1b4edf"
#state = AttributeDict(vars={})
from rich import print

def attach_previous_data(state):
    """""
    Attaches data from previous runner of the same batch.
    """""
    print("ATTACHING PREVIOUS DATA")
    runner : Runner
    #get batch_id of current runer
    res, runner = cs.get_runner(state.runner_id)
    if res < 0:
        if runner.batch_id is None:
            print(f"No batch_id found for runner {runner.id}")
        else:
            print(f"Couldnt get previous runner {state.runner_id} error: {runner}")
        return None
    
    batch_id = runner.batch_id
    #batch_id = "6a6b0bcf"
    res, runner_ids =cs.get_archived_runnerslist_byBatchID(batch_id, "desc")
    if res < 0:
        msg = f"error whne fetching runners of batch {batch_id} {runner_ids}"
        print(msg)
        return None
    
    if runner_ids is None or len(runner_ids) == 0:
        print(f"NO runners found for batch {batch_id} {runner_ids}")
        return None
    
    last_runner = runner_ids[0]
    print("Previous runner identified:", last_runner)

    #get archived header - to get transferables
    runner_header : RunArchive = None
    res, runner_header = cs.get_archived_runner_header_byID(last_runner)
    if res < 0:
        print(f"Error when fetching runner header {last_runner}")
        return None

    state.vars["transferables"] = runner_header.transferables
    print("INITIALIZED transferables", state.vars["transferables"])


    #get details from the runner
    print(f"Fetching runner details of {last_runner}")
    res, val = cs.get_archived_runner_details_byID(last_runner)
    if res < 0:
        print(f"no archived runner {last_runner}")
        return None

    detail = RunArchiveDetail(**val)
    #print("toto jsme si dotahnuli", detail.bars)

    # from stratvars directives 
    attach_previous_bar_data = safe_get(state.vars, "attach_previous_bar_data", 50)
    attach_previous_tick_data = safe_get(state.vars, "attach_previous_tick_data", None)
    
    #indicators datetime utc
    indicators = slice_dict_lists(d=detail.indicators[0],last_item=attach_previous_bar_data, time_to_datetime=True)

    #time -datetime utc, updated - timestamp float
    bars = slice_dict_lists(d=detail.bars, last_item=attach_previous_bar_data, time_to_datetime=True)

    #zarovname tick spolu s bar daty
    if attach_previous_tick_data is None:
        oldest_timestamp = bars["updated"][0]

        #returns only values older that oldest_timestamp
        cbar_inds = filter_timeseries_by_timestamp(detail.indicators[1], oldest_timestamp)
    else:
        cbar_inds = slice_dict_lists(d=detail.indicators[1],last_item=attach_previous_tick_data)

    #USE these as INITs - TADY SI TO JESTE ZASTAVIT a POROVNAT
    #print("state.indicatorsL", state.indicators, "NEW:", indicators)
    state.indicators = AttributeDict(**indicators)
    print("transfered indicators:", len(state.indicators["time"]))
    #print("state.bars", state.bars, "NEW:", bars)
    state.bars = AttributeDict(bars)
    print("transfered bars:", len(state.bars["time"]))
    #print("state.cbar_indicators", state.cbar_indicators, "NEW:", cbar_inds)
    state.cbar_indicators = AttributeDict(cbar_inds)
    print("transfered ticks:", len(state.cbar_indicators["time"]))

    print("TRANSFERABLEs INITIALIZED")
    #bars
    #transferable_state_vars = ["martingale", "batch_profit"]
    #1. pri initu se tyto klice v state vars se namapuji do ext_data ext_data["transferrables"]["martingale"] = state.vars["martingale"]
    #2. pri transferu se vse z ext_data["trasferrables"] dá do stejnénné state.vars["martingale"]
    #3. na konci dne se uloží do sloupce transferables v RunArchive

    #pridavame dailyBars z extData
    # if hasattr(detail, "ext_data") and "dailyBars" in detail.ext_data:
    #     state.dailyBars = detail.ext_data["dailyBars"]
    return

# if __name__ == "__main__":
#     attach_previous_data(state)