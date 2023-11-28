//mozna dat do dokument ready a rozdelit na handlers a funkce


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
    //console.log("pred odeslanim json string", jsonString)
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
            disable_arch_buttons();
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