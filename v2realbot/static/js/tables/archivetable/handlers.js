//event handlers for archiveTables



$(document).ready(function () {
    initialize_archiveRecords();
    archiveRecords.ajax.reload();
    disable_arch_buttons();


    // Use 'td:nth-child(2)' to target the second column
    $('#archiveTable tbody').on('click', 'td:nth-child(2)', function () {
        var data = archiveRecords.row(this).data();
        //var imageUrl = '/media/report_'+data.id+".png"; // Replace with your logic to get image URL
        var imageUrl = '/media/basic/'+data.id+'.png'; // Replace with your logic to get image URL
        //console.log(imageUrl)
        display_image(imageUrl)
    });

    // Use 'td:nth-child(2)' to target the second column
    $('#archiveTable tbody').on('click', 'td:nth-child(18)', function () {
        var data = archiveRecords.row(this).data();
        if (data.batch_id) {
            display_batch_report(data.batch_id)
        }
    });

    //selectable rows in archive table
    $('#archiveTable tbody').on('click', 'tr[data-group-name]', function () {
        if ($(this).hasClass('selected')) {
            //$(this).removeClass('selected');
            //aadd here condition that disable is called only when there is no other selected class on tr[data-group-name]
        // Check if there are no other selected rows before disabling buttons
            if ($('#archiveTable tr[data-group-name].selected').length === 1) {
                disable_arch_buttons();
            }
            //disable_arch_buttons()
        } else {
            //archiveRecords.$('tr.selected').removeClass('selected');
            $(this).addClass('selected');
            enable_arch_buttons()
        }
    });


    //TOOL BUTTONs on BATCH HEADER

    // Event listener for click to display batch report
    $('#archiveTable tbody').on('click', 'tr.group-header #batchtool_report_button', function (event) {
        event.stopPropagation();
        // Get the parent <tr> element
        var parentTr = $(this).closest('tr');
        // Retrieve the 'data-name' attribute from the parent <tr>
        var batch_id = parentTr.data('name');
        display_batch_report(batch_id)
    });

    // Event listener for click to delete batch
    $('#archiveTable tbody').on('click', 'tr.group-header #batchtool_delete_button', function (event) {
        event.stopPropagation();
        // Get the parent <tr> element
        var parentTr = $(this).closest('tr');
        // Retrieve the 'data-name' attribute from the parent <tr>
        var batch_id = parentTr.data('name');
        $('#batch_id_del').val(batch_id);
        $('#listofids').html("");
        window.$('#delModalBatch').modal('show');
    });

    // Event listener for click to xml export batch
    $('#archiveTable tbody').on('click', 'tr.group-header #batchtool_exportxml_button', function (event) {
        event.stopPropagation();
        // Get the parent <tr> element
        var parentTr = $(this).closest('tr');
        // Retrieve the 'data-name' attribute from the parent <tr>
        var batch_id = parentTr.data('name');
        download_exported_data("xml", batch_id);
    });

    // Event listener for click to csv export batch
    $('#archiveTable tbody').on('click', 'tr.group-header #batchtool_exportcsv_button', function (event) {
        event.stopPropagation();
        // Get the parent <tr> element
        var parentTr = $(this).closest('tr');
        // Retrieve the 'data-name' attribute from the parent <tr>
        var batch_id = parentTr.data('name');
        console.log(batch_id)
        download_exported_data("csv", batch_id);
    });

    // Event listener for optimal batch cutoff
    $('#archiveTable tbody').on('click', 'tr.group-header #batchtool_cutoff_button', function (event) {
        event.stopPropagation();
        // Get the parent <tr> element
        var parentTr = $(this).closest('tr');
        // Retrieve the 'data-name' attribute from the parent <tr>
        var batch_id = parentTr.data('name');
        console.log(batch_id)
        analyze_optimal_cutoff(batch_id)
    });

    //TOOL BUTTONs above the TABLE - for selected days
    //button export
    $('#button_export_xml').click(function(event) {
        download_exported_data("xml");
    });
        
        
    //button export
    $('#button_export_csv').click(function(event) {
        download_exported_data("csv");
    });
    
    //button select page
    $('#button_selpage').click(function () {
        if ($('#button_selpage').hasClass('active')) {
            $('#button_selpage').removeClass('active');
            archiveRecords.rows().deselect();
            disable_arch_buttons();
          }
          else {
            $('#button_selpage').addClass('active');
            archiveRecords.rows( { page: 'current' } ).select();
            enable_arch_buttons();
          }
    });

    //button clear log
    $('#button_clearlog').click(function () {
		$('#lines').empty();
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
              //console.log("first request ok")                      
              //console.log(JSON.stringify(data,null,2));
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
                //console.log("first request ok")                      
                //console.log(JSON.stringify(data,null,2));
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
            //console.log("Result from first request:", result1);
            //console.log("Result from second request:", result2);
            //console.log("calling compare")
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
            //console.log(data1.metrics)

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
            //console.log(data2.metrics)

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

    //generate batch optimization cutoff (predelat na button pro obecne analyzy batche)
    $('#button_analyze').click(function () {
        analyze_optimal_cutoff();
    });

    //generate report button
    $('#button_report').click(function () {
        rows = archiveRecords.rows('.selected');
        if (rows == undefined) {
            return
        }
        $('#button_report').attr('disabled','disabled');
        runnerIds = []
        if(rows.data().length > 0 ) {
            // Loop through the selected rows and display an alert with each row's ID
            rows.every(function (rowIdx, tableLoop, rowLoop ) {
                var data = this.data()
                runnerIds.push(data.id);
            });
        }
        $.ajax({
            url:"/archived_runners/generatereportimage",
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-API-Key',
                    API_KEY); },
            method:"POST",
            xhrFields: {
                responseType: 'blob'
            },
            contentType: "application/json",
            processData: false,
            data: JSON.stringify(runnerIds),
            success:function(blob){		
                var url = window.URL || window.webkitURL;
                console.log("vraceny obraz", blob)
                console.log("url",url.createObjectURL(blob))
                display_image(url.createObjectURL(blob))
                $('#button_report').attr('disabled',false);
            },
            error: function(xhr, status, error) {
                console.log("proc to skace do erroru?")
                //window.alert(JSON.stringify(xhr));
                console.log(JSON.stringify(xhr));
                $('#button_report').attr('disabled',false);             
            }
        })
    });

    //button to query log
    $('#logRefreshButton').click(function () {
        refresh_logfile()
    });

    $('#logFileSelect').change(function() {
        refresh_logfile();
    });

    //button to open log modal
    $('#button_show_log').click(function () {
        window.$('#logModal').modal('show');
        refresh_logfile()
    });

    //delete batch button - open modal - DECOMISS - dostupne jen na batche
    // $('#button_delete_batch').click(function () {
    //     row = archiveRecords.row('.selected').data();
    //     if (row == undefined || row.batch_id == undefined) {
    //         return
    //     }
    //     $('#batch_id_del').val(row.batch_id);

    //     rows = archiveRecords.rows('.selected');
    //     if (rows == undefined) {
    //         return
    //     }
    //     $('#listofids').html("");
    //     window.$('#delModalBatch').modal('show');
    // });


    //delete batch submit modal
    $("#delModalBatch").on('submit','#delFormBatch', delete_batch);

    //delete arch button - open modal
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
        refresh_arch_and_callback(row, get_detail_and_chart)
    });

    //run again button
    $('#button_runagain_arch').click(run_day_again)

    //run in bt mode
    $('#button_runbt_arch').click(function() {
        run_day_again(true);
      });

    //workaround pro spatne oznacovani selectu i pro group-headery
    // $('#archiveTable tbody').on('click', 'tr.group-header', function(event) {
    // var $row = $(this);

    // // Schedule the class removal/addition for the next event loop
    // setTimeout(function() {
    //     if ($row.hasClass("selected")) {
    //         console.log("Header selected, removing selection");
    //         $row.removeClass("selected");
    //     } 
    // }, 0);
    // });

    // Expand/Collapse functionality
    $('#archiveTable tbody').on('click', 'tr.group-header', expand_collapse_rows);

})
        