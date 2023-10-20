//ARCHIVE TABLES
let editor_diff_arch1
let editor_diff_arch2

function refresh_arch_and_callback(row, callback) {
    console.log("entering refresh")
    var request = $.ajax({
        url: "/archived_runners/"+row.id,
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-API-Key',
            API_KEY); },
        method:"GET",
        contentType: "application/json",
        dataType: "json",
        success:function(data){   
            console.log("fetched data ok")                      
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
        console.log("Response received. calling callback")
        //call callback function
        callback(response)

    }, function(error) {
        // Handle errors from either request here
        // Example:
        console.error("Error from first request:", error);
        console.log("requesting id error")
    });
}

$(document).ready(function () {
    archiveRecords.ajax.reload();

    //button clear log
    $('#button_clearlog').click(function () {
		$('#lines').empty();
    });

    //disable buttons (enable on row selection)
    $('#button_runagain_arch').attr('disabled','disabled');
    $('#button_show_arch').attr('disabled','disabled');
    $('#button_delete_arch').attr('disabled','disabled');
    $('#button_edit_arch').attr('disabled','disabled');
    $('#button_compare_arch').attr('disabled','disabled');

    //selectable rows in archive table
    $('#archiveTable tbody').on('click', 'tr', function () {
        if ($(this).hasClass('selected')) {
            //$(this).removeClass('selected');
            $('#button_show_arch').attr('disabled','disabled');
            $('#button_runagain_arch').attr('disabled','disabled');
            $('#button_delete_arch').attr('disabled','disabled');
            $('#button_edit_arch').attr('disabled','disabled');
            $('#button_compare_arch').attr('disabled','disabled');
        } else {
            //archiveRecords.$('tr.selected').removeClass('selected');
            $(this).addClass('selected');
            $('#button_show_arch').attr('disabled',false);
            $('#button_runagain_arch').attr('disabled',false);
            $('#button_delete_arch').attr('disabled',false);
            $('#button_edit_arch').attr('disabled',false);
            $('#button_compare_arch').attr('disabled',false);
        }
    });

    //button compare arch
    $('#button_compare_arch').click(function () {
        if (editor_diff_arch1) {editor_diff_arch1.dispose()}
        if (editor_diff_stratin1) {editor_diff_stratin1.dispose()}
        if (editor_diff_arch2) {editor_diff_arch2.dispose()}
        if (editor_diff_stratin2) {editor_diff_stratin2.dispose()}
        window.$('#diffModal').modal('show');
        rows = archiveRecords.rows('.selected').data();

        id1 = rows[0].id
        id2 = rows[1].id

        var request1 = $.ajax({
          url: "/archived_runners/"+id1,
          beforeSend: function (xhr) {
              xhr.setRequestHeader('X-API-Key',
              API_KEY); },
          method:"GET",
          contentType: "application/json",
          dataType: "json",
          success:function(data){   
              console.log("first request ok")                      
              console.log(JSON.stringify(data,null,2));
          },
          error: function(xhr, status, error) {
              var err = eval("(" + xhr.responseText + ")");
              window.alert(JSON.stringify(xhr));
              console.log(JSON.stringify(xhr));
              console.log("first request error")
          }
        });
        var request2 = $.ajax({
            url: "/archived_runners/"+id2,
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-API-Key',
                API_KEY); },
            method:"GET",
            contentType: "application/json",
            dataType: "json",
            success:function(data){   
                console.log("first request ok")                      
                console.log(JSON.stringify(data,null,2));
            },
            error: function(xhr, status, error) {
                var err = eval("(" + xhr.responseText + ")");
                window.alert(JSON.stringify(xhr));
                console.log(JSON.stringify(xhr));
                console.log("first request error")
            }
          });

        // Handling the responses of both requests
        $.when(request1, request2).then(function(response1, response2) {
            // Both requests have completed successfully
            var result1 = response1[0];
            var result2 = response2[0];
            console.log("Result from first request:", result1);
            console.log("Result from second request:", result2);
            console.log("calling compare")
            perform_compare(result1, result2)
            // Perform your action with the results from both requests
            // Example:

        }, function(error1, error2) {
            // Handle errors from either request here
            // Example:
            console.error("Error from first request:", error1);
            console.error("Error from second request:", error2);
        });

        //sem vstupuji dva nove natahnute objekty 
        function perform_compare(data1, data2) {

            var record1 = new Object()
            //console.log(JSON.stringify(rows))

            record1 = JSON.parse(data1.strat_json)
            //record1.json = rows[0].json
            //record1.id = rows[0].id;
            // record1.id2 = parseInt(rows[0].id2);
            //record1.name = rows[0].name;
            // record1.symbol = rows[0].symbol;
            // record1.class_name = rows[0].class_name;
            // record1.script = rows[0].script;
            // record1.open_rush = rows[0].open_rush;
            // record1.close_rush = rows[0].close_rush;
            //console.log(record1.stratvars_conf)

            //ELEMENTS TO COMPARE

            //profit sekce
            console.log(data1.metrics)

            try {
                record1["profit"] = JSON.parse(data1.metrics.profit)
            }
            catch (e) {
                console.log(e.message)
            }

            //record1.stratvars_conf = TOML.parse(record1.stratvars_conf);
            //record1.add_data_conf = TOML.parse(record1.add_data_conf);
            // record1.note = rows[0].note;
            // record1.history = "";
        //jsonString1 = JSON.stringify(record1, null, 2);

            var record2 = new Object()
            record2 = JSON.parse(data2.strat_json)

            // record2.id = rows[1].id;
            // record2.id2 = parseInt(rows[1].id2);
            //record2.name = rows[1].name;
            // record2.symbol = rows[1].symbol;
            // record2.class_name = rows[1].class_name;
            // record2.script = rows[1].script;
            // record2.open_rush = rows[1].open_rush;
            // record2.close_rush = rows[1].close_rush;
    
            //ELEMENTS TO COMPARE
            console.log(data2.metrics)

            try {
                record2["profit"] = JSON.parse(data2.metrics.profit)
            }
            catch (e) {
                console.log(e.message)
            }
            //record2.stratvars_conf = TOML.parse(record2.stratvars_conf);
            //record2.add_data_conf = TOML.parse(record2.add_data_conf);
            // record2.note = rows[1].note;
            // record2.history = "";
            //jsonString2 = JSON.stringify(record2, null, 2);

            $('#diff_first').text(record1.name);
            $('#diff_second').text(record2.name);
            $('#diff_first_id').text(data1.id);
            $('#diff_second_id').text(data2.id);

            //monaco
            require(["vs/editor/editor.main"], () => {
                editor_diff_arch1 = monaco.editor.createDiffEditor(document.getElementById('diff_content1'),
                    {
                        language: 'toml',
                        theme: 'tomlTheme-dark',
                        originalEditable: false,
                        automaticLayout: true
                    }
                );
                console.log(record1.stratvars_conf)
                console.log(record2.stratvars_conf)
                editor_diff_arch1.setModel({
                    original: monaco.editor.createModel(record1.stratvars_conf, 'toml'),
                    modified: monaco.editor.createModel(record2.stratvars_conf, 'toml'),
                });
                editor_diff_arch2 = monaco.editor.createDiffEditor(document.getElementById('diff_content2'),
                    {
                        language: 'toml',
                        theme: 'tomlTheme-dark',
                        originalEditable: false,
                        automaticLayout: true
                    }
                );
                editor_diff_arch2.setModel({
                    original: monaco.editor.createModel(record1.add_data_conf, 'toml'),
                    modified: monaco.editor.createModel(record2.add_data_conf, 'toml'),
                });
            });

            // var delta = compareObjects(record1, record2)
            // const htmlMarkup2 = `<pre>{\n${generateHTML(record2, delta)}}\n</pre>`;
            // document.getElementById('second').innerHTML = htmlMarkup2;

            // const htmlMarkup1 = `<pre>{\n${generateHTML(record1, delta)}}\n</pre>`;
            // document.getElementById('first').innerHTML = htmlMarkup1;

            event.preventDefault();
            //$('#button_compare').attr('disabled','disabled');
        }
    });


    //delete button
    $('#button_delete_arch').click(function () {
        rows = archiveRecords.rows('.selected');
        if (rows == undefined) {
            return
        }
        $('#listofids').html("");

        if(rows.data().length > 0 ) {
            ids_to_del = ""
            // Loop through the selected rows and display an alert with each row's ID
            rows.every(function (rowIdx, tableLoop, rowLoop ) {
                var data = this.data()
                ids_to_del = ids_to_del  + data.id + "<br>"
            });

            $('#listofids').html(ids_to_del);
            window.$('#delModalArchive').modal('show');
            //$('#delidarchive').val(row.id);
        }
    });

    //edit button
    $('#button_edit_arch').click(function () {
        row = archiveRecords.row('.selected').data();
        if (row == undefined) {
            return
        }

        refresh_arch_and_callback(row, display_edit_modal)

        function display_edit_modal(row) {
            window.$('#editModalArchive').modal('show');
            $('#editidarchive').val(row.id);
            $('#editnote').val(row.note);


            try {
                metrics = JSON.parse(row.metrics)
            }
            catch (e) {
                metrics = row.metrics
            }
            $('#metrics').val(JSON.stringify(metrics,null,2));
            //$('#metrics').val(TOML.parse(row.metrics));
            if (row.stratvars_toml) {
                $('#editstratvars').val(row.stratvars_toml);
            }
            else{
                $('#editstratvars').val(JSON.stringify(row.stratvars,null,2));
            }
            
            
            $('#editstratjson').val(row.strat_json);
        }
    });

    //show button
    $('#button_show_arch').click(function () {

        row = archiveRecords.row('.selected').data();
        if (row == undefined) {
            return
        }

        refresh_arch_and_callback(row, get_detail_and_show)

        function get_detail_and_show(row) {
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
                    console.log(JSON.stringify(data,null,2));
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
    });
})

    //run again button
    $('#button_runagain_arch').click(function () {
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
                console.log("fetched data ok")                      
                console.log(JSON.stringify(data,null,2));
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
                console.log("fetched data ok")                      
                console.log(JSON.stringify(data,null,2));
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

            console.log("Result from first request:", result1);
            console.log("Result from second request:", result2);

            console.log("calling compare")
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
            console.log(record1)

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
            record1["test_batch_id"];

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

            console.log("record1 pred odeslanim", record1)
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

})

//edit modal
$("#editModalArchive").on('submit','#editFormArchive', function(event){
    event.preventDefault();
    $('#editarchive').attr('disabled','disabled');
    trow = archiveRecords.row('.selected').data();
    note = $('#editnote').val()
    var formData = $(this).serializeJSON();
    row = {}
    row["id"] = trow.id
    row["note"] = note
    jsonString = JSON.stringify(row);
    console.log("pred odeslanim json string", jsonString)
    $.ajax({
        url:"/archived_runners/"+trow.id,
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-API-Key',
                API_KEY); },
        method:"PATCH",
        contentType: "application/json",
        // dataType: "json",
        data: jsonString,
        success:function(data){				
            $('#editFormArchive')[0].reset();
            window.$('#editModalArchive').modal('hide');				
            $('#editarchive').attr('disabled', false);
            archiveRecords.ajax.reload();
        },
        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            window.alert(JSON.stringify(xhr));
            console.log(JSON.stringify(xhr));
            $('#editarchive').attr('disabled', false);
        }
    })
});

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
            console.log(data)
            archiveRecords.ajax.reload();
        },
        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            window.alert(JSON.stringify(xhr));
            console.log(JSON.stringify(xhr));
            $('#deletearchive').attr('disabled', false);
            archiveRecords.ajax.reload();
        }
    })
}

//delete modal
$("#delModalArchive").on('submit','#delFormArchive', function(event){
    event.preventDefault();
    $('#deletearchive').attr('disabled','disabled');
    //rows = archiveRecords.rows('.selected');
    if(rows.data().length > 0 ) {
        runnerIds = []
        // Loop through the selected rows and display an alert with each row's ID
        rows.every(function (rowIdx, tableLoop, rowLoop ) {
            var data = this.data()
            runnerIds.push(data.id);
        });
        delete_arch_rows(runnerIds)
    }
});

//archive table
var archiveRecords = 
    $('#archiveTable').DataTable( {
        ajax: { 
            url: '/archived_runners/',
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
                    {data: 'strat_id'},
                    {data: 'name'},
                    {data: 'symbol'},
                    {data: 'note'},
                    {data: 'started'},
                    {data: 'stopped'},
                    {data: 'mode'},
                    {data: 'account', visible: true},
                    {data: 'bt_from', visible: true},
                    {data: 'bt_to', visible: true},
                    {data: 'ilog_save', visible: true},
                    {data: 'profit'},
                    {data: 'trade_count', visible: true},
                    {data: 'end_positions', visible: true},
                    {data: 'end_positions_avgp', visible: true},
                    {data: 'metrics', visible: true},
                    {data: 'batch_id', visible: true},
                ],
        paging: false,
        processing: false,
        columnDefs: [{
            targets: [0,1,17],
            render: function ( data, type, row ) {
                if (!data) return data
                return '<div class="tdnowrap" title="'+data+'">'+data+'</i>'
            },
            },
            {
                targets: [5],
                render: function ( data, type, row ) {
                    now = new Date(data)
                    if (type == "sort") {
                        return new Date(data).getTime();
                    }
                    var date = new Date(data);
                    tit = date.toLocaleString('cs-CZ', {
                            timeZone: 'America/New_York',
                          })

                    if (isToday(now)) {
                        //return local time only
                        return '<div title="'+tit+'">'+ 'dnes ' + format_date(data,false,true)+'</div>'
                    }
                    else
                    {
                        //return  local datetime
                        return '<div title="'+tit+'">'+ format_date(data,false,false)+'</div>'
                    }
                },
                },
                {
                    targets: [6],
                    render: function ( data, type, row ) {
                        now = new Date(data)
                        if (type == "sort") {
                            return new Date(data).getTime();
                        }
                        var date = new Date(data);
                        tit = date.toLocaleString('cs-CZ', {
                                timeZone: 'America/New_York',
                              })
    
                        if (isToday(now)) {
                            //return local time only
                            return '<div title="'+tit+'" class="token level comment">'+ 'dnes ' + format_date(data,false,true)+'</div>'
                        }
                        else
                        {
                            //return  local datetime
                            return '<div title="'+tit+'" class="token level number">'+ format_date(data,false,false)+'</div>'
                        }
                    },
                    },
                {
                targets: [9,10],
                render: function ( data, type, row ) {
                    if (type == "sort") {
                        return new Date(data).getTime();
                    }
                    //console.log(data)
                    //market datetime
                    return data ? format_date(data, true) : data
                },
                },
                {
                    targets: [2],
                    render: function ( data, type, row ) {
                        return '<div class="tdname tdnowrap" title="'+data+'">'+data+'</div>'
                    },
                },
                // {
                //     targets: [4],
                //     render: function ( data, type, row ) {
                //         return '<div class="tdname tdnowrap" title="'+data+'">'+data+'</div>'
                //     },
                // },
                {
                    targets: [16],
                    render: function ( data, type, row ) {
                        //console.log("metrics", data)
                        try {
                            data = JSON.parse(data)
                        }
                        catch (error) {
                            //console.log(error)
                        }
                        var res = JSON.stringify(data)
                        var unquoted = res.replace(/"([^"]+)":/g, '$1:')

                        //zobrazujeme jen kratkou summary pokud mame, jinak davame vse, do titlu davame vzdy vse
                        //console.log(data)
                        short = null
                        if ((data) && (data.profit) && (data.profit.sum)) {
                            short = data.profit.sum
                        }
                        else {
                            short = unquoted
                        }
                        return '<div class="tdmetrics" title="'+unquoted+'">'+short+'</div>'
                    },
                },
                {
                    targets: [4],
                    render: function ( data, type, row ) {
                        return '<div class="tdnote" title="'+data+'">'+data+'</div>'
                    },
                },
                {
                    targets: [13,14,15],
                    render: function ( data, type, row ) {
                        return '<div class="tdsmall">'+data+'</div>'
                    },
                },
                {
                    targets: [11],
                    render: function ( data, type, row ) {
                        //if ilog_save true
                        if (data) {
                            return '<span class="material-symbols-outlined">done_outline</span>'
                        }
                        else {
                            return null
                        }
                    },
                },
                {
                    targets: [8],
                    render: function ( data, type, row ) {
                        //if ilog_save true
                        if (data == "ACCOUNT1") {
                            res="ACC1"
                        }
                        else if (data == "ACCOUNT2") {
                            res="ACC2"
                        }
                        else { res=data}
                        return res
                    },
                },
                {
                    targets: [7],
                    render: function ( data, type, row ) {
                        //if ilog_save true
                        if (data == "backtest") {
                            res="bt"
                        }
                        else { res=data}
                        return res
                    },
                }
        ],
        order: [[6, 'desc']],
        select: {
            style: 'multi',
            selector: 'td'
        },
        paging: true,
        // lengthChange: false,
        // select: true,
        // createdRow: function( row, data, dataIndex){
        //     if (is_running(data.id) ){
        //         alert("runner");
        //         $(row).addClass('highlight');
        //     }
        //}
        } );

//WIP buttons to hide datatable columns
        // document.querySelectorAll('a.toggle-vis').forEach((el) => {
        //     el.addEventListener('click', function (e) {
        //         e.preventDefault();
         
        //         let columnIdx = e.target.getAttribute('data-column');
        //         let column = archiveRecords.column(columnIdx);
         
        //         // Toggle the visibility
        //         column.visible(!column.visible());
        //     });
        // });

        