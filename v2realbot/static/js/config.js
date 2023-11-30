//JS code for using config value on the frontend
//TODO zvazit presunuti do TOML z JSONu

// CREATE TABLE "config_table" (
// 	"id"	INTEGER,
// 	"item_name"	TEXT NOT NULL,
// 	"json_data"	JSON NOT NULL,
// 	"item_lang"	TEXT NOT NULL, //not implemented yet
// 	PRIMARY KEY("id" AUTOINCREMENT)
// ); //novy komentar

let configData = {}

//sluzba z globalni promenne s JS configuraci dotahne dana data
function get_from_config(name, def_value) {
    def_value = def_value ? def_value : null 
    console.log("required", name, configData)
    if ((configData["JS"]) && (configData["JS"][name] !== undefined)) {
        console.log("returned from config", configData["JS"][name])
        return configData["JS"][name]
    }
    else {
        console.log("returned def_value", def_value)
        return def_value
    }
}


function loadConfig(configName) {
    return new Promise((resolve, reject) => {
        const rec = new Object();
        rec.item_name = configName;
        $.ajax({
            url: `/config-items-by-name/`,
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-API-Key', API_KEY);
            },
            method: 'GET',
            contentType: "application/json",
            dataType: "json",
            data: rec,
            success: function (data) {
                try {
                    var configData = JSON.parse(data.json_data);
                    resolve(configData);  // Resolve the promise with configData
                }
                catch (error) {
                    reject(error);  // Reject the promise if there's an error
                }
            },
            error: function(xhr, status, error) {
                reject(new Error(xhr.responseText));  // Reject the promise on AJAX error
            }
        });
    });
}

function getConfiguration(area) {
    return loadConfig(area).then(configData => {
        console.log("Config loaded for", area, configData);
        return configData;
    }).catch(error => {
        console.error('Error loading config for', area, error);
        throw error; // Re-throw to allow caller to handle
    });
}

//asynchrone naplni promennou
async function loadConfigData(jsConfigName) {
    try {
        configData[jsConfigName] = await getConfiguration(jsConfigName);
        console.log("jsConfigName", jsConfigName);
    } catch (error) {
        console.error('Failed to load button configuration:',jsConfigName, error);
    }
}


$(document).ready(function () {
    var jsConfigName = "JS"
    loadConfigData(jsConfigName)
});
