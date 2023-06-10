//ARCHIVE TABLES
$(document).ready(function () {
    archiveRecords.ajax.reload();

    //button clear log
    $('#button_clearlog').click(function () {
		$('#lines').empty();
    });

    //disable buttons (enable on row selection)
    $('#button_show_arch').attr('disabled','disabled');
    $('#button_delete_arch').attr('disabled','disabled');
    $('#button_edit_arch').attr('disabled','disabled');
    $('#button_compare_arch').attr('disabled','disabled');

    //selectable rows in archive table
    $('#archiveTable tbody').on('click', 'tr', function () {
        if ($(this).hasClass('selected')) {
            //$(this).removeClass('selected');
            $('#button_show_arch').attr('disabled','disabled');
            $('#button_delete_arch').attr('disabled','disabled');
            $('#button_edit_arch').attr('disabled','disabled');
            $('#button_compare_arch').attr('disabled','disabled');
        } else {
            //archiveRecords.$('tr.selected').removeClass('selected');
            $(this).addClass('selected');
            $('#button_show_arch').attr('disabled',false);
            $('#button_delete_arch').attr('disabled',false);
            $('#button_edit_arch').attr('disabled',false);
            $('#button_compare_arch').attr('disabled',false);
        }
    });


    //button compare arch
    $('#button_compare_arch').click(function () {
        window.$('#diffModal').modal('show');
        rows = archiveRecords.rows('.selected').data();
        var record1 = new Object()
        //console.log(JSON.stringify(rows))
        record1 = JSON.parse(rows[0].strat_json)
        //record1.json = rows[0].json
        //record1.id = rows[0].id;
        // record1.id2 = parseInt(rows[0].id2);
        //record1.name = rows[0].name;
        // record1.symbol = rows[0].symbol;
        // record1.class_name = rows[0].class_name;
        // record1.script = rows[0].script;
        // record1.open_rush = rows[0].open_rush;
        // record1.close_rush = rows[0].close_rush;
        record1.stratvars_conf = TOML.parse(record1.stratvars_conf);
        record1.add_data_conf = TOML.parse(record1.add_data_conf);
        // record1.note = rows[0].note;
        // record1.history = "";
       //jsonString1 = JSON.stringify(record1, null, 2);

        var record2 = new Object()
        record2 = JSON.parse(rows[1].strat_json)

        // record2.id = rows[1].id;
        // record2.id2 = parseInt(rows[1].id2);
        //record2.name = rows[1].name;
        // record2.symbol = rows[1].symbol;
        // record2.class_name = rows[1].class_name;
        // record2.script = rows[1].script;
        // record2.open_rush = rows[1].open_rush;
        // record2.close_rush = rows[1].close_rush;
        record2.stratvars_conf = TOML.parse(record2.stratvars_conf);
        record2.add_data_conf = TOML.parse(record2.add_data_conf);
        // record2.note = rows[1].note;
        // record2.history = "";
        //jsonString2 = JSON.stringify(record2, null, 2);


        document.getElementById('first').innerHTML = '<pre>'+JSON.stringify(record1, null, 2)+'</pre>'
       $('#diff_first').text(record1.name);
       $('#diff_second').text(record2.name);

        //mozna parse?

        var delta = compareObjects(record1, record2)
        const htmlMarkup1 = `<pre>{\n${generateHTML(record2, delta)}}\n</pre>`;
        document.getElementById('second').innerHTML = htmlMarkup1;

        event.preventDefault();
        //$('#button_compare').attr('disabled','disabled');
    });


    //delete button
    $('#button_delete_arch').click(function () {
        row = archiveRecords.row('.selected').data();
        window.$('#delModalArchive').modal('show');
        $('#delidarchive').val(row.id);
    });

    //edit button
    $('#button_edit_arch').click(function () {
        row = archiveRecords.row('.selected').data();
        window.$('#editModalArchive').modal('show');
        $('#editidarchive').val(row.id);
        $('#editnote').val(row.note);
        $('#metrics').val(JSON.stringify(row.open_orders,null,2));
        $('#editstratvars').val(JSON.stringify(row.stratvars,null,2));
        $('#editstratjson').val(row.strat_json);
    });

    //show button
    $('#button_show_arch').click(function () {
        row = archiveRecords.row('.selected').data();
        $('#button_show_arch').attr('disabled',true);
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
    });
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


//delete modal
$("#delModalArchive").on('submit','#delFormArchive', function(event){
    event.preventDefault();
    $('#deletearchive').attr('disabled','disabled');
    id = $('#delidarchive').val()
    //var formData = $(this).serializeJSON();
    $.ajax({
        url:"/archived_runners/"+id,
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-API-Key',
                API_KEY); },
        method:"DELETE",
        contentType: "application/json",
        dataType: "json",
        success:function(data){				
            $('#delFormArchive')[0].reset();
            window.$('#delModalArchive').modal('hide');				
            $('#deletearchive').attr('disabled', false);
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
                    {data: 'stratvars', visible: false},
                    {data: 'profit'},
                    {data: 'trade_count', visible: true},
                    {data: 'end_positions', visible: true},
                    {data: 'end_positions_avgp', visible: true},
                    {data: 'strat_json', visible: false},
                    {data: 'open_orders', visible: true}
                ],
        paging: false,
        processing: false,
        columnDefs: [{
            targets: [0,1],
            render: function ( data, type, row ) {
                return '<div class="tdnowrap" title="'+data+'">'+data+'</i>'
            },
            },
            {
                targets: [5,6],
                render: function ( data, type, row ) {
                    now = new Date(data)
                    if (type == "sort") {
                        return new Date(data).getTime();
                    }
                    
                    if (isToday(now)) {
                        //return local time only
                        return 'dnes ' + format_date(data,false,true)
                    }
                    else
                    {
                        //return  local datetime
                        return format_date(data,false,false)
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
                        return '<div class="tdname" title="'+data+'">'+data+'</i>'
                    },
                },
                {
                    targets: [18],
                    render: function ( data, type, row ) {
                        var res = JSON.stringify(data)
                        const unquoted = res.replace(/"([^"]+)":/g, '$1:')
                        return '<div class="tdmetrics" title="'+unquoted+'">'+unquoted+'</i>'
                    },
                },
                {
                    targets: [4],
                    render: function ( data, type, row ) {
                        return '<div class="tdnote" title="'+data+'">'+data+'</i>'
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


        