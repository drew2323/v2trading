//delete modal
$("#delModalRunmanager").on('submit','#delFormRunmanager', function(event){
    event.preventDefault();
    $('#deleterunmanager').attr('disabled','disabled');

    //get val from #delidrunmanager
    id = $('#delidrunmanager').val();
    delete_runmanager_row(id);
});

//add api
// fetch(`/run_manager_records/`, {
//     method: 'POST',
//     headers: { 
//         'Content-Type': 'application/json',
//         'X-API-Key': API_KEY 
//     },
//     body: JSON.stringify(newRecord) 
// })

// fetch(`/run_manager_records/${recordId}`, {
//     method: 'PATCH',
//     headers: { 
//         'Content-Type': 'application/json',
//         'X-API-Key': API_KEY 
//     },
//     body: JSON.stringify(updatedData)
// })

function getCheckedWeekdays() {
    const checkboxes = document.querySelectorAll('input[name="weekdays_filter[]"]:checked');
    const selectedDays = Array.from(checkboxes).map(checkbox => checkbox.value);
    return selectedDays;
}


//submit form
$("#addeditModalRunmanager").on('submit','#addeditFormRunmanager', function(event){
    //event.preventDefault();
    //code for add
    if ($('#runmanagersubmit').val() == "Add") {

        event.preventDefault();
        //set id as editable
        $('#runmanagersubmit').attr('disabled','disabled');
        //trow = runmanagerRecords.row('.selected').data();
        //note = $('#editnote').val()

        // Handle weekdays functionality
        var weekdays = [];
        if ($('#runman_enable_weekdays').is(':checked')) {
            $('#addeditFormRunmanager input[name="weekdays"]:checked').each(function() {
                var weekday = $(this).val();
                switch(weekday) {
                    case 'monday':    weekdays.push(0); break;
                    case 'tuesday':   weekdays.push(1); break;
                    case 'wednesday': weekdays.push(2); break;
                    case 'thursday':  weekdays.push(3); break;
                    case 'friday':    weekdays.push(4); break;
                    // Add cases for Saturday and Sunday if needed
                }
            });
        }
        console.log("weekdays pole", weekdays)

        var formData = $(this).serializeJSON();
        console.log("formData", formData)

        delete formData["enable_weekdays"]
        delete formData["weekdays"]

        //pokud je zatrzeno tak aplikujeme filter, jinak nevyplnujeme
        if (weekdays.length > 0) {
            formData.weekdays_filter = weekdays
        }
        console.log(formData)
        if ($('#runmanilog_save').prop('checked')) {
            formData.ilog_save = true;
        }
        else 
        {
            formData.ilog_save = false;
        }

        //if (formData.batch_id == "") {delete formData["batch_id"];}

        //projede vsechny atributy a kdyz jsou "" tak je smaze, default nahradi backend
        for (let key in formData) {
            if (formData.hasOwnProperty(key) && formData[key] === "") {
                delete formData[key];
            }
        }

        jsonString = JSON.stringify(formData);
        console.log("json string pro formData pred odeslanim", jsonString)
        $.ajax({
            url:"/run_manager_records/",
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-API-Key',
                    API_KEY); },
            method:"POST",
            contentType: "application/json",
            // dataType: "json",
            data: jsonString,
            success:function(data){				
                $('#addeditFormRunmanager')[0].reset();
                window.$('#addeditModalRunmanager').modal('hide');				
                $('#runmanagersubmit').attr('disabled', false);
                runmanagerRecords.ajax.reload();
                disable_runmanager_buttons();
            },
            error: function(xhr, status, error) {
                var err = eval("(" + xhr.responseText + ")");
                window.alert(JSON.stringify(xhr));
                console.log(JSON.stringify(xhr));
                $('#runmanagersubmit').attr('disabled', false);
            }
        })
    }
    //code for edit
    else {
        event.preventDefault();       
        $('#runmanagersubmit').attr('disabled','disabled');
        //trow = runmanagerRecords.row('.selected').data();
        //note = $('#editnote').val()

        // Handle weekdays functionality
        var weekdays = [];
        if ($('#runman_enable_weekdays').is(':checked')) {
            $('#addeditFormRunmanager input[name="weekdays"]:checked').each(function() {
                var weekday = $(this).val();
                switch(weekday) {
                    case 'monday':    weekdays.push(0); break;
                    case 'tuesday':   weekdays.push(1); break;
                    case 'wednesday': weekdays.push(2); break;
                    case 'thursday':  weekdays.push(3); break;
                    case 'friday':    weekdays.push(4); break;
                    // Add cases for Saturday and Sunday if needed
                }
            });
        }

        var formData = $(this).serializeJSON();
        delete formData["enable_weekdays"]
        delete formData["weekdays"]

        //pokud je zatrzeno tak aplikujeme filter, jinak nevyplnujeme
        if (weekdays.length > 0) {
            formData.weekdays_filter = weekdays
        }
        console.log(formData)
        if ($('#runmanilog_save').prop('checked')) {
            formData.ilog_save = true;
        }
        else 
        {
            formData.ilog_save = false;
        }

        //projede formatributy a kdyz jsou "" tak je smaze, default nahradi backend - tzn. smaze se puvodni hodnota
        for (let key in formData) {
            if (formData.hasOwnProperty(key) && formData[key] === "") {
                delete formData[key];
            }
        }

        jsonString = JSON.stringify(formData);
        console.log("EDIT json string pro formData pred odeslanim", jsonString);
        $.ajax({
            url:"/run_manager_records/"+formData.id,
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-API-Key',
                    API_KEY); },
            method:"PATCH",
            contentType: "application/json",
            // dataType: "json",
            data: jsonString,
            success:function(data){
                console.log("EDIT success data", data);				
                $('#addeditFormRunmanager')[0].reset();
                window.$('#addeditModalRunmanager').modal('hide');				
                $('#runmanagersubmit').attr('disabled', false);
                runmanagerRecords.ajax.reload();
                disable_runmanager_buttons();
            },
            error: function(xhr, status, error) {
                var err = eval("(" + xhr.responseText + ")");
                window.alert(JSON.stringify(xhr));
                console.log(JSON.stringify(xhr));
                $('#runmanagersubmit').attr('disabled', false);
            }
        });  
    }
        
});