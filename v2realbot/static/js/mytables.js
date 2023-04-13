
API_KEY = localStorage.getItem("api-key")

//on button
function store_api_key(event) {
    key = document.getElementById("api-key").value;
    localStorage.setItem("api-key", key);
    API_KEY = key;
}

function get_status(id) {
    var status = "stopped"
    runnerRecords.rows().iterator('row', function ( context, index ) {
        var data = this.row(index).data();
        //window.alert(JSON.stringify(data))
        if (data.id == id) {
            //window.alert("found");
            if ((data.run_mode) == "backtest") { status_detail = data.run_mode}
            else { status_detail = data.run_mode + " | " + data.run_account}
            if (data.run_paused == null) {
                status = "running | "+ status_detail
            }
            else {
                status = "paused | "+ status_detail
            }}
            //window.alert("found") }
    });
    return status
}

function is_running(id) {
    var running = false
    runnerRecords.rows().iterator('row', function ( context, index ) {
        var data = this.row(index).data();
        //window.alert(JSON.stringify(data))
        if (data.id == id) {
            running = true    
        }
            //window.alert("found") }
    });
    return running
}
    // alert(JSON.stringify(stratinRecords.data()))
    // arr = stratinRecords.data()
    // foreach(row in arr.rows) {
    //     alert(row.id)
    // }

    // //let obj = arr.find(o => o.id2 === '2');
    // //console.log(obj);
    // //alert(JSON.stringify(obj))




$(document).ready(function () {
    //reaload hlavni tabulky

    stratinRecords.ajax.reload();
    runnerRecords.ajax.reload();

    //disable buttons (enable on row selection)
    $('#button_pause').attr('disabled','disabled');
    $('#button_stop').attr('disabled','disabled');
    $('#button_edit').attr('disabled','disabled');
    $('#button_delete').attr('disabled','disabled');
    $('#button_run').attr('disabled','disabled');

    //selectable rows in stratin table
    $('#stratinTable tbody').on('click', 'tr', function () {
        if ($(this).hasClass('selected')) {
            $(this).removeClass('selected');
            $('#button_edit').attr('disabled','disabled');
            $('#button_delete').attr('disabled','disabled');
            $('#button_run').attr('disabled','disabled');
        } else {
            stratinRecords.$('tr.selected').removeClass('selected');
            $(this).addClass('selected');
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
        } else {
            stratinRecords.$('tr.selected').removeClass('selected');
            $(this).addClass('selected');
            $('#button_pause').attr('disabled', false);
            $('#button_stop').attr('disabled', false);
        }
    });

    //button refresh
    $('#button_refresh').click(function () {
        runnerRecords.ajax.reload();
        stratinRecords.ajax.reload();
    })

    //button pause
    $('#button_pause').click(function () {
        row = runnerRecords.row('.selected').data();
        event.preventDefault();
        $('#button_pause').attr('disabled','disabled');
        $.ajax({
            url:"/stratins/"+row.id+"/pause",
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

    //button stop
    $('#button_stop').click(function () {
        row = runnerRecords.row('.selected').data();
        event.preventDefault();
        $('#button_stop').attr('disabled','disabled');
        $.ajax({
            url:"/stratins/"+row.id+"/stop",
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
            url:"/stratins/stop",
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
        //$('#runForm')[0].reset();
        $('#runid').val(row.id);
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
    });
    //delete button
    $('#button_delete').click(function () {
        row = stratinRecords.row('.selected').data();
        window.$('#delModal').modal('show');
        $('#delid').val(row.id);
        $('.modal-title').html(" Delete Record");
        $('#action').val('delRecord');
        $('#save').val('Delete');

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
                    {data: 'class_name'},
                    {data: 'script'},
                    {data: 'open_rush', visible: false},
                    {data: 'close_rush', visible: false},
                    {data: 'stratvars_conf', visible: false},
                    {data: 'add_data_conf', visible: false},
                    {data: 'note'},
                    {data: 'history', visible: false},
                    {data: 'id', visible: true}
                ],
        columnDefs: [{
            targets: 12,
            render: function ( data, type, row ) {
                var status = get_status(data)
                return '<i class="fas fa-check-circle">'+status+'</i>'
            },
            }],
        paging: false,
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
                    {data: 'run_started'},
                    {data: 'run_mode'},
                    {data: 'run_account'},
                    {data: 'run_paused'}
                ],
        paging: false,
        processing: false
        } );

//modal na run
$("#runModal").on('submit','#runForm', function(event){
    event.preventDefault();
    $('#run').attr('disabled','disabled');
    var formData = $(this).serializeJSON();
    //rename runid to id
    Object.defineProperty(formData, "id", Object.getOwnPropertyDescriptor(formData, "runid"));
    delete formData["runid"];
    if (formData.bt_from == "") {delete formData["bt_from"];}
    if (formData.bt_to == "") {delete formData["bt_to"];}
    jsonString = JSON.stringify(formData);
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
        //code for add
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

//delete
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
