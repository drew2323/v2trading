//docasne ulozeni aktivovanych buttonu pred reloadem
var activatedButtons = []
//seznam upravenych instant indikatoru a jejich konfigurace
// var addedInds = {}

function store_activated_buttons_state(extra) {
    activatedButtons = []
    if (extra) {
        activatedButtons.push(extra)
    }
    //ulozime si stav aktivovaných buttonků před změnou - mozna do sluzby
    $('#indicatorsButtons .switcher-active-item').each(function() {
      activatedButtons.push($(this).text());
      });
}

//JQUERY SECTION
$(document).ready(function () {

    //modal - delete indicator button
    $('#deleteIndicatorButton').click(function () {
        indname = $('#indicatorName').val()
        runner_id = $("#statusArchId").text()
        if (!runner_id) {
            alert("no arch runner selected")
            return
        }

        obj = new Object()
        obj.runner_id = runner_id
        // obj.toml = TOML.parse(ind_editor.getValue())
        obj.toml = ""
        obj.name = indname
        jsonString = JSON.stringify(obj);
        //console.log("pred odeslanim",jsonString)
        //cal rest api
        $.ajax({
            url:"/archived_runners/"+runner_id+"/previewindicator",
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-API-Key',
                    API_KEY); },
            method:"DELETE",
            contentType: "application/json",
            data: jsonString,
            success:function(data){
                window.$('#indicatorModal').modal('hide');
                //updatneme globalni promennou obsahujici vsechny arch data
                //TBD nebude fungovat az budu mit vic chartů otevřených - předělat
                //smazeme zaznam o indiaktoru v lokalni kopii ext_data (z nich se pak prekresli indikatory)
                if ((archData.ext_data !== null) && (archData.ext_data.instantindicators)) {
                    let index = archData.ext_data.instantindicators.findIndex(indicator => indicator.name === indname);
                    if (index !== -1) {
                        archData.ext_data.instantindicators.splice(index, 1);
                    }
                }
                
                if (archData.indicators[0][indname]) {
                    delete archData.indicators[0][indname]
                }
                else if (archData.indicators[1][indname]) {
                    delete archData.indicators[1][indname]
                }
                //delete addedInds[indname]
                //get active resolution
                const element = document.querySelector('.switcher-active-item');
                resolution = element.textContent
                //console.log("aktivni rozliseni", resolution)
                switch_to_interval(resolution, archData)
            },
            error: function(xhr, status, error) {
                var err = eval("(" + xhr.responseText + ")");
                window.alert(JSON.stringify(xhr));
                //console.log(JSON.stringify(xhr));
                //$('#button_runagain_arch').attr('disabled',false);
            }
        })
    });


    var myModalEl = document.getElementById('indicatorModal')
    myModalEl.addEventListener('hidden.bs.modal', function (event) {
        close_indicator_modal()
    })

    function close_indicator_modal() {
        index = $('#indicatorId').val()
        const elem = document.getElementById("IND"+index);
        if  (elem) {
            elem.classList.replace('switcher-item-highlighted', 'switcher-item');
        }
        //vracime pripadny schovany del button
        $('#deleteIndicatorButton').show();
        $('#saveIndicatorButton').show();
        window.$('#indicatorModal').modal('hide');
    }

    //HLAVNI SAVE akce INDICATOR MODAL - ulozi nebo vytvori novy
    $('#saveIndicatorButton').click(function () {
        indName = $('#indicatorName').val()
        if (!indName) {
            alert("name musi byt vyplneno")
            return
        }
        
        index = $('#indicatorId').val()
        var elem = document.getElementById("IND"+index);
        if (elem) {
            //pokud existuje - pak jde bud o edit nebo duplicate - podle jmena

            //jmeno je updatnute, jde o duplicate - vytvarime novy index
            if (elem.textContent !== $('#indicatorName').val()) {
                //alert("duplikujeme")
                index_ind++
                index = index_ind
            }
        }
        //pokud neexistuje, pak jde o novy index - pouzijeme tento

        runner_id = $("#statusArchId").text()
        if (!runner_id) {
            alert("no arch runner selected")
            return
        }

        // store_activated_buttons_state()
        // //pridame jeste tu aktualni, aby se zobrazila jako aktivni
        // activatedButtons.push(indName);
        console.log(activatedButtons)

        obj = new Object()
        //obj.runner_id = runner_id
        obj.name = indName
        obj.toml = ind_editor.getValue()
        jsonString = JSON.stringify(obj);
        //console.log("pred odeslanim",jsonString)
        //cal rest api
        $.ajax({
            url:"/archived_runners/"+runner_id+"/previewindicator",
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-API-Key',
                    API_KEY); },
            method:"PUT",
            contentType: "application/json",
            data: jsonString,
            success:function(data){
                //kod pro update/vytvoreni je zde stejny - updatujeme jen zdrojove dictionary
                window.$('#indicatorModal').modal('hide');
                console.log("navrat",data)
                //indName = $('#indicatorName').val()
                //updatneme/vytvorime klic v globalni promennou obsahujici vsechny arch data
                //TBD nebude fungovat az budu mit vic chartů otevřených - předělat
                if (data[0].length > 0) {
                    archData.indicators[0][indName] = data[0]
                } else if (data[1].length > 0) {
                    archData.indicators[1][indName] = data[1]
                }
                else {
                    alert("neco spatne s response ", data)
                }
                
                //pridame pripadne upatneme v ext_data

                //smazeme zaznam o indiaktoru v lokalni kopii ext_data (z nich se pak prekresli indikatory)
                if ((archData.ext_data !== null) && (archData.ext_data.instantindicators)) {
                    let index = archData.ext_data.instantindicators.findIndex(indicator => indicator.name === indName);
                    if (index !== -1) {
                        archData.ext_data.instantindicators.splice(index, 1);
                    }
                    archData.ext_data.instantindicators.push(obj)
                }
                //neexistuje instantindicators - vytvorime jej a vlozime prvni objekt
                else if ((archData.ext_data !== null) && (!archData.ext_data.instantindicators)) {
                    //a pridame tamtez novy zaznam
                    archData.ext_data["instantindicators"] =[obj]
                }                

                //glob promenna obsahujici aktualne pridane indikatory a jejich konfigurace
                //addedInds[indName] = obj.toml
                //get active resolution
                const element = document.querySelector('.switcher-active-item');
                resolution = element.textContent
                //console.log("aktivni rozliseni", resolution)
                //vykreslime  a pridavame jeste nazev indikatoru, ktery se ma vykreslit do aktivnich
                switch_to_interval(resolution, archData, indName)
            },
            error: function(xhr, status, error) {
                var err = eval("(" + xhr.responseText + ")");
                window.alert(JSON.stringify(xhr));
                //console.log(JSON.stringify(xhr));
                //$('#button_runagain_arch').attr('disabled',false);
            }
        })
    });

});