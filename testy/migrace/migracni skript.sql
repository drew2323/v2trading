
CREATE TABLE "sqlb_temp_table_1" (
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
	"data"	json NOT NULL,
	PRIMARY KEY("runner_id")
);
INSERT INTO "main"."sqlb_temp_table_1" ("batch_id","data","runner_id") SELECT "batch_id","data","runner_id" FROM "main"."runner_header"
PRAGMA defer_foreign_keys;
PRAGMA defer_foreign_keys = '1';
DROP TABLE "main"."runner_header"
ALTER TABLE "main"."sqlb_temp_table_1" RENAME TO "runner_header"
PRAGMA defer_foreign_keys = '0';

CREATE INDEX "index_runner_header_batch" ON "runner_header" (
	"batch_id"
)

CREATE INDEX "index_runner_header_pk" ON "runner_header" (
	"runner_id"
)

CREATE INDEX "index_runner_header_strat" ON "runner_header" (
	"strat_id"
)
