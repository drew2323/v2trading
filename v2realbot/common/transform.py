from v2realbot.common.model import RunArchive, RunArchiveView, RunManagerRecord
from datetime import datetime
import orjson
import v2realbot.controller.services as cs

#prevede dict radku zpatky na objekt vcetme retypizace
def row_to_runmanager(row: dict) -> RunManagerRecord:

    is_running = cs.is_runner_running(row['runner_id']) if row['runner_id'] else False

    res = RunManagerRecord(
        moddus=row['moddus'],
        id=row['id'],
        strat_id=row['strat_id'],
        symbol=row['symbol'],
        mode=row['mode'],
        account=row['account'],
        note=row['note'],
        ilog_save=bool(row['ilog_save']),
        bt_from=datetime.fromisoformat(row['bt_from']) if row['bt_from'] else None,
        bt_to=datetime.fromisoformat(row['bt_to']) if row['bt_to'] else None,
        weekdays_filter=[int(x) for x in row['weekdays_filter'].split(',')] if row['weekdays_filter'] else [],
        batch_id=row['batch_id'],
        testlist_id=row['testlist_id'],
        start_time=row['start_time'],
        stop_time=row['stop_time'],
        status=row['status'],
        #last_started=zoneNY.localize(datetime.fromisoformat(row['last_started'])) if row['last_started'] else None,
        last_processed=datetime.fromisoformat(row['last_processed']) if row['last_processed'] else None,
        history=row['history'],
        valid_from=datetime.fromisoformat(row['valid_from']) if row['valid_from'] else None,
        valid_to=datetime.fromisoformat(row['valid_to']) if row['valid_to'] else None,
        runner_id = row['runner_id'] if row['runner_id'] and is_running else None,  #runner_id is only present if it is running
        strat_running = is_running) #cant believe this when called from separate process  as not current
    return res

#prevede dict radku zpatky na objekt vcetme retypizace
def row_to_runarchiveview(row: dict) -> RunArchiveView:
    a =  RunArchiveView(
        id=row['runner_id'],
        strat_id=row['strat_id'],
        batch_id=row['batch_id'],
        symbol=row['symbol'],
        name=row['name'],
        note=row['note'],
        started=datetime.fromisoformat(row['started']) if row['started'] else None,
        stopped=datetime.fromisoformat(row['stopped']) if row['stopped'] else None,
        mode=row['mode'],
        account=row['account'],
        bt_from=datetime.fromisoformat(row['bt_from']) if row['bt_from'] else None,
        bt_to=datetime.fromisoformat(row['bt_to']) if row['bt_to'] else None,
        ilog_save=bool(row['ilog_save']),
        profit=float(row['profit']),
        trade_count=int(row['trade_count']),
        end_positions=int(row['end_positions']),
        end_positions_avgp=float(row['end_positions_avgp']),
        metrics=orjson.loads(row['metrics']) if row['metrics'] else None,
        batch_profit=int(row['batch_profit']) if row['batch_profit'] and row['batch_id'] else 0,
        batch_count=int(row['batch_count']) if row['batch_count'] and row['batch_id'] else 0,
    )
    return a

#prevede dict radku zpatky na objekt vcetme retypizace
def row_to_runarchive(row: dict) -> RunArchive:
    return RunArchive(
        id=row['runner_id'],
        strat_id=row['strat_id'],
        batch_id=row['batch_id'],
        symbol=row['symbol'],
        name=row['name'],
        note=row['note'],
        started=datetime.fromisoformat(row['started']) if row['started'] else None,
        stopped=datetime.fromisoformat(row['stopped']) if row['stopped'] else None,
        mode=row['mode'],
        account=row['account'],
        bt_from=datetime.fromisoformat(row['bt_from']) if row['bt_from'] else None,
        bt_to=datetime.fromisoformat(row['bt_to']) if row['bt_to'] else None,
        strat_json=orjson.loads(row['strat_json']),
        settings=orjson.loads(row['settings']),
        ilog_save=bool(row['ilog_save']),
        profit=float(row['profit']),
        trade_count=int(row['trade_count']),
        end_positions=int(row['end_positions']),
        end_positions_avgp=float(row['end_positions_avgp']),
        metrics=orjson.loads(row['metrics']),
        stratvars_toml=row['stratvars_toml'],
        transferables=orjson.loads(row['transferables']) if row['transferables'] else None
    )