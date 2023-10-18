import sqlite3
from v2realbot.config import DATA_DIR
from v2realbot.utils.utils import json_serial
from uuid import UUID, uuid4
import json
from datetime import datetime
from v2realbot.enums.enums import RecordType, StartBarAlign, Mode, Account
from v2realbot.common.model import RunArchiveDetail, RunArchive, RunArchiveView
from tinydb import TinyDB, Query, where
from v2realbot.common.db import pool, execute_with_retry



# Helper function to transform a row to a RunArchive object
def row_to_object(row: dict) -> RunArchive:
    return RunArchive(
        id=row.get('id'),
        strat_id=row.get('strat_id'),
        batch_id=row.get('batch_id'),
        symbol=row.get('symbol'),
        name=row.get('name'),
        note=row.get('note'),
        started=row.get('started'),
        stopped=row.get('stopped'),
        mode=row.get('mode'),
        account=row.get('account'),
        bt_from=row.get('bt_from'),
        bt_to=row.get('bt_to'),
        strat_json=row.get('strat_json'),
        stratvars=row.get('stratvars'),
        settings=row.get('settings'),
        ilog_save=row.get('ilog_save'),
        profit=row.get('profit'),
        trade_count=row.get('trade_count'),
        end_positions=row.get('end_positions'),
        end_positions_avgp=row.get('end_positions_avgp'),
        metrics=row.get('open_orders'),
        #metrics=json.loads(row.get('metrics')) if row.get('metrics') else None,
        stratvars_toml=row.get('stratvars_toml')
    )

def get_all_archived_runners():
    conn = pool.get_connection()
    try:
        conn.row_factory = lambda c, r: json.loads(r[0])
        c = conn.cursor()
        res = c.execute(f"SELECT data FROM runner_header")
    finally:
        conn.row_factory = None
        pool.release_connection(conn)        
    return 0, res.fetchall()

def insert_archive_header(archeader: RunArchive):
    conn = pool.get_connection()
    try:
        c = conn.cursor()
        json_string = json.dumps(archeader, default=json_serial)
        if archeader.batch_id is not None:
            statement = f"INSERT INTO runner_header (runner_id, batch_id, ra)  VALUES ('{str(archeader.id)}','{str(archeader.batch_id)}','{json_string}')"
        else:
            statement = f"INSERT INTO runner_header (runner_id, ra) VALUES ('{str(archeader.id)}','{json_string}')"
            
        res = execute_with_retry(c,statement)
        conn.commit()
    finally:
        pool.release_connection(conn)
    return res.rowcount

set = list[RunArchive]

def migrate_to_columns(ra: RunArchive):
    conn = pool.get_connection()
    try:

        c = conn.cursor()
        # statement = f"""UPDATE runner_header SET
        #     strat_id='{str(ra.strat_id)}',
        #     batch_id='{ra.batch_id}',
        #     symbol='{ra.symbol}',
        #     name='{ra.name}',
        #     note='{ra.note}',
        #     started='{ra.started}',
        #     stopped='{ra.stopped}',
        #     mode='{ra.mode}',
        #     account='{ra.account}',
        #     bt_from='{ra.bt_from}',
        #     bt_to='{ra.bt_to}',
        #     strat_json='ra.strat_json)',
        #     settings='{ra.settings}',
        #     ilog_save='{ra.ilog_save}',
        #     profit='{ra.profit}',
        #     trade_count='{ra.trade_count}',
        #     end_positions='{ra.end_positions}',
        #     end_positions_avgp='{ra.end_positions_avgp}',
        #     metrics='{ra.metrics}',
        #     stratvars_toml="{ra.stratvars_toml}"
        # WHERE runner_id='{str(ra.strat_id)}'
        # """
        # print(statement)

        res = c.execute('''
            UPDATE runner_header 
            SET strat_id=?, batch_id=?, symbol=?, name=?, note=?, started=?, stopped=?, mode=?, account=?, bt_from=?, bt_to=?, strat_json=?, settings=?, ilog_save=?, profit=?, trade_count=?, end_positions=?, end_positions_avgp=?, metrics=?, stratvars_toml=?
            WHERE runner_id=?
            ''',
            (str(ra.strat_id), ra.batch_id, ra.symbol, ra.name, ra.note, ra.started, ra.stopped, ra.mode, ra.account, ra.bt_from, ra.bt_to, json.dumps(ra.strat_json), json.dumps(ra.settings), ra.ilog_save, ra.profit, ra.trade_count, ra.end_positions, ra.end_positions_avgp, json.dumps(ra.metrics), ra.stratvars_toml, str(ra.id)))

        conn.commit()
    finally:

        pool.release_connection(conn)        
    return 0, res

res, set = get_all_archived_runners()
print(f"fetched {len(set)}")
for row in set:
    ra: RunArchive = row_to_object(row)
    print(f"item {ra.id}")
    res, val = migrate_to_columns(ra)
    print(res,val)
    print("migrated", ra.id)


#print(set)

# def migrate():
#     set = list[RunArchiveDetail]
#     #res, set = get_all_archived_runners_detail()
#     print(f"fetched {len(set)}")
#     for row in set:
#         #insert_archive_detail(row)
#         print(f"inserted {row['id']}")


# idecko = uuid4()

# runArchiveDetail: RunArchiveDetail = RunArchiveDetail(id = idecko,
#                                                     name="nazev runneru",
#                                                     bars=bars,
#                                                     indicators=[dict(time=[])],
#                                                     statinds=dict(neco=233,zase=333),
#                                                     trades=list(dict()))