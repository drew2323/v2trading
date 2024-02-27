var archiveRecords = null

//ekvivalent to ready
function initialize_archiveRecords() {

    //archive table
    archiveRecords = 
        $('#archiveTable').DataTable( {
            ajax: { 
                url: '/archived_runners_p/',
                dataSrc: 'data',
                method:"POST",
                contentType: "application/json",
                // dataType: "json",
                beforeSend: function (xhr) {
                    xhr.setRequestHeader('X-API-Key',
                        API_KEY); },
                data: function (d) {
                            return JSON.stringify(d);
                        },       
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
                        {data: 'batch_profit', visible: false},
                        {data: 'batch_count', visible: false},
                    ],
            paging: true,
            processing: true,
            serverSide: true,
            columnDefs: [
                {
                    targets: 1,
                    render: function ( data, type, row ) {
                        if (type === 'display') {
                            //console.log("arch")
                            var color = getColorForId(data);
                            return '<div class="tdnowrap" data-bs-toggle="tooltip" data-bs-placement="top" title="'+data+'"><span class="color-tag" style="background-color:' + color + ';"></span>'+data+'</div>';
                        }
                        return data;
                    },
                },
                {
                targets: [0,17],
                render: function ( data, type, row ) {
                    if (!data) return data
                    return '<div class="tdnowrap" title="'+data+'">'+data+'</i>'
                },
                },
                {
                    targets: [5],
                    render: function ( data, type, row ) {
                        if (type == "sort") {
                            return new Date(data).getTime();
                        }
                        //data = "2024-02-26T19:29:13.400621-05:00"
                        // Create a date object from the string, represents given moment in time in UTC time
                        var date = new Date(data);
            
                        tit = date.toLocaleString('cs-CZ', {
                                timeZone: 'America/New_York',
                            })

                        if (isToday(date)) {
                            //console.log("volame isToday s", date)
                            //return local time only
                            return '<div title="'+tit+'">'+ 'dnes ' + format_date(data,true,true)+'</div>'
                        }
                        else
                        {
                            //return  local datetime
                            return '<div title="'+tit+'">'+ format_date(data,true,false)+'</div>'
                        }
                    },
                    },
                    {
                        targets: [6],
                        render: function ( data, type, row ) {
                            if (type == "sort") {
                                return new Date(data).getTime();
                            }
                            var date = new Date(data);
                            tit = date.toLocaleString('cs-CZ', {
                                    timeZone: 'America/New_York',
                                })
        
                            if (isToday(date)) {
                                //return local time only
                                return '<div title="'+tit+'" class="token level comment">'+ 'dnes ' + format_date(data,true,true)+'</div>'
                            }
                            else
                            {
                                //return  local datetime
                                return '<div title="'+tit+'" class="token level number">'+ format_date(data,true,false)+'</div>'
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
                info: true,
                style: 'multi',
                //selector: 'tbody > tr:not(.group-header)'
                selector: 'tbody > tr:not(.group-header)' 
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
            // Add row grouping based on 'batch_id'
            //TODO projit a zrevidovat - pripadne optimalizovat 
            //NOTE zde jse skoncil
            rowGroup: {
                dataSrc: 'batch_id',
                //toto je volano pri renderovani headeru grupy
                startRender: function (rows, group) {
                    var firstRowData = rows.data()[0];
                    //pro no-batch-id je idcko prvni id
                    var groupId = group ? group : 'no-batch-id-' + firstRowData.id;
                    var stateKey = 'dt-group-state-' + groupId;
                    var state = localStorage.getItem(stateKey);
                    var profit = firstRowData.batch_profit
                    var itemCount = firstRowData.batch_count

                    // Iterate over each row in the group to set the data attribute
                    // zaroven pro kazdy node nastavime viditelnost podle nastaveni
                    rows.every(function (rowIdx, tableLoop, rowLoop) {
                        var rowNode = $(this.node());
                        rowNode.attr('data-group-name', groupId);
                        //defaultne jsou batche zabalene a nobatche rozbalene, pokud nenastavim jinak
                        if (state == 'collapsed' || (!state) && group) {
                            rowNode.hide();
                        } else {
                            rowNode.show();
                        }
                    });

                    // Initialize variables for the group
                    //var itemCount = 0;
                    var period = '';
                    var batch_note = '';
                    //var profit = '';
                    var started = null;
                    var stratinId = null;
                    var symbol = null;

                    // // Process each item only once
                    // archiveRecords.rows({ search: 'applied' }).every(function (rowIdx, tableLoop, rowLoop) {
                    //     var data = this.data();
            
                    //     if ((group && data.batch_id == group)) {
                    //         itemCount++;
                    //         if (itemCount === 1 ) {
                    //             firstNote = data.note ? data.note.substring(0, 14) : '';

                    //             if (data.note) {
                    //                 better_counter = extractNumbersFromString(data.note);
                    //             }
                    //             try {
                    //                 profit = data.metrics.profit.batch_sum_profit;
                    //             } catch (e) {
                    //                 profit = 'N/A';
                    //             }
                    //         }
                    //     }
                    // });                


                    //pokud mame batch_id podivame se zda jeho nastaveni uz nema a pokud ano pouzijeme to
                    //pokud nemame tak si ho loadneme
                    //Tento kod parsuje informace do header hlavicky podle notes, je to relevantni pouze pro
                    //backtest batche, nikoliv pro paper a live, kde pocet dni je neznamy a poznamka se muze menit
                    //do budoucna tento parsing na frontendu bude nahrazen batch tabulkou v db, ktera persistuje
                    //tyto data
                    if (group) {
                        const existingBatch = batchHeaders.find(batch => batch.batch_id == group);
                        //jeste neni v poli batchu - udelame hlavicku
                        if (!existingBatch) {
                            // itemCount = extractNumbersFromString(firstRowData.note);
                            // if (!itemCount) {
                            //     itemCount="NA"
                            // }
                
                            // try { profit = firstRowData.metrics.profit.batch_sum_profit;}
                            // catch (e) {profit = 'NA'}
                            
                            // if (!profit) {profit = 'NA'}
                            period = firstRowData.note ? firstRowData.note.substring(0, 14) : '';
                            try {
                            batch_note = firstRowData.note ? firstRowData.note.split("N:")[1].trim() : ''
                            } catch (e) { batch_note = ''}
                            started = firstRowData.started
                            stratinId = firstRowData.strat_id
                            symbol = firstRowData.symbol
                            if (period.startsWith("SCHED")) {
                                period = "SCHEDULER";
                              }
                            var newBatchHeader = {batch_id:group, batch_note:batch_note, profit:profit, itemCount:itemCount, period:period, started:started, stratinId:stratinId, symbol:symbol};
                            batchHeaders.push(newBatchHeader)
                        }
                        //uz je v poli, ale mame novejsi (pribyl v ramci backtestu napr.) - updatujeme
                        else if (new Date(existingBatch.started) < new Date(firstRowData.started)) {
                            // try {itemCount = extractNumbersFromString(firstRowData.note);}
                            // catch (e) {itemCount = 'NA'}
                            // try {profit = firstRowData.metrics.profit.batch_sum_profit;}
                            // catch (e) {profit = 'NA'}
                            period = firstRowData.note ? firstRowData.note.substring(0, 14) : '';
                            if (period.startsWith("SCHED")) {
                                period = "SCHEDULER";
                              }
                            try {
                                batch_note = firstRowData.note ? firstRowData.note.split("N:")[1].trim() : ''
                                } catch (e) { batch_note = ''}
                            started = firstRowData.started
                            stratinId = firstRowData.strat_id
                            symbol = firstRowData.symbol
                            existingBatch.itemCount = itemCount;
                            existingBatch.profit = profit;
                            existingBatch.period = period;
                            existingBatch.started = started;
                            existingBatch.batch_note = batch_note
                        }
                        //uz je v poli batchu vytahneme
                        else {
                            profit = existingBatch.profit
                            itemCount = existingBatch.itemCount
                            period = existingBatch.period
                            started = existingBatch.started
                            stratinId = existingBatch.stratinId
                            symbol = existingBatch.symbol
                            batch_note = existingBatch.batch_note
                        }
                    }

                    //zaroven nastavime u vsech childu

                    // Construct the GROUP HEADER - sem pripadna tlačítka atp.
                    //var groupHeaderContent = '<strong>' + (group ? 'Batch ID: ' + group : 'No Batch') + '</strong>';
                    var tools = ''
                    var icon = ''
                    icon_color = ''
                    profit_icon_color = ''
                    exp_coll_icon_name = ''
                    exp_coll_icon_name = (state == 'collapsed') ? 'expand_more' : 'expand_less'
                    if (group) {
                        tools = '<span class="batchtool">'
                        tools += '<span id="batchtool_report_button" class="material-symbols-outlined tool-icon" title="Batch Report">lab_profile</span>'
                        tools += '<span id="batchtool_delete_button" class="material-symbols-outlined tool-icon" title="Delete Batch">delete</span>'
                        tools += '<span id="batchtool_exportcsv_button" class="material-symbols-outlined tool-icon" title="Export batch to csv">csv</span>'
                        tools += '<span id="batchtool_exportxml_button" class="material-symbols-outlined tool-icon" title="Export batch to xml">insert_drive_file</span>'
                        tools += '<span id="batchtool_cutoff_button" class="material-symbols-outlined tool-icon" title="Cutoff heatmap for batch">cut</span>'                    
                        //dynamic button placeholder
                        //tools += '<div class="dropdown"><button class="btn btn-outline-success btn-sm dropdown-toggle" type="button" id="actionDropdown" data-bs-toggle="dropdown" aria-expanded="false">Choose analyzer</button><ul class="dropdown-menu dropdown-menu-dark" aria-labelledby="actionDropdown"></ul></div>'
                        tools += '<div class="batch_buttons_container" id="bb'+group+'" data-batch-id="'+group+'"></div>'

                        //final closure
                        tools += '</span>'
                        icon_color = getColorForId(stratinId)
                        profit_icon_color = (profit>0) ? "#4f8966" : "#bb2f5e" //"#d42962"  
                    }
                    else {
                        //def color for no batch - semi transparent
                        icon_color = "#ced4da17"
                    }
                    icon = '<span class="material-symbols-outlined expand-icon" style="background-color:' + icon_color + ';" title="Expand">'+exp_coll_icon_name+'</span>'

                    //console.log(group, groupId, stratinId)
                    //var groupHeaderContent = '<span class="batchheader-batch-id">'+(group ? '<span class="color-tag" style="background-color:' + getColorForId(stratinId) + ';"></span>Batch ID: ' + group: 'No Batch')+'</span>';
                    var groupHeaderContent = '<span class="batchheader-batch-id">'+ icon + (group ? 'Batch ID: ' + group: 'No Batch')+'</span>';
                    groupHeaderContent += (group ? '<span class="batchheader-symbol-info" style="color:'+icon_color+'">' + symbol + '</span><span class="batchheader-count-info">(' + itemCount + ')</span>' + '  <span class="batchheader-period-info">' + period + '</span>   <span class="batchheader-profit-info" style="color:'+profit_icon_color+'">Profit: ' + profit + '</span>'  : '');
                    groupHeaderContent += group ? tools : ""
                    groupHeaderContent += group ? '<span class="batchheader-note-info">' + batch_note + '</span>' : ''
                    return $('<tr/>')
                        .append('<td colspan="18">' + groupHeaderContent + '</td>')
                        .attr('data-name', groupId)
                        .addClass('group-header')
                        .addClass(state);
                }
            },
            lengthMenu: [ [10, 50, 200, 500, -1], [10, 50, 200, 500, "All"] ],
            drawCallback: function (settings) {
                //console.log("drawcallback", configData)
                setTimeout(function(){ 
    
                    //populate all tool buttons on batch header
                    // Loop over all divs with the class 'batch-buttons-container'
                    if (configData["dynamic_buttons"]) {
                            //console.log("jsme tu po cekani")
                            //console.log("pred loopem")
                            $('.batch_buttons_container').each((index, element) => {
                                //console.log("jsme uvnitr foreach");
                                idecko = $(element).attr('id')
                                //console.log("idecko", idecko)
                                var batchId = $(element).data('batch-id'); // Get the data-batch-id attribute
                                //console.log("nalezeno pred", batchId, $(element));
                                populate_dynamic_buttons($(element), configData["dynamic_buttons"], batchId);
                                //console.log("po", $(element));
                            });
                    }else {
                        console.log("no dynamic_buttons configuration loaded")
                    }
                }, 1);  
                // var api = this.api();
                // var rows = api.rows({ page: 'current' }).nodes();
                    
                // api.column(17, { page: 'current' }).data().each(function (group, i) {
                //     console.log("drawCallabck i",i)
                //     console.log("rows", $(rows).eq(i))
                //     var groupName = group ? group : $(rows).eq(i).attr('data-name');
                //     console.log("groupName", groupName)
                //     var stateKey = 'dt-group-state-' + groupName;
                //     var state = localStorage.getItem(stateKey);
            
                //     if (state === 'collapsed') {
                //         $(rows).eq(i).hide();
                //     } else {
                //         $(rows).eq(i).show();
                //     }
                    
                    // Set the unique identifier as a data attribute on each row
                    //$(rows).eq(i).attr('data-group-name', groupName);
            
                    // // Add or remove the 'collapsed' class based on the state
                    // if (groupName.startsWith('no-batch-id-')) {
                    //     $('tr[data-name="' + groupName + '"]').toggleClass('collapsed', state === 'collapsed');
                    // }
                // });
            }
    });

}