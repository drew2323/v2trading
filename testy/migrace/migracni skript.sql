
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




###a pak tato cast na odstraneni data sloupce
CREATE TABLE "sqlb_temp_table_2" (
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
	PRIMARY KEY("runner_id")
);
INSERT INTO "main"."sqlb_temp_table_2" ("account","batch_id","bt_from","bt_to","end_positions","end_positions_avgp","ilog_save","metrics","mode","name","note","profit","runner_id","settings","started","stopped","strat_id","strat_json","stratvars_toml","symbol","trade_count") SELECT "account","batch_id","bt_from","bt_to","end_positions","end_positions_avgp","ilog_save","metrics","mode","name","note","profit","runner_id","settings","started","stopped","strat_id","strat_json","stratvars_toml","symbol","trade_count" FROM "main"."runner_header"
PRAGMA defer_foreign_keys;
PRAGMA defer_foreign_keys = '1';
DROP TABLE "main"."runner_header"
ALTER TABLE "main"."sqlb_temp_table_2" RENAME TO "runner_header"
PRAGMA defer_foreign_keys = '0';
CREATE INDEX "index_runner_header_pk" ON "runner_header" (
	"runner_id"
);
CREATE INDEX "index_runner_header_strat" ON "runner_header" (
	"strat_id"
);
CREATE INDEX "index_runner_header_batch" ON "runner_header" (
	"batch_id"
);
RELEASE "db4s_renamecolumn_1697637283072384";
PRAGMA database_list;
SELECT type,name,sql,tbl_name FROM "main".sqlite_master;
SELECT type,name,sql,tbl_name FROM sqlite_temp_master;
PRAGMA "main".foreign_key_check
RELEASE "db4s_edittable_1697637265835032";
PRAGMA foreign_keys = '1';