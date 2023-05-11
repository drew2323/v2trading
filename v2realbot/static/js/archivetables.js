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

    //selectable rows in archive table
    $('#archiveTable tbody').on('click', 'tr', function () {
        if ($(this).hasClass('selected')) {
            $(this).removeClass('selected');
            $('#button_show_arch').attr('disabled','disabled');
            $('#button_delete_arch').attr('disabled','disabled');
            $('#button_edit_arch').attr('disabled','disabled');
        } else {
            stratinRecords.$('tr.selected').removeClass('selected');
            $(this).addClass('selected');
            $('#button_show_arch').attr('disabled',false);
            $('#button_delete_arch').attr('disabled',false);
            $('#button_edit_arch').attr('disabled',false);
        }
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
                    //market datetime
                    return format_date(data, true)
                },
                },
                {
                    targets: [2],
                    render: function ( data, type, row ) {
                        return '<div class="tdname" title="'+data+'">'+data+'</i>'
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
        // paging: true,
        // lengthChange: false,
        // select: true,
        // createdRow: function( row, data, dataIndex){
        //     if (is_running(data.id) ){
        //         alert("runner");
        //         $(row).addClass('highlight');
        //     }
        //}
        } );


        