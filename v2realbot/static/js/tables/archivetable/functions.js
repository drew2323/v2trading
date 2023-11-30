//funkce a promenne specificke pro archiveTable
//usually work with archiveRecords

//ARCHIVE TABLES
let editor_diff_arch1
let editor_diff_arch2
var archData = null
var batchHeaders = []

function refresh_arch_and_callback(row, callback) {
    //console.log("entering refresh")
    var request = $.ajax({
        url: "/archived_runners/"+row.id,
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-API-Key',
            API_KEY); },
        method:"GET",
        contentType: "application/json",
        dataType: "json",
        success:function(data){   
            //console.log("fetched data ok")                      
            //console.log(JSON.stringify(data,null,2));
        },
        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            window.alert(JSON.stringify(xhr));
            console.log(JSON.stringify(xhr));
        }
    });

    // Handling the responses of both requests
    $.when(request).then(function(response) {
        // Both requests have completed successfully
        //console.log("Result from  request:", response);
        //console.log("Response received. calling callback")
        //call callback function
        callback(response)

    }, function(error) {
        // Handle errors from either request here
        // Example:
        console.error("Error from first request:", error);
        console.log("requesting id error")
    });
}

//triggers charting
function get_detail_and_chart(row) {
    $.ajax({
        url:"/archived_runners_detail/"+row.id,
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-API-Key',
            API_KEY); },
        method:"GET",
        contentType: "application/json",
        dataType: "json",
        success:function(data){							
            $('#button_show_arch').attr('disabled',false);
            $('#chartContainerInner').addClass("show");
            //$("#lines").html("<pre>"+JSON.stringify(row.stratvars,null,2)+"</pre>")
            
            //$('#chartArchive').append(JSON.stringify(data,null,2));
            //console.log(JSON.stringify(data,null,2));
            //if lower res is required call prepare_data otherwise call chart_archived_run()
            //get other base resolutions
            prepare_data(row, 1, "Min", data)
        },
        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            window.alert(JSON.stringify(xhr));
            //console.log(JSON.stringify(xhr));
            $('#button_show_arch').attr('disabled',false);
        }
    })
}

//rerun stratin
function run_day_again() {
    row = archiveRecords.row('.selected').data();
    $('#button_runagain_arch').attr('disabled',true);

    var record1 = new Object()
    //console.log(JSON.stringify(rows))

    //record1 = JSON.parse(rows[0].strat_json)
    //record1.json = rows[0].json

    //TBD mozna zkopirovat jen urcite?

    //getting required data (detail of the archived runner + stratin to be run)
    var request1 = $.ajax({
        url: "/archived_runners/"+row.id,
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-API-Key',
            API_KEY); },
        method:"GET",
        contentType: "application/json",
        dataType: "json",
        success:function(data){   
            //console.log("fetched data ok")                      
            //console.log(JSON.stringify(data,null,2));
        },
        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            window.alert(JSON.stringify(xhr));
            console.log(JSON.stringify(xhr));
        }
      });

      //nalaodovat data pro strategii
      var request2 = $.ajax({
        url: "/stratins/"+row.strat_id,
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-API-Key',
            API_KEY); },
        method:"GET",
        contentType: "application/json",
        dataType: "json",
        success:function(data){   
            //console.log("fetched data ok")                      
            //console.log(JSON.stringify(data,null,2));
        },
        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            window.alert(JSON.stringify(xhr));
            console.log(JSON.stringify(xhr));
        }
      });


    // Handling the responses of both requests
    $.when(request1, request2).then(function(response1, response2) {
        // Both requests have completed successfully
        var result1 = response1[0];
        var result2 = response2[0];

        //console.log("Result from first request:", result1);
        //console.log("Result from second request:", result2);

        //console.log("calling compare")
        rerun_strategy(result1, result2)
        // Perform your action with the results from both requests
        // Example:

    }, function(error1, error2) {
        // Handle errors from either request here
        // Example:
        console.error("Error from first request:", error1);
        console.error("Error from second request:", error2);
    });


    function rerun_strategy(archRunner, stratData) {
        record1 = archRunner
        //console.log(record1)

        //smazeneme nepotrebne a pridame potrebne
        //do budoucna predelat na vytvoreni noveho objektu
        //nebudeme muset odstanovat pri kazdem pridani noveho atributu v budoucnu
        delete record1["end_positions"];
        delete record1["end_positions_avgp"];
        delete record1["profit"];
        delete record1["trade_count"];
        delete record1["stratvars_toml"];
        delete record1["started"];
        delete record1["stopped"];
        delete record1["metrics"];
        delete record1["settings"];
        delete record1["stratvars"];

        record1.note = "RERUN " + record1.note

        if (record1.bt_from == "") {delete record1["bt_from"];}
        if (record1.bt_to == "") {delete record1["bt_to"];}
    
        //mazeme, pouze rerunujeme single
        delete record1["test_batch_id"];
        delete record1["batch_id"];

        const rec = new Object()
        rec.id2 = parseInt(stratData.id2);
        rec.name = stratData.name;
        rec.symbol = stratData.symbol;
        rec.class_name = stratData.class_name;
        rec.script = stratData.script;
        rec.open_rush = stratData.open_rush;
        rec.close_rush = stratData.close_rush;
        rec.stratvars_conf = stratData.stratvars_conf;
        rec.add_data_conf = stratData.add_data_conf;
        rec.note = stratData.note;
        rec.history = "";
        strat_json = JSON.stringify(rec, null, 2);
        record1.strat_json = strat_json
        
        //zkopirujeme strat_id do id a smazeme strat_id
        record1.id = record1.strat_id
        delete record1["strat_id"];

        //console.log("record1 pred odeslanim", record1)
        jsonString = JSON.stringify(record1);

        $.ajax({
            url:"/stratins/"+record1.id+"/run",
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-API-Key',
                    API_KEY); },
            method:"PUT",
            contentType: "application/json",
            data: jsonString,
            success:function(data){							
                $('#button_runagain_arch').attr('disabled',false);
                setTimeout(function () {
                    runnerRecords.ajax.reload();
                    stratinRecords.ajax.reload();
                }, 1500);
            },
            error: function(xhr, status, error) {
                var err = eval("(" + xhr.responseText + ")");
                window.alert(JSON.stringify(xhr));
                //console.log(JSON.stringify(xhr));
                $('#button_runagain_arch').attr('disabled',false);
            }
        })
    }

}


function expand_collapse_rows(event) {
    event.stopPropagation()
    var headerRow = $(this);
    var name = headerRow.data('name');
    var collapsed = headerRow.hasClass('collapsed');

    // Toggle the expand icon name
    var expandIcon = headerRow.find('.expand-icon');
    if (collapsed) {
        expandIcon.text('expand_less');
    } else {
        expandIcon.text('expand_more');
    }

    headerRow.toggleClass('collapsed');

    archiveRecords.rows().every(function () {
        var row = $(this.node());
        var rowGroup = row.attr('data-group-name');
        if (rowGroup == name) {
            row.toggle();
        }
    });

    // Save the state
    if (collapsed) {
        localStorage.setItem('dt-group-state-' + name, 'expanded');
    } else {
        localStorage.setItem('dt-group-state-' + name, 'collapsed');
    }
    }

function delete_batch(event){
    event.preventDefault();
    batch_id = $('#batch_id_del').val();
    $('#deletebatch').attr('disabled', 'disabled');
    $.ajax({
        url:"/archived_runners/batch/"+batch_id,
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-API-Key',
                API_KEY); },
        method:"DELETE",
        contentType: "application/json",
        dataType: "json",
        data: JSON.stringify(batch_id),
        success:function(data){				
            $('#delFormBatch')[0].reset();
            window.$('#delModalBatch').modal('hide');
            $('#deletebatch').attr('disabled', false);				
            $('#button_delete_batch').attr('disabled', false);
            //console.log(data)
            archiveRecords.ajax.reload();
            disable_arch_buttons();
        },
        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            window.alert(JSON.stringify(xhr));
            console.log(JSON.stringify(xhr));
            $('#deletebatch').attr('disabled', false);
            $('#button_delete_batch').attr('disabled', false);
            archiveRecords.ajax.reload();
            disable_arch_buttons();
        }
    })
}


function analyze_optimal_cutoff(batch_id = null) {
    //definice parametru
    param_obj = { rem_outliers:false, steps:50}
    obj = {function: "analyze_optimal_cutoff", runner_ids:[], batch_id:null, params:param_obj}
    //bereme bud selected runners
    if (!batch_id) {
        rows = archiveRecords.rows('.selected').data();
        if (rows == undefined) {
            return
        }
        $('#button_analyze').attr('disabled','disabled');
        // Extract IDs from each row's data and store them in an array
        obj.runner_ids = [];
        for (var i = 0; i < rows.length; i++) {
            obj.runner_ids.push(rows[i].id); // Assuming 'id' is the property that contains the row ID
        }
    }
    //nebo batch
    else {
        obj.batch_id = batch_id

    }
    console.log("analyze cutoff objekt", obj)
    // batch_id: Optional[str] = None
    // runner_ids: Optional[List[UUID]] = None
    // #additional parameter
    // params: Optional[dict] = None    

    $.ajax({
        url:"/batches/optimizecutoff/",
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-API-Key',
                API_KEY); },
        method:"POST",
        xhrFields: {
            responseType: 'blob'
        },
        xhr: function() {
            var xhr = new XMLHttpRequest();
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 2) { // Headers have been received
                    if (xhr.status === 200) {
                        xhr.responseType = "blob"; // Set responseType to 'blob' for successful image responses
                    } else {
                        xhr.responseType = "text"; // Set responseType to 'text' for error messages
                    }
                }
            };
            return xhr;
        },
        contentType: "application/json",
        processData: false,
        data: JSON.stringify(obj),
        success:function(blob){		
            var url = window.URL || window.webkitURL;
            console.log("vraceny obraz", blob)
            console.log("url",url.createObjectURL(blob))
            display_image(url.createObjectURL(blob))
            if (!batch_id) {
                $('#button_analyze').attr('disabled',false);
            }
        },
        error: function(xhr, status, error) {
            console.log("proc to skace do erroru?")
            window.alert(JSON.stringify(xhr));
            console.log(JSON.stringify(xhr));
            $('#button_analyze').attr('disabled',false);
            if (!batch_id) {
                $('#button_analyze').attr('disabled',false);
            }             
        }
    })
}

//pomocna funkce, ktera vraci filtrovane radky tabulky (bud oznacene nebo batchove)
function get_selected_or_batch(batch_id = null) {
    if (!batch_id) {
        rows = archiveRecords.rows('.selected');
    } else {
        rows = archiveRecords.rows( function ( idx, data, node ) {
            return data.batch_id == batch_id;
        });
        //console.log("batch rows",batch_id, rows)
    }
    return rows
}

//prepares export data, either for selected rows or based on batch_id
function prepare_export(batch_id = null) {
    rows = get_selected_or_batch(batch_id)
    var trdList = []
    if(rows.data().length > 0 ) {
        //console.log(rows.data())
        // Loop through the selected rows and display an alert with each row's ID
        rows.every(function (rowIdx, tableLoop, rowLoop ) {
            var data = this.data()
            data.metrics.prescr_trades.forEach((trade) => {
                new_obj = {}
                new_obj["entry_time"] = (trade.entry_time) ? new Date(trade.entry_time * 1000) : null
                new_obj["entry_time"] = (new_obj["entry_time"]) ? new_obj["entry_time"].toLocaleString('cs-CZ', {
                    timeZone: 'America/New_York',
                  }) : null
                new_obj["exit_time"] = (trade.exit_time) ? new Date(trade.exit_time * 1000):null
                new_obj["exit_time"] = (new_obj["exit_time"]) ? new_obj["exit_time"].toLocaleString('cs-CZ', {
                    timeZone: 'America/New_York',
                  }) : null
                new_obj["direction"] = trade.direction
                new_obj["profit"] = trade.profit
                new_obj["rel_profit"] = trade.rel_profit
                trdList.push(new_obj)
            })
        });
    }
    return trdList
}

function download_exported_data(type, batch_id = null) {
    filename = batch_id ? "batch"+batch_id+"-trades" : "trades"
    if (type == "xml") {
        response_type = "application/xml"
        output = convertToXml(prepare_export(batch_id))
        }
    else {
        response_type = "text/csv"
        output = convertToCsv(prepare_export(batch_id))
    }
    console.log(output)
    downloadFile(response_type,type, filename, output)
}

function display_image(imageUrl) {
    // Attempt to load the image
    var img = new Image();
    img.src = imageUrl;
    img.onload = function() {
        // If the image loads successfully, display it
        $('#previewImg').attr('src', imageUrl);
        //$('#imagePreview').show();
        window.$('#imageModal').modal('show');        
    };
    img.onerror = function(e) {
        console.log("Image load error", e);
        console.log("Image object:", img);
        console.log("no image available")
        // If the image fails to load, do nothing
    };
}

function display_batch_report(batch_id) {
    //var imageUrl = '/media/report_'+data.id+".png"; // Replace with your logic to get image URL
    var imageUrl = '/media/basic/'+batch_id+'.png'; // Replace with your logic to get image URL
    //console.log(imageUrl)
    display_image(imageUrl)
}

function refresh_logfile() {
    $.ajax({
        url:"/log?lines=30",
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-API-Key',
            API_KEY); },
        method:"GET",
        contentType: "application/json",
        dataType: "json",
        success:function(response){
            if (response.lines.length == 0) {
                $('#log-content').html("no records");
            }
            else {
                $('#log-content').html(response.lines.join('\n'));	
            }	
        },
        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            window.alert(JSON.stringify(xhr));
        }
    })        
}

function delete_arch_rows(ids) {
    $.ajax({
        url:"/archived_runners/",
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-API-Key',
                API_KEY); },
        method:"DELETE",
        contentType: "application/json",
        dataType: "json",
        data: JSON.stringify(ids),
        success:function(data){				
            $('#delFormArchive')[0].reset();
            window.$('#delModalArchive').modal('hide');				
            $('#deletearchive').attr('disabled', false);
            //console.log(data)
            archiveRecords.ajax.reload();
            disable_arch_buttons()
        },
        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            window.alert(JSON.stringify(xhr));
            console.log(JSON.stringify(xhr));
            $('#deletearchive').attr('disabled', false);
            //archiveRecords.ajax.reload();
        }
    })
}

function extractNumbersFromString(str) {
    // Regular expression to match the pattern #number1/number2
    const pattern = /#(\d+)\/(\d+)/;
    const match = str.match(pattern);

    if (match) {
        // Extract number1 and number2 from the match
        const number1 = parseInt(match[1], 10);
        const number2 = parseInt(match[2], 10);

        //return { number1, number2 };
        return number2;
    } else {
        return null;
    }
}

// Function to generate a unique key for localStorage based on batch_id
function generateStorageKey(batchId) {
    return 'dt-group-state-' + batchId;
}


function disable_arch_buttons() {
    //disable buttons (enable on row selection)
    $('#button_runagain_arch').attr('disabled','disabled');
    $('#button_show_arch').attr('disabled','disabled');
    $('#button_delete_arch').attr('disabled','disabled');
    $('#button_delete_batch').attr('disabled','disabled');
    $('#button_analyze').attr('disabled','disabled');
    $('#button_edit_arch').attr('disabled','disabled');
    $('#button_compare_arch').attr('disabled','disabled');
    $('#button_report').attr('disabled','disabled');
    $('#button_export_xml').attr('disabled','disabled');   
    $('#button_export_csv').attr('disabled','disabled');   
}

function enable_arch_buttons() {
    $('#button_analyze').attr('disabled',false);
    $('#button_show_arch').attr('disabled',false);
    $('#button_runagain_arch').attr('disabled',false);
    $('#button_delete_arch').attr('disabled',false);
    $('#button_delete_batch').attr('disabled',false);
    $('#button_edit_arch').attr('disabled',false);
    $('#button_compare_arch').attr('disabled',false);
    $('#button_report').attr('disabled',false);
    $('#button_export_xml').attr('disabled',false);
    $('#button_export_csv').attr('disabled',false);
}