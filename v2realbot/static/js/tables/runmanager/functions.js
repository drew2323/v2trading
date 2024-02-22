function refresh_runmanager_and_callback(row, callback) {
    //console.log("entering refresh")
    var request = $.ajax({
        url: "/run_manager_records/"+row.id,
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

function delete_runmanager_row(id) {
    $.ajax({
        url:"/run_manager_records/"+id,
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-API-Key',
                API_KEY); },
        method:"DELETE",
        contentType: "application/json",
        dataType: "json",
        // data: JSON.stringify(ids),
        success:function(data){				
            $('#delFormRunmanager')[0].reset();
            window.$('#delModalRunmanager').modal('hide');				
            $('#deleterunmanager').attr('disabled', false);
            //console.log(data)
            runmanagerRecords.ajax.reload();
            disable_runmanager_buttons()
        },
        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            window.alert(JSON.stringify(xhr));
            console.log(JSON.stringify(xhr));
            $('#deleterunmanager').attr('disabled', false);
            //archiveRecords.ajax.reload();
        }
    })
}

//enable/disable based if row(s) selected
function disable_runmanager_buttons() {
    //disable buttons (enable on row selection)
    //$('#button_add_sched').attr('disabled','disabled');
    $('#button_edit_sched').attr('disabled','disabled');
    $('#button_delete_sched').attr('disabled','disabled');
    $('#button_history_sched').attr('disabled','disabled');
}

function enable_runmanager_buttons() {
    //enable buttons
    //$('#button_add_sched').attr('disabled',false);
    $('#button_edit_sched').attr('disabled',false);
    $('#button_delete_sched').attr('disabled',false);
    $('#button_history_sched').attr('disabled',false);
}

// Function to update options
function updateSelectOptions(type) {
    var allOptions = {
        'paper': '<option value="paper">paper</option>',
        'live': '<option value="live">live</option>',
        'backtest': '<option value="backtest">backtest</option>',
        'prep': '<option value="prep">prep</option>'
    };

    var allowedOptions = (type === "schedule") ? ['paper', 'live'] : Object.keys(allOptions);
    
    var $select = $('#runmanmode');
    $select.empty(); // Clear current options

    allowedOptions.forEach(function(opt) {
        $select.append(allOptions[opt]); // Append allowed options
    });
}