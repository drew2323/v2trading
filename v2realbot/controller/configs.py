
import v2realbot.common.db as db
from v2realbot.common.model import ConfigItem
import v2realbot.utils.config_handler as ch

# region CONFIG db services
#TODO vytvorit modul pro dotahovani z pythonu (get_from_config(var_name, def_value) {)- stejne jako v js 
#TODO zvazit presunuti do TOML z JSONu
def get_all_config_items():
    conn = db.pool.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT id, item_name, json_data FROM config_table')
        config_items = [{"id": row[0], "item_name": row[1], "json_data": row[2]} for row in cursor.fetchall()]
    finally:
        db.pool.release_connection(conn)
    return 0, config_items

# Function to get a config item by ID
def get_config_item_by_id(item_id):
    conn = db.pool.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT item_name, json_data FROM config_table WHERE id = ?', (item_id,))
        row = cursor.fetchone()
    finally:
        db.pool.release_connection(conn)
    if row is None:
        return -2, "not found"
    else:
        return 0, {"item_name": row[0], "json_data": row[1]}

# Function to get a config item by ID
def get_config_item_by_name(item_name):
    #print(item_name)
    conn = db.pool.get_connection()
    try:
        cursor = conn.cursor()
        query = f"SELECT item_name, json_data FROM config_table WHERE item_name = '{item_name}'"
        #print(query)
        cursor.execute(query)
        row = cursor.fetchone()
        #print(row)
    finally:
        db.pool.release_connection(conn)
    if row is None:
        return -2, "not found"
    else:
        return 0, {"item_name": row[0], "json_data": row[1]}

# Function to create a new config item
def create_config_item(config_item: ConfigItem):
    conn = db.pool.get_connection()
    try:
        try:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO config_table (item_name, json_data) VALUES (?, ?)', (config_item.item_name, config_item.json_data))
            item_id = cursor.lastrowid
            conn.commit()
            print(item_id)
        finally:
            db.pool.release_connection(conn)

        return 0, {"id": item_id, "item_name":config_item.item_name, "json_data":config_item.json_data}
    except Exception as e:
        return -2, str(e)

# Function to update a config item by ID
def update_config_item(item_id, config_item: ConfigItem):
    conn = db.pool.get_connection()
    try:
        try:
            cursor = conn.cursor()
            cursor.execute('UPDATE config_table SET item_name = ?, json_data = ? WHERE id = ?', (config_item.item_name, config_item.json_data, item_id))
            conn.commit()

            #refresh active item je zatím řešena takto natvrdo při updatu položky "active_profile" a při startu aplikace
            if config_item.item_name == "active_profile":
                ch.config_handler.activate_profile()
        finally:
            db.pool.release_connection(conn)
        return 0, {"id": item_id, **config_item.dict()}
    except Exception as e:
        return -2, str(e)
    
# Function to delete a config item by ID
def delete_config_item(item_id):
    conn = db.pool.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM config_table WHERE id = ?', (item_id,))
        conn.commit()
    finally:
       db.pool.release_connection(conn) 
    return 0, {"id": item_id}

# endregion

#Example of using config directive
# config_directive = "overrides"
# ret, res = get_config_item_by_name(config_directive)
# if ret < 0:
#     print(f"CONFIG OVERRIDE {config_directive} Error {res}")
# else:
#     config = orjson.loads(res["json_data"])

#     print("OVERRIDN CFG:", config)
#     for key, value in config.items():
#         if hasattr(cfg, key):
#             print(f"Overriding {key} with {value}")
#             setattr(cfg, key, value)

