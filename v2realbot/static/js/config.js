//JS code for using config value on the frontend
//TODO zvazit presunuti do TOML z JSONu

configData = {}

function get_from_config(name, def_value) {
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

$(document).ready(function () {
    const apiBaseUrl = '';

    // Function to populate the config list and load JSON data initially
    function loadConfig(configName) {
        const rec = new Object()
        rec.item_name = configName
        $.ajax({
            url: `${apiBaseUrl}/config-items-by-name/`,
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-API-Key',
                    API_KEY); },
            METHOD: 'GET',
            contentType: "application/json",
            dataType: "json",
            data: rec,
            success: function (data) {
                console.log(data)
                try {
                    configData[configName] = JSON.parse(data.json_data)
                    console.log(configData)
                    console.log("jsme tu")
                    indConfig = configData["JS"].indConfig
                    console.log("after")
                    //console.log(JSON.stringify(indConfig, null,null, 2))

                    console.log("before CHART_SHOW_TEXT",CHART_SHOW_TEXT)
                    var CHART_SHOW_TEXT = configData["JS"].CHART_SHOW_TEXT
                    console.log("after CHART_SHOW_TEXT",CHART_SHOW_TEXT)
                }
                catch (error) {
                    window.alert(`Nešlo rozparsovat JSON_data string ${configName}`, error.message)
                }
                
            },
            error: function(xhr, status, error) {
                var err = eval("(" + xhr.responseText + ")");
                window.alert(`Nešlo dotáhnout config nastaveni z db ${configName}`, JSON.stringify(xhr));
                console.log(JSON.stringify(xhr));
            }
        });

    }

    const jsConfigName = "JS"
    //naloadovan config
    loadConfig(jsConfigName)

});
