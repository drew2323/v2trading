//on button
function store_api_key(event) {
    key = document.getElementById("api-key").value;
    localStorage.setItem("api-key", key);
    API_KEY = key;
}

function get_status(id) {
    var status = ""
    runnerRecords.rows().iterator('row', function ( context, index ) {
        var data = this.row(index).data();
        //window.alert(JSON.stringify(data))
        if (data.strat_id == id) {
            //window.alert("found");
            if ((data.run_mode) == "backtest") { status_detail = '<span>'+data.run_mode+'</span>'}
            else { status_detail = data.run_mode + " | " + data.run_account}
            if (data.run_paused == null) {
                status = '<span class="material-symbols-outlined">play_circle</span>'+status_detail
            }
            else {
                status = '<span class="material-symbols-outlined">pause_circle</span>'+ status_detail
            }}
            //window.alert("found") }
    });
    return status
}

function is_stratin_running(id) {
    var running = false
    runnerRecords.rows().iterator('row', function ( context, index ) {
        var data = this.row(index).data();
        //window.alert(JSON.stringify(data))
        if (data.strat_id == id) {
            running = true    
        }
            //window.alert("found") }
    });
    return running
}


//STRATIN and RUNNERS TABELS
$(document).ready(function () {
    stratinRecords.ajax.reload();
    runnerRecords.ajax.reload();

    $('#trade-timestamp').val(localStorage.getItem("trade_timestamp"));
    $('#trade-count').val(localStorage.getItem("trade_count"));
    $('#trade-symbol').val(localStorage.getItem("trade_symbol"));
    $('#trade-minsize').val(localStorage.getItem("trade_minsize"));
    $('#trade-filter').val(localStorage.getItem("trade_filter"));


    //disable buttons (enable on row selection)
    $('#button_pause').attr('disabled','disabled');
    $('#button_stop').attr('disabled','disabled');
    $('#button_connect').attr('disabled','disabled');
    $('#button_edit').attr('disabled','disabled');
    $('#button_dup').attr('disabled','disabled');
    $('#button_copy').attr('disabled','disabled');
    $('#button_delete').attr('disabled','disabled');
    $('#button_run').attr('disabled','disabled');

    //selectable rows in stratin table
    $('#stratinTable tbody').on('click', 'tr', function () {
        if ($(this).hasClass('selected')) {
            //$(this).removeClass('selected');
            $('#button_dup').attr('disabled','disabled');
            $('#button_copy').attr('disabled','disabled');
            $('#button_edit').attr('disabled','disabled');
            $('#button_delete').attr('disabled','disabled');
            $('#button_run').attr('disabled','disabled');
        } else {
            //stratinRecords.$('tr.selected').removeClass('selected');
            $(this).addClass('selected');
            $('#button_dup').attr('disabled',false);
            $('#button_copy').attr('disabled',false);
            $('#button_edit').attr('disabled',false);
            $('#button_delete').attr('disabled',false);
            $('#button_run').attr('disabled',false);
        }
    });

    //selectable rows runners Table
    $('#runnerTable tbody').on('click', 'tr', function () {
        if ($(this).hasClass('selected')) {
            $(this).removeClass('selected');
            $('#button_pause').attr('disabled', 'disabled');
            $('#button_stop').attr('disabled', 'disabled');
            $('#button_connect').attr('disabled', 'disabled');
        } else {
            stratinRecords.$('tr.selected').removeClass('selected');
            $(this).addClass('selected');
            $('#button_pause').attr('disabled', false);
            $('#button_stop').attr('disabled', false);
            $('#button_connect').attr('disabled', false);
        }
    });


   //button get historical trades
   $('#bt-trade').click(function () {
    event.preventDefault();
    $('#bt-trade').attr('disabled','disabled');
    $( "#trades-data").addClass("in");

    localStorage.setItem("trade_timestamp",$('#trade-timestamp').val());
    localStorage.setItem("trade_count",$('#trade-count').val());
    localStorage.setItem("trade_symbol",$('#trade-symbol').val());
    localStorage.setItem("trade_minsize",$('#trade-minsize').val());
    localStorage.setItem("trade_filter",$('#trade-filter').val());

    const rec = new Object()
    rec.timestamp_from = parseFloat($('#trade-timestamp').val())-parseInt($('#trade-count').val())
    rec.timestamp_to = parseFloat($('#trade-timestamp').val())+parseInt($('#trade-count').val())
    symbol = $('#trade-symbol').val()
    //jsonString = JSON.stringify(rec);
    //alert(JSON.stringify(rec))
    $.ajax({
        url:"/tradehistory/"+symbol+"/",
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-API-Key',
            API_KEY); },
        method:"GET",
        contentType: "application/json",
        dataType: "json",
        data: rec,
        success:function(data){							
            $('#bt-trade').attr('disabled', false);
            $('#trades-data').show();
            //$('#trades-data').text("")
            var minsize = parseInt($('#trade-minsize').val());
            //filter string to filter array
            var valueInserted = $("#trade-filter").val(); // "tag1,tag2,tag3, "two words""
            var filterList = valueInserted.split(",");  // ["tag1", "tag2", "tag3", "two words"]
            for (var i in filterList) {
                filterList[i] = filterList[i].trim();
            }

            console.log("filter list")
            console.log(filterList)
            console.log(minsize)
            var row = ""
            //zakrouhleno na milisekundy
            var puvodni = parseFloat(parseInt(parseFloat($('#trade-timestamp').val())*1000))/1000
            console.log(puvodni)
            $('#trades-data-table').html(row);
            data.forEach((tradeLine) => {
                //console.log(JSON.stringify(tradeLine))
                date = new Date(tradeLine.timestamp)
                timestamp = date.getTime()/1000
                console.log(timestamp)

                //trade contains filtered condition or size<minsize
                bg = (findCommonElements3(filterList, tradeLine.conditions) || (parseInt(tradeLine.size) < minsize) ? 'style="background-color: #411e1e;"' : '')

                row += '<tr role="row" '+ ((timestamp == puvodni) ? 'class="highlighted"' : '') +' ' + bg + '><td>' + timestamp + '</td><td>' + tradeLine.price + '</td>' +
                            '<td class="dt-center">' + tradeLine.size + '</td><td>' + tradeLine.id + '</td>' +
                            '<td>' + tradeLine.conditions + '</td><td>' + tradeLine.tape + '</td>' +
                            '<td>' + tradeLine.timestamp + '</td></tr>';
            
            });
            //console.log(row);
            $('#trades-data-table').html(row);
            // $('#trades-data').html(row)
        },
        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            window.alert(JSON.stringify(xhr));
            console.log(JSON.stringify(xhr));
            $('#bt-trade').attr('disabled', false);
        }
    })
});

    //on hover of each logline move timestamp to trade history input field
    //   $('.line').click(function () {
    //     timestamp = $(this).data("timestamp");
    //     console.log(timestamp);
    //     $('#trade-timestamp').val(timestamp);
    // })


    //button refresh
    $('.refresh').click(function () {
        runnerRecords.ajax.reload();
        stratinRecords.ajax.reload();
        archiveRecords.ajax.reload();
    })

    //button copy
    $('#button_copy').click(function () {
        event.preventDefault();
        $('#button_copy').attr('disabled','disabled');
        row = stratinRecords.row('.selected').data();
        const rec = new Object()
        rec.id2 = parseInt(row.id2);
        rec.name = row.name;
        rec.symbol = row.symbol;
        rec.class_name = row.class_name;
        rec.script = row.script;
        rec.open_rush = row.open_rush;
        rec.close_rush = row.close_rush;
        rec.stratvars_conf = row.stratvars_conf;
        rec.add_data_conf = row.add_data_conf;
        rec.note = row.note;
        rec.history = "";
        jsonString = JSON.stringify(rec, null, 2);
        navigator.clipboard.writeText(jsonString);
        $('#button_copy').attr('disabled', false);
    })

   //button duplicate
   $('#button_dup').click(function () {
    row = stratinRecords.row('.selected').data();
    event.preventDefault();
    $('#button_dup').attr('disabled','disabled');
    const rec = new Object()
    rec.id2 = parseInt(row.id2) + 1;
    rec.name = row.name + " copy";
    rec.symbol = row.symbol;
    rec.class_name = row.class_name;
    rec.script = row.script;
    rec.open_rush = row.open_rush;
    rec.close_rush = row.close_rush;
    rec.stratvars_conf = row.stratvars_conf;
    rec.add_data_conf = row.add_data_conf;
    rec.note = row.note;
    rec.history = "";
    jsonString = JSON.stringify(rec);
    $.ajax({
        url:"/stratins/",
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-API-Key',
            API_KEY); },
        method:"POST",
        contentType: "application/json",
        dataType: "json",
        data: jsonString,
        success:function(data){							
            $('#button_dup').attr('disabled', false);
            stratinRecords.ajax.reload();
        },
        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            window.alert(JSON.stringify(xhr));
            console.log(JSON.stringify(xhr));
            $('#button_dup').attr('disabled', false);
        }
    })
});

    //button pause
    $('#button_pause').click(function () {
        row = runnerRecords.row('.selected').data();
        event.preventDefault();
        $('#button_pause').attr('disabled','disabled');
        $.ajax({
            url:"/runners/"+row.id+"/pause",
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-API-Key',
                API_KEY); },
            method:"PUT",
            contentType: "application/json",
            dataType: "json",
            success:function(data){							
                $('#button_pause').attr('disabled', false);
                runnerRecords.ajax.reload();
                stratinRecords.ajax.reload();
            },
            error: function(xhr, status, error) {
                var err = eval("(" + xhr.responseText + ")");
                window.alert(JSON.stringify(xhr));
                console.log(JSON.stringify(xhr));
                $('#button_pause').attr('disabled', false);
            }
        })
    });

    //button compare stratin
    $('#button_compare').click(function () {
        window.$('#diffModal').modal('show');
        rows = stratinRecords.rows('.selected').data();
        const rec1 = new Object()
        rec1.id = rows[0].id;
        rec1.id2 = parseInt(rows[0].id2);
        rec1.name = rows[0].name;
        rec1.symbol = rows[0].symbol;
        rec1.class_name = rows[0].class_name;
        rec1.script = rows[0].script;
        rec1.open_rush = rows[0].open_rush;
        rec1.close_rush = rows[0].close_rush;
        rec1.stratvars_conf = TOML.parse(rows[0].stratvars_conf);
        rec1.add_data_conf = TOML.parse(rows[0].add_data_conf);
        rec1.note = rows[0].note;
        rec1.history = "";
       //jsonString1 = JSON.stringify(rec1, null, 2);

        const rec2 = new Object()
        rec2.id = rows[1].id;
        rec2.id2 = parseInt(rows[1].id2);
        rec2.name = rows[1].name;
        rec2.symbol = rows[1].symbol;
        rec2.class_name = rows[1].class_name;
        rec2.script = rows[1].script;
        rec2.open_rush = rows[1].open_rush;
        rec2.close_rush = rows[1].close_rush;
        rec2.stratvars_conf = TOML.parse(rows[1].stratvars_conf);
        rec2.add_data_conf = TOML.parse(rows[1].add_data_conf);
        rec2.note = rows[1].note;
        rec2.history = "";
        //jsonString2 = JSON.stringify(rec2, null, 2);


        //document.getElementById('first').innerHTML = '<pre>'+JSON.stringify(rec1, null, 2)+'</pre>'
       $('#diff_first').text(rec1.name);
       $('#diff_second').text(rec2.name);

       var delta = compareObjects(rec1, rec2)
       const htmlMarkup2 = `<pre>{\n${generateHTML(rec2, delta)}}\n</pre>`;
       document.getElementById('second').innerHTML = htmlMarkup2;

       //var delta1 = compareObjects(rec2, rec1)
       const htmlMarkup1 = `<pre>{\n${generateHTML(rec1, delta)}}\n</pre>`;
       document.getElementById('first').innerHTML = htmlMarkup1;

        event.preventDefault();
        //$('#button_compare').attr('disabled','disabled');
    });

    //button connect
    $('#button_connect').click(function () {
        row = runnerRecords.row('.selected').data();
        event.preventDefault();
        $('#button_connect').attr('disabled','disabled');
        $('#runnerId').val(row.id);
        disconnect(event)
        connect(event)
        // $( "#bt-conn" ).trigger( "click" );
        $('#button_connect').attr('disabled',false);
    });

    //button stop
    $('#button_stop').click(function () {
        row = runnerRecords.row('.selected').data();
        event.preventDefault();
        $('#button_stop').attr('disabled','disabled');
        $.ajax({
            url:"/runners/"+row.id+"/stop",
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-API-Key',
                    API_KEY); },
            method:"PUT",
            contentType: "application/json",
            dataType: "json",
            success:function(data){							
                $('#button_stop').attr('disabled', false);
                setTimeout(function () {
                    runnerRecords.ajax.reload();
                    stratinRecords.ajax.reload();
                  }, 2300)
            },
            error: function(xhr, status, error) {
                var err = eval("(" + xhr.responseText + ")");
                window.alert(JSON.stringify(xhr));
                console.log(JSON.stringify(xhr));
                $('#button_stop').attr('disabled', false);
            }
        })
    });

    //button stop all
    $('#button_stopall').click(function () {
        event.preventDefault();
        $('#buttonall_stop').attr('disabled','disabled');
        $.ajax({
            url:"/runners/stop",
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-API-Key',
                    API_KEY); },
            method:"PUT",
            contentType: "application/json",
            dataType: "json",
            success:function(data){							
                $('#button_stopall').attr('disabled', false);
                setTimeout(function () {
                    runnerRecords.ajax.reload();
                    stratinRecords.ajax.reload();
                  }, 2300)
            },
            error: function(xhr, status, error) {
                var err = eval("(" + xhr.responseText + ")");
                window.alert(JSON.stringify(xhr));
                console.log(JSON.stringify(xhr));
                $('#button_stopall').attr('disabled', false);
            }
        })
    });


    //button run
    $('#button_run').click(function () {
        row = stratinRecords.row('.selected').data();
        window.$('#runModal').modal('show');
        $('#bt_from').val(localStorage.getItem("bt_from"));
        //console.log(localStorage.getItem("bt_from"))
        $('#bt_to').val(localStorage.getItem("bt_to"));
        //console.log(localStorage.getItem("bt_to"))
        $('#test_batch_id').val(localStorage.getItem("test_batch_id"));
        $('#mode').val(localStorage.getItem("mode"));
        $('#account').val(localStorage.getItem("account"));
        $('#debug').val(localStorage.getItem("debug"));
        $('#ilog_save').val(localStorage.getItem("ilog_save"));
        $('#runid').val(row.id);

        // Initially, check the value of "batch" and enable/disable "from" and "to" accordingly
        if ($("#test_batch_id").val() !== "") {
            $("#bt_from, #bt_to").prop("disabled", true);
        } else {
            $("#bt_from, #bt_to").prop("disabled", false);
        }

        // Listen for changes in the "batch" input
        $("#test_batch_id").on("input", function() {
            if ($(this).val() !== "") {
                // If "batch" is not empty, disable "from" and "to"
                $("#bt_from, #bt_to").prop("disabled", true);
            } else {
                // If "batch" is empty, enable "from" and "to"
                $("#bt_from, #bt_to").prop("disabled", false);
            }
        });


    });

    //button add
    $('#button_add').click(function () {
        window.$('#recordModal').modal('show');
        $('#recordForm')[0].reset();
		$('.modal-title').html("<i class='fa fa-plus'></i> Add Record");
		$('#action').val('addRecord');
		$('#save').val('Add');
    });

    //edit button
    $('#button_edit').click(function () {
        row = stratinRecords.row('.selected').data();
        window.$('#recordModal').modal('show');
        $('#id').val(row.id);
        $('#id2').val(row.id2);
        $('#name').val(row.name);
        $('#symbol').val(row.symbol);
        $('#class_name').val(row.class_name);				
        $('#script').val(row.script);
        $('#open_rush').val(row.open_rush);
        $('#close_rush').val(row.close_rush);
        $('#stratvars_conf').val(row.stratvars_conf);
        $('#add_data_conf').val(row.add_data_conf);
        $('#note').val(row.note);
        $('#history').val(row.history);
        $('.modal-title').html(" Edit Records");
        $('#action').val('updateRecord');
        $('#save').val('Save');
    //code for toml editor
  // Initialize Monaco Editor

        // require.config({ paths: { vs: 'monaco-editor/min/vs' } });
        // require(['vs/editor/editor.main'], function () {
        //     var editor = $("#editor").monacoEditor({
        //         language: "toml",
        //         value: row.stratvars_conf
        //         });   
        //     // Get content from Monaco Editor and set it to the textarea using jQuery
        //     editor.getModels()[0].onDidChangeContent(function() {
        //         var tomlContent = monaco.editor.getModels()[0].getValue();
        //         $('#stratvars_conf').val(tomlContent);
        //     });
        // }); 


    });
    //delete button
    $('#button_delete').click(function () {
        row = stratinRecords.row('.selected').data();
        window.$('#delModal').modal('show');
        $('#delid').val(row.id);
        $('#action').val('delRecord');
        $('#save').val('Delete');

    });
    //json add button
    $('#button_add_json').click(function () {
        window.$('#jsonModal').modal('show');
    });
} );


//stratin table
var stratinRecords = 
    $('#stratinTable').DataTable( {
        ajax: { 
            url: '/stratins/',
            dataSrc: '',
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-API-Key',
                    API_KEY); },
            error: function(xhr, status, error) {
                //var err = eval("(" + xhr.responseText + ")");
                //window.alert(JSON.stringify(xhr));
                console.log(JSON.stringify(xhr));
            }
            },
        columns: [{ data: 'id' },
                    {data: 'id2'},
                    {data: 'name'},
                    {data: 'symbol'},
                    {data: 'class_name', visible: false},
                    {data: 'script', visible: true},
                    {data: 'open_rush', visible: false},
                    {data: 'close_rush', visible: false},
                    {data: 'stratvars_conf', visible: false},
                    {data: 'add_data_conf', visible: false},
                    {data: 'note'},
                    {data: 'history', visible: false},
                    {data: 'id', visible: true},
                ],
        paging: true,
        processing: false,
        columnDefs: [{
            targets: 12,
            render: function ( data, type, row ) {
                var status = get_status(data)
                return status
            },
            },
            {
                targets: 0,
                render: function ( data, type, row ) {
                    return '<div class="tdnowrap" data-bs-toggle="tooltip" data-bs-placement="top" title="'+data+'">'+data+'</i>'
                },
                },
            ],
        order: [[1, 'asc']],
        select: {
            style: 'multi',
            selector: 'td'
        },
        // createdRow: function( row, data, dataIndex){
        //     if (is_running(data.id) ){
        //         alert("runner");
        //         $(row).addClass('highlight');
        //     }
        //}
        } );

//runner table
var runnerRecords = 
    $('#runnerTable').DataTable( {
        ajax: { 
            url: '/runners/',
            dataSrc: '',
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-API-Key',
                    API_KEY); },
            error: function(xhr, status, error) {
                //var err = eval("(" + xhr.responseText + ")");
                //window.alert(JSON.stringify(xhr));
                console.log(JSON.stringify(xhr));
            },
            // success:function(data){							
            //     if ( ! runnerRecords.data().count() ) {
            //         $('#button_stopall').attr('disabled', 'disabled');
            //     }
            //     else {
            //         $('#button_stopall').attr('disabled', false);
            //     }
            // },
            },
        columns: [{ data: 'id' },
                    {data: 'strat_id'},
                    {data: 'run_started'},
                    {data: 'run_mode'},
                    {data: 'run_symbol'},
                    {data: 'run_account'},
                    {data: 'run_ilog_save'},
                    {data: 'run_paused'},
                    {data: 'run_profit'},
                    {data: 'run_trade_count'},
                    {data: 'run_positions'},
                    {data: 'run_avgp'},
                ],
        paging: false,
        processing: false,
        columnDefs: [            {
            targets: [0,1],
            render: function ( data, type, row ) {
                return '<div class="tdnowrap" title="'+data+'">'+data+'</i>'
            },
            },
            {
                targets: [2],
                render: function ( data, type, row ) {
                    return format_date(data)
                },
                },
        ],
        // select: {
        //     style: 'multi'
        // },
        } );

//modal na run
$("#runModal").on('submit','#runForm', function(event){
    localStorage.setItem("bt_from", $('#bt_from').val());
    localStorage.setItem("bt_to", $('#bt_to').val());
    localStorage.setItem("test_batch_id", $('#test_batch_id').val());
    localStorage.setItem("mode", $('#mode').val());
    localStorage.setItem("account", $('#account').val());
    localStorage.setItem("debug", $('#debug').val());
    localStorage.setItem("ilog_save", $('#ilog_save').val());
    event.preventDefault();
    $('#run').attr('disabled','disabled');
    
    var formData = $(this).serializeJSON();
    //rename runid to id
    Object.defineProperty(formData, "id", Object.getOwnPropertyDescriptor(formData, "runid"));
    delete formData["runid"];
    console.log(formData)
    if ($('#ilog_save').prop('checked')) {
        formData.ilog_save = true;
    }
    else 
    {
        formData.ilog_save = false;
    }
    // $('#subscribe').prop('checked')
    if (formData.bt_from == "") {delete formData["bt_from"];}
    if (formData.bt_to == "") {delete formData["bt_to"];}

    if (formData.test_batch_id == "") {delete formData["test_batch_id"];}

    //create strat_json - snapshot of stratin
    row = stratinRecords.row('.selected').data();
    const rec = new Object()
    rec.id2 = parseInt(row.id2);
    rec.name = row.name;
    rec.symbol = row.symbol;
    rec.class_name = row.class_name;
    rec.script = row.script;
    rec.open_rush = row.open_rush;
    rec.close_rush = row.close_rush;
    rec.stratvars_conf = row.stratvars_conf;
    rec.add_data_conf = row.add_data_conf;
    rec.note = row.note;
    rec.history = "";
    strat_json = JSON.stringify(rec, null, 2);
    formData.strat_json = strat_json

    jsonString = JSON.stringify(formData);
    //console.log(jsonString)
    //window.alert(jsonString);
    $.ajax({
        url:"/stratins/"+formData.id+"/run",
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-API-Key',
                API_KEY); },
        method:"PUT",
        contentType: "application/json",
        data: jsonString,
        success:function(data){
            //pokud mame subscribnuto na RT                
            if ($('#subscribe').prop('checked')) {
                //subscribe input value gets id of current runner
                //$('#runid').val()
                //data obsuje ID runneru - na ten se subscribneme
                console.log("vysledek z run:", data)
                $('#runnerId').val(data);
                $( "#bt-conn" ).trigger( "click" );
            }				
            $('#runForm')[0].reset();
            window.$('#runModal').modal('hide');				
            $('#run').attr('disabled', false);
            setTimeout(function () {
                runnerRecords.ajax.reload();
                stratinRecords.ajax.reload();
              }, 1500);
        },
        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            window.alert(JSON.stringify(xhr));
            console.log(JSON.stringify(xhr));
            $('#run').attr('disabled', false);
        }

    })
});


//modal na add/edit
$("#recordModal").on('submit','#recordForm', function(event){
    if ($('#save').val() == "Add") {
        //code for add
        event.preventDefault();
        $('#save').attr('disabled','disabled');
        var formData = $(this).serializeJSON();
        jsonString = JSON.stringify(formData);
        $.ajax({
            url:"/stratins/",
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-API-Key',
                    API_KEY); },
            method:"POST",
            contentType: "application/json",
            dataType: "json",
            data: jsonString,
            success:function(data){				
                $('#recordForm')[0].reset();
                window.$('#recordModal').modal('hide');				
                $('#save').attr('disabled', false);
                setTimeout(function () {
                    runnerRecords.ajax.reload();
                    stratinRecords.ajax.reload();
                  }, 750)
            },
            error: function(xhr, status, error) {
                var err = eval("(" + xhr.responseText + ")");
                window.alert(JSON.stringify(xhr));
                console.log(JSON.stringify(xhr));
                $('#save').attr('disabled', false);
            }

        })
    }
    else {
        //code for edit
        event.preventDefault();
        $('#save').attr('disabled','disabled');
        var formData = $(this).serializeJSON();
        jsonString = JSON.stringify(formData);
        $.ajax({
            url:"/stratins/"+formData.id,
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-API-Key',
                    API_KEY); },
            method:"PATCH",
            contentType: "application/json",
            dataType: "json",
            data: jsonString,
            success:function(data){				
                $('#recordForm')[0].reset();
                window.$('#recordModal').modal('hide');				
                $('#save').attr('disabled', false);
                stratinRecords.ajax.reload();
            },
            error: function(xhr, status, error) {
                var err = eval("(" + xhr.responseText + ")");
                window.alert(JSON.stringify(xhr));
                console.log(JSON.stringify(xhr));
                $('#save').attr('disabled', false);
            }

        })
        
    }

});	

//add json modal
$("#jsonModal").on('submit','#jsonForm', function(event){
    event.preventDefault();
    $('#json_add').attr('disabled','disabled');
    jsonString = $('#jsontext').val();
    $.ajax({
        url:"/stratins/",
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-API-Key',
                API_KEY); },
        method:"POST",
        contentType: "application/json",
        dataType: "json",
        data: jsonString,
        success:function(data){				
            $('#jsonForm')[0].reset();
            window.$('#jsonModal').modal('hide');				
            $('#json_add').attr('disabled', false);
            setTimeout(function () {
                runnerRecords.ajax.reload();
                stratinRecords.ajax.reload();
                }, 750)
        },
        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            window.alert(JSON.stringify(xhr));
            console.log(JSON.stringify(xhr));
            $('#json_add').attr('disabled', false);
        }
    })
});


//delete modal
$("#delModal").on('submit','#delForm', function(event){
        event.preventDefault();
        $('#delete').attr('disabled','disabled');
        var formData = $(this).serializeJSON();
        $.ajax({
            url:"/stratins/"+formData.delid,
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-API-Key',
                    API_KEY); },
            method:"DELETE",
            contentType: "application/json",
            dataType: "json",
            success:function(data){				
                $('#delForm')[0].reset();
                window.$('#delModal').modal('hide');				
                $('#delete').attr('disabled', false);
                stratinRecords.ajax.reload();
            },
            error: function(xhr, status, error) {
                var err = eval("(" + xhr.responseText + ")");
                window.alert(JSON.stringify(xhr));
                console.log(JSON.stringify(xhr));
                $('#delete').attr('disabled', false);
            }

        })
});
