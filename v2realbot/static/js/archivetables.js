//ARCHIVE TABLES
$(document).ready(function () {
    archiveRecords.ajax.reload();

    //disable buttons (enable on row selection)
    $('#button_show_arch').attr('disabled','disabled');
    $('#button_delete_arch').attr('disabled','disabled');


    //selectable rows in archive table
    $('#archiveTable tbody').on('click', 'tr', function () {
        if ($(this).hasClass('selected')) {
            $(this).removeClass('selected');
            $('#button_show_arch').attr('disabled','disabled');
            $('#button_delete_arch').attr('disabled','disabled');
        } else {
            stratinRecords.$('tr.selected').removeClass('selected');
            $(this).addClass('selected');
            $('#button_show_arch').attr('disabled',false);
            $('#button_delete_arch').attr('disabled',false);
        }
    });

    //delete button
    $('#button_delete_arch').click(function () {
        row = archiveRecords.row('.selected').data();
        window.$('#delModalArchive').modal('show');
        $('#delidarchive').val(row.id);
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
                    {data: 'name'},
                    {data: 'symbol'},
                    {data: 'note'},
                    {data: 'started'},
                    {data: 'stopped'},
                    {data: 'mode'},
                    {data: 'account', visible: true},
                    {data: 'bt_from', visible: true},
                    {data: 'bt_to', visible: true},
                    {data: 'stratvars', visible: true},
                    {data: 'profit'},
                    {data: 'trade_count', visible: true},
                    {data: 'end_positions', visible: true},
                    {data: 'end_positions_avgp', visible: true},
                    {data: 'open_orders', visible: true}
                ],
        columnDefs: [{
            targets: [4,5,8,9],
            render: function ( data, type, row ) {
                return format_date(data)
            },
            }],
        order: [[5, 'desc']],
        paging: true,
        lengthChange: false,
        // createdRow: function( row, data, dataIndex){
        //     if (is_running(data.id) ){
        //         alert("runner");
        //         $(row).addClass('highlight');
        //     }
        //}
        } );