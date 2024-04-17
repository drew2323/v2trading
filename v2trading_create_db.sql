BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "test_list" (
	"id"	varchar(32) NOT NULL,
	"name"	varchar(255) NOT NULL,
	"dates"	json NOT NULL
);
CREATE TABLE IF NOT EXISTS "runner_detail" (
	"runner_id"	varchar(32) NOT NULL,
	"data"	json NOT NULL,
	PRIMARY KEY("runner_id")
);
CREATE TABLE IF NOT EXISTS "runner_header" (
	"runner_id"	varchar(32) NOT NULL,
	"strat_id"	TEXT,
	"batch_id"	TEXT,
	"symbol"	TEXT,
	"name"	TEXT,
	"note"	TEXT,
	"started"	TEXT,
	"stopped"	TEXT,
	"mode"	TEXT,
	"account"	TEXT,
	"bt_from"	TEXT,
	"bt_to"	TEXT,
	"strat_json"	TEXT,
	"settings"	TEXT,
	"ilog_save"	INTEGER,
	"profit"	NUMERIC,
	"trade_count"	INTEGER,
	"end_positions"	INTEGER,
	"end_positions_avgp"	NUMERIC,
	"metrics"	TEXT,
	"stratvars_toml"	TEXT,
	"transferables"        TEXT,
	PRIMARY KEY("runner_id")
);
CREATE TABLE IF NOT EXISTS "config_table" (
	"id"	INTEGER,
	"item_name"	TEXT NOT NULL,
	"json_data"	JSON NOT NULL,
	"item_lang"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "runner_logs" (
	"runner_id"	varchar(32) NOT NULL,
	"time"	real NOT NULL,
	"data"	json NOT NULL
);
CREATE TABLE "run_manager" (
    "moddus"    TEXT NOT NULL,
    "id"    varchar(32),
    "strat_id"  varchar(32) NOT NULL,
    "symbol"    TEXT,
    "account"   TEXT NOT NULL,
    "mode"  TEXT NOT NULL,
    "note"  TEXT,
    "ilog_save" BOOLEAN,
    "bt_from"   TEXT,
    "bt_to" TEXT,
    "weekdays_filter"   TEXT,
    "batch_id"  TEXT,
    "start_time"    TEXT NOT NULL,
    "stop_time" TEXT NOT NULL,
    "status"    TEXT NOT NULL,
    "last_processed"    TEXT,
    "history"   TEXT,
    "valid_from"    TEXT,
    "valid_to"  TEXT,
    "testlist_id"   TEXT,
    "runner_id" varchar2(32),
    "market" TEXT,
    PRIMARY KEY("id")
);
CREATE INDEX idx_moddus ON run_manager (moddus);
CREATE INDEX idx_status ON run_manager (status);
CREATE INDEX idx_status_moddus ON run_manager (status, moddus);
CREATE INDEX idx_valid_from_to ON run_manager (valid_from, valid_to);
CREATE INDEX idx_stopped_batch_id ON runner_header (stopped, batch_id);
CREATE INDEX idx_search_value ON runner_header (strat_id, batch_id);
CREATE INDEX IF NOT EXISTS "index_runner_header_pk" ON "runner_header" (
	"runner_id"
);
CREATE INDEX IF NOT EXISTS "index_runner_header_strat" ON "runner_header" (
	"strat_id"
);
CREATE INDEX IF NOT EXISTS "index_runner_header_batch" ON "runner_header" (
	"batch_id"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_runner_detail_pk" ON "runner_detail" (
	"runner_id"
);
CREATE INDEX IF NOT EXISTS "index_runner_logs" ON "runner_logs" (
	"runner_id",
	"time"
);
INSERT INTO config_table VALUES (1, "test", "{}", "json");
COMMIT;
