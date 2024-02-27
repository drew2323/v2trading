var runmanagerRecords = null

//ekvivalent to ready
function initialize_runmanagerRecords() {

    //archive table
    runmanagerRecords = 
        $('#runmanagerTable').DataTable( {
            ajax: { 
                url: '/run_manager_records/',
                dataSrc: '',
                method:"GET",
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
            columns: [  { data: 'id' },
                        { data: 'moddus' },
                        { data: 'strat_id' },
                        {data: 'symbol'},
                        {data: 'account'},
                        {data: 'mode'},
                        {data: 'note'},
                        {data: 'ilog_save'},
                        {data: 'bt_from'},
                        {data: 'bt_to'},
                        {data: 'weekdays_filter', visible: true},
                        {data: 'batch_id', visible: true},
                        {data: 'start_time', visible: true},
                        {data: 'stop_time', visible: true},
                        {data: 'status'},
                        {data: 'last_processed', visible: true},
                        {data: 'history', visible: false},
                        {data: 'valid_from', visible: true},
                        {data: 'valid_to', visible: true},
                        {data: 'testlist_id', visible: true},
                        {data: 'strat_running', visible: true},
                        {data: 'runner_id', visible: true},                  
                    ],
            paging: true,
            processing: true,
            serverSide: false,
            columnDefs: [
                {   //history
                    targets: [6],
                    render: function(data, type, row, meta) {
                        if (!data) return data;
                        var stateClass = 'truncated-text';
                        var uniqueId = 'note-' + row.id;
        
                        if (localStorage.getItem(uniqueId) === 'expanded') {
                            stateClass = 'expanded-text';
                        }
        
                        if (type === 'display') {
                            return '<div class="' + stateClass + '" id="' + uniqueId + '">' + data + '</div>';
                        }
                        return data;
                    },
                },
                {   //iloc_save
                    targets: [7],
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
                    targets: [10], //weekdays
                    render: function (data, type, row) {
                        if (!data) return data;
                        // Map each number in the array to a weekday
                        var weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"];
                        return data.map(function(dayNumber) {
                            return weekdays[dayNumber];
                        }).join(', ');
                    },
                },
                {
                    targets: [0, 21], //interni id, runner_id
                    render: function ( data, type, row ) {
                        if (!data) return data;
                        if (type === 'display') {
                            return '<div class="tdnowrap" data-bs-toggle="tooltip" data-bs-placement="top" title="'+data+'">'+data+'</div>';
                        }
                        return data;
                    },
                },
                {
                    targets: [2], //strat_id
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
                    targets: [3,12,13], //symbol, start_time, stop_time
                    render: function ( data, type, row ) {
                        if (type === 'display') {
                            //console.log("arch")
                            var color = getColorForId(row.strat_id);
                            return '<span style="color:' + color + ';">'+data+'</span>';
                        }
                        return data;
                    },
                },
                {
                    targets: [16], //history
                    render: function ( data, type, row ) {
                        if (type === 'display') {
                            if (!data) data = "";
                            return '<div data-bs-toggle="tooltip" data-bs-placement="top" title="'+data+'">'+data+'</div>';
                        }
                        return data;
                    },
                },
                {
                    targets: [14], //status
                    render: function ( data, type, row ) {
                        if (type === 'display') {
                            //console.log("arch")
                            var color = data == "active" ? "#3f953f" : "#f84c4c";
                            return '<span style="color:' + color + ';">'+data+'</span>';
                        }
                        return data;
                    },
                },
                {
                    targets: [20], //strat_running
                    render: function ( data, type, row ) {
                        if (type === 'display') {
                            if (!data) data = "";
                            console.log("running", data)
                            //var color = data == "active" ? "#3f953f" : "#f84c4c";
                            data = data ? "running" : ""
                            return '<div title="' + row.runner_id + '" style="color:#3f953f;">'+data+'</div>';
                        }
                        return data;
                    },
                },
                // {
                // targets: [0,17],
                // render: function ( data, type, row ) {
                //     if (!data) return data
                //     return '<div class="tdnowrap" title="'+data+'">'+data+'</i>'
                // },
                // },
                {   
                    targets: [15,17, 18, 8, 9], //start, stop, valid_from, valid_to, bt_from, bt_to, last_proccessed
                    render: function ( data, type, row ) {
                        if (!data) return data
                        if (type == "sort") {
                            return new Date(data).getTime();
                        }
                        var date = new Date(data);
                        tit = date.toLocaleString('cs-CZ', {
                                timeZone: 'America/New_York',
                            })
                        return '<div title="'+tit+'">'+ format_date(data,true,false)+'</div>'
                        // if (isToday(now)) {
                        //     //return local time only
                        //     return '<div title="'+tit+'">'+ 'dnes ' + format_date(data,true,true)+'</div>'
                        // }
                        // else
                        // {
                        //     //return  local datetime
                        //     return '<div title="'+tit+'">'+ format_date(data,true,false)+'</div>'
                        // }
                    },
                    },
                    // {
                    //     targets: [6],
                    //     render: function ( data, type, row ) {
                    //         now = new Date(data)
                    //         if (type == "sort") {
                    //             return new Date(data).getTime();
                    //         }
                    //         var date = new Date(data);
                    //         tit = date.toLocaleString('cs-CZ', {
                    //                 timeZone: 'America/New_York',
                    //             })
        
                    //         if (isToday(now)) {
                    //             //return local time only
                    //             return '<div title="'+tit+'" class="token level comment">'+ 'dnes ' + format_date(data,false,true)+'</div>'
                    //         }
                    //         else
                    //         {
                    //             //return  local datetime
                    //             return '<div title="'+tit+'" class="token level number">'+ format_date(data,false,false)+'</div>'
                    //         }
                    //     },
                    //     },
                    // {
                    // targets: [9,10],
                    // render: function ( data, type, row ) {
                    //     if (type == "sort") {
                    //         return new Date(data).getTime();
                    //     }
                    //     //console.log(data)
                    //     //market datetime
                    //     return data ? format_date(data, true) : data
                    // },
                    // },
                    // {
                    //     targets: [2],
                    //     render: function ( data, type, row ) {
                    //         return '<div class="tdname tdnowrap" title="'+data+'">'+data+'</div>'
                    //     },
                    // },
                    // // {
                    // //     targets: [4],
                    // //     render: function ( data, type, row ) {
                    // //         return '<div class="tdname tdnowrap" title="'+data+'">'+data+'</div>'
                    // //     },
                    // // },
                    // {
                    //     targets: [16],
                    //     render: function ( data, type, row ) {
                    //         //console.log("metrics", data)
                    //         try {
                    //             data = JSON.parse(data)
                    //         }
                    //         catch (error) {
                    //             //console.log(error)
                    //         }
                    //         var res = JSON.stringify(data)
                    //         var unquoted = res.replace(/"([^"]+)":/g, '$1:')

                    //         //zobrazujeme jen kratkou summary pokud mame, jinak davame vse, do titlu davame vzdy vse
                    //         //console.log(data)
                    //         short = null
                    //         if ((data) && (data.profit) && (data.profit.sum)) {
                    //             short = data.profit.sum
                    //         }
                    //         else {
                    //             short = unquoted
                    //         }
                    //         return '<div class="tdmetrics" title="'+unquoted+'">'+short+'</div>'
                    //     },
                    // },
                    // {
                    //     targets: [4],
                    //     render: function ( data, type, row ) {
                    //         return '<div class="tdnote" title="'+data+'">'+data+'</div>'
                    //     },
                    // },
                    // {
                    //     targets: [13,14,15],
                    //     render: function ( data, type, row ) {
                    //         return '<div class="tdsmall">'+data+'</div>'
                    //     },
                    // },
                    // {
                    //     targets: [11],
                    //     render: function ( data, type, row ) {
                    //         //if ilog_save true
                    //         if (data) {
                    //             return '<span class="material-symbols-outlined">done_outline</span>'
                    //         }
                    //         else {
                    //             return null
                    //         }
                    //     },
                    // },
                    {
                        targets: [4], //account
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
                        targets: [5], //mode
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
            order: [[1, 'asc']],
            select: {
                info: true,
                style: 'multi',
                //selector: 'tbody > tr:not(.group-header)'
                selector: 'tbody > tr:not(.group-header)' 
            },
            paging: true
    });

}