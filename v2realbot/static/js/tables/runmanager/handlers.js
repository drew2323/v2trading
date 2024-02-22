/* <button title="Create new" id="button_add_sched" class="btn btn-outline-success btn-sm">Add</button>
<button title="Edit selected" id="button_edit_sched" class="btn btn-outline-success btn-sm">Edit</button>
<button title="Delete selected" id="button_delete_sched" class="btn btn-outline-success btn-sm">Delete</button>


id="delModalRunmanager" 
id="addeditModalRunmanager"   id="runmanagersubmit" == "Add vs Edit"
 */

// Function to apply filter
function applyFilter(filter) {
    switch (filter) {
        case 'filterSchedule':
            runmanagerRecords.column(1).search('schedule').draw();
            break;
        case 'filterQueue':
            runmanagerRecords.column(1).search('queue').draw();
            break;
        // default:
        //     runmanagerRecords.search('').columns().search('').draw();
        //     break;
    }
}

// Function to get the ID of current active filter
function getCurrentFilter() {
    var activeFilter = $('input[name="filterOptions"]:checked').attr('id');
    console.log("activeFilter", activeFilter)
    return activeFilter;
}

// Function to show/hide input fields based on the current filter
function updateInputFields() {
    var activeFilter = getCurrentFilter();

    switch (activeFilter) {
        case 'filterSchedule':
            $('#runmantestlist_id_div').hide();
            $('#runmanbt_from_div').hide();
            $('#runmanbt_to_div').hide();

            $('#runmanvalid_from_div').show();
            $('#runmanvalid_to_div').show();
            $('#runmanstart_time_div').show();
            $('#runmanstop_time_div').show();
            break;
        case 'filterQueue':
            $('#runmantestlist_id_div').show();
            $('#runmanbt_from_div').show();
            $('#runmanbt_to_div').show();

            $('#runmanvalid_from_div').hide();
            $('#runmanvalid_to_div').hide();
            $('#runmanstart_time_div').hide();
            $('#runmanstop_time_div').hide();
            break;
        default:
            //$('#inputForSchedule, #inputForQueue').hide();
            break;
    }
}


//event handlers for runmanager table
$(document).ready(function () {
    initialize_runmanagerRecords();
    runmanagerRecords.ajax.reload();
    disable_runmanager_buttons();

    //on click on #button_refresh_sched call runmanagerRecords.ajax.reload()
    $('#button_refresh_sched').click(function () {
        runmanagerRecords.ajax.reload();
    });

    // Event listener for changes in the radio buttons
    $('input[name="filterOptions"]').on('change', function() {
        var selectedFilter = $(this).attr('id');
        applyFilter(selectedFilter);
        // Save the selected filter to local storage
        localStorage.setItem('selectedFilter', selectedFilter);
    });


    // Load the last selected filter from local storage and apply it
    var lastSelectedFilter = localStorage.getItem('selectedFilter');
    if (lastSelectedFilter) {
        $('#' + lastSelectedFilter).prop('checked', true).change();
    }

    //listen for changes on weekday enabling button
    $('#runman_enable_weekdays').change(function() {
        if ($(this).is(':checked')) {
            $('.weekday-checkboxes').show();
        } else {
            $('.weekday-checkboxes').hide();
        }
    }); 

    //selectable rows in runmanager table
    $('#runmanagerTable tbody').on('click', 'tr', function () {
        if ($(this).hasClass('selected')) {
            //$(this).removeClass('selected');
            //aadd here condition that disable is called only when there is no other selected class on tr[data-group-name]
        // Check if there are no other selected rows before disabling buttons
            if ($('#runmanagerTable tr.selected').length === 1) {
                disable_runmanager_buttons();
            }
            //disable_arch_buttons()
        } else {
            //archiveRecords.$('tr.selected').removeClass('selected');
            $(this).addClass('selected');
            enable_runmanager_buttons()
        }
    });


    //delete button
    $('#button_delete_sched').click(function () {
    row = runmanagerRecords.row('.selected').data();
    window.$('#delModalRunmanager').modal('show');
    $('#delidrunmanager').val(row.id);
    // $('#action').val('delRecord');
    // $('#save').val('Delete');
    });

    //button add
    $('#button_add_sched').click(function () {
        window.$('#addeditModalRunmanager').modal('show');
        $('#addeditFormRunmanager')[0].reset();
        //$("#runmanid").prop('readonly', false);
        if (getCurrentFilter() == 'filterQueue') {
            mode = 'queue';
        } else {
            mode = 'schedule';
        }
        //set modus
        $('#runmanmoddus').val(mode);
        //updates fields according to selected type
        updateInputFields();
        updateSelectOptions(mode);
        // Initially, check the value of "batch" and enable/disable "btfrom" and "btto" accordingly
        if ($("#runmantestlist_id").val() !== "") {
            $("#runmanbt_from, #runmanbt_to").prop("disabled", true);
        } else {
            $("#runmanbt_from, #runmanbt_to").prop("disabled", false);
        }

        // Listen for changes in the "batch" input and diasble/enable "btfrom" and "btto" accordingly
        $("#runmantestlist_id").on("input", function() {
            if ($(this).val() !== "") {
                // If "batch" is not empty, disable "from" and "to"
                $("#runmanbt_from, #runmanbt_to").prop("disabled", true);
            } else {
                // If "batch" is empty, enable "from" and "to"
                $("#runmanbt_from, #runmanbt_to").prop("disabled", false);
            }
        });

        $('.modal-title_run').html("<i class='fa fa-plus'></i> Add Record");
        $('#runmanagersubmit').val('Add');
        $('#runmanager_enable_weekdays').prop('checked', false);
        $('.weekday-checkboxes').hide();
    });

    //edit button
    $('#button_edit_sched').click(function () {
        row = runmanagerRecords.row('.selected').data();
        if (row == undefined) {
            return
        }
        window.$('#addeditModalRunmanager').modal('show');
        //set fields as readonly
        //$("#runmanid").prop('readonly', true); 
        //$("#runmanmoddus").prop('readonly', true); 
        console.log("pred editem puvodni row", row)
        refresh_runmanager_and_callback(row, show_edit_modal)

        function show_edit_modal(row) {
            console.log("pred editem refreshnuta row", row);
            $('#addeditFormRunmanager')[0].reset();
            $('.modal-title_run').html("<i class='fa fa-plus'></i> Edit Record");
            $('#runmanagersubmit').val('Edit');

            //updates fields according to selected type
            updateInputFields();
            // get shared attributess
            $('#runmanid').val(row.id);
            $('#runmanhistory').val(row.history);
            $('#runmanlast_processed').val(row.last_processed);
            $('#runmanstrat_id').val(row.strat_id);
            $('#runmanmode').val(row.mode);
            $('#runmanmoddus').val(row.moddus);
            $('#runmanaccount').val(row.account);
            $('#runmanstatus').val(row.status);
            $('#runmanbatch_id').val(row.batch_id);
            $('#runmanrunner_id').val(row.runner_id);
            $("#runmanilog_save").prop("checked", row.ilog_save);
            $('#runmannote').val(row.note);

            $('#runmantestlist_id').val(row.testlist_id);
            $('#runmanbt_from').val(row.bt_from);
            $('#runmanbt_to').val(row.bt_to);

            $('#runmanvalid_from').val(row.valid_from);
            $('#runmanvalid_to').val(row.valid_to);
            $('#runmanstart_time').val(row.start_time);				
            $('#runmanstop_time').val(row.stop_time);

            // Initially, check the value of "batch" and enable/disable "from" and "to" accordingly
            if ($("#runmantestlist_id").val() !== "") {
                $("#runmanbt_from, #runmanbt_to").prop("disabled", true);
            } else {
                $("#runmanbt_from, #runmanbt_to").prop("disabled", false);
            }

            // Listen for changes in the "batch" input
            $("#runmantestlist_id").on("input", function() {
                if ($(this).val() !== "") {
                    // If "batch" is not empty, disable "from" and "to"
                    $("#runmanbt_from, #runmanbt_to").prop("disabled", true);
                } else {
                    // If "batch" is empty, enable "from" and "to"
                    $("#runmanbt_from, #runmanbt_to").prop("disabled", false);
                }
            });

            type =   $('#runmanmoddus').val();
            updateSelectOptions(type);

            //add weekdays_filter transformation from string "1,2,3" to array [1,2,3]
     
            // Assuming you have row.weekend_filter available here
            var weekdayFilter = row.weekdays_filter; 

            //

            if (weekdayFilter) {
                $('#runman_enable_weekdays').prop('checked', true);
                $(".weekday-checkboxes").show();

                // Map numbers to weekday names
                var dayOfWeekMap = {
                    "0": "monday",
                    "1": "tuesday",
                    "2": "wednesday",
                    "3": "thursday",
                    "4": "friday",
                    "5": "saturday", // Adjust if needed for your mapping
                    "6": "sunday"  // Adjust if needed for your mapping
                };

                // Iterate through the selected days
                $.each(weekdayFilter, function(index, dayIndex) {
                    var dayOfWeek = dayOfWeekMap[dayIndex];
                    if (dayOfWeek) { // Make sure the day exists in the map
                        $("#" + dayOfWeek).prop("checked", true);  
                    }
                });
            }
            else {
                $('#runman_enable_weekdays').prop('checked', false);
                $(".weekday-checkboxes").hide();
            }

        }

    });

    //edit button
    $('#button_history_sched').click(function () {
        row = runmanagerRecords.row('.selected').data();
        if (row == undefined) {
            return
        }
        window.$('#historyModalRunmanager').modal('show');
        //set fields as readonly
        //$("#runmanid").prop('readonly', true); 
        //$("#runmanmoddus").prop('readonly', true); 
        //console.log("pred editem puvodni row", row)
        refresh_runmanager_and_callback(row, show_history_modal)

        function show_history_modal(row) {
            //console.log("pred editem refreshnuta row", row);
            $('#historyModalRunmanagerForm')[0].reset();
            // get shared attributess
            $('#RunmanId').val(row.id);
            var date = new Date(row.last_processed);
            formatted = date.toLocaleString('cs-CZ', {
                    timeZone: 'America/New_York',
                })
            $('#Runmanlast_processed').val(formatted);
            $('#Runmanhistory').val(row.history);
        }
    });

});