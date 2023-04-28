
API_KEY = localStorage.getItem("api-key")
var chart = null
//Date.prototype.toJSON = function(){ return Date.parse(this)/1000 }

// safely handles circular references https://stackoverflow.com/questions/11616630/how-can-i-print-a-circular-structure-in-a-json-like-format
JSON.safeStringify = (obj, indent = 2) => {
    let cache = [];
    const retVal = JSON.stringify(
      obj,
      (key, value) =>
        typeof value === "object" && value !== null
          ? cache.includes(value)
            ? undefined // Duplicate reference found, discard key
            : cache.push(value) && value // Store value in our collection
          : value,
      indent
    );
    cache = null;
    return retVal;
  };

// Iterate through each element in the
// first array and if some of them
// include the elements in the second
// array then return true.
function findCommonElements3(arr1, arr2) {
return arr1.some(item => arr2.includes(item))
}

function set_timestamp(timestamp) {
    //console.log(timestamp);
    $('#trade-timestamp').val(timestamp);
}

//KEY shortcuts
Mousetrap.bind('e', function() { 
    $( "#button_edit" ).trigger( "click" );
});
Mousetrap.bind('a', function() { 
    $( "#button_add" ).trigger( "click" );
});
Mousetrap.bind('d', function() { 
    $( "#button_dup" ).trigger( "click" );
});
Mousetrap.bind('c', function() { 
    $( "#button_copy" ).trigger( "click" );
});
Mousetrap.bind('r', function() { 
    $( "#button_run" ).trigger( "click" );
});
Mousetrap.bind('p', function() { 
    $( "#button_pause" ).trigger( "click" );
});
Mousetrap.bind('s', function() { 
    $( "#button_stop" ).trigger( "click" );
});
Mousetrap.bind('j', function() { 
    $( "#button_add_json" ).trigger( "click" );
});
Mousetrap.bind('x', function() { 
    $( "#button_delete" ).trigger( "click" );
});

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

var tradeDetails = new Map();
//CHART ARCHIVED RUN - move to own file
//input array object bars = { high: [1,2,3], time: [1,2,3], close: [2,2,2]...}
//output array [{ time: 111, open: 11, high: 33, low: 333, close: 333},..]
function transform_data(data) {
    transformed = []
    //get basic bars, volume and vvwap
    var bars = []
    var volume = []
    var vwap = []
    data.bars.time.forEach((element, index, array) => {
        sbars = {};
        svolume = {};
        svwap = {};

        sbars["time"] = element;
        sbars["close"] = data.bars.close[index]
        sbars["open"] = data.bars.open[index]
        sbars["high"] = data.bars.high[index]
        sbars["low"] = data.bars.low[index]


        svwap["time"] = element
        svwap["value"] = data.bars.vwap[index]

        svolume["time"] = element
        svolume["value"] = data.bars.volume[index]

        bars.push(sbars)
        vwap.push(svwap)
        volume.push(svolume)
    });
    transformed["bars"] = bars
    transformed["vwap"] = vwap
    transformed["volume"] = volume

    //get markers - avgp line for all buys
    var avgp_buy_line = []
    var avgp_markers = []
    var markers = []
    var markers_line = []
    data.trades.forEach((trade, index, array) => {
        obj = {};
        a_markers = {}
        timestamp = Date.parse(trade.order.filled_at)/1000
        if (trade.order.side == "buy") {
            //line pro avgp markers
            obj["time"] = timestamp;
            obj["value"] = trade.pos_avg_price;
            avgp_buy_line.push(obj)

            //avgp markers pro prumernou cenu aktualnich pozic
            a_markers["time"] = timestamp
            a_markers["position"] = "aboveBar"
            a_markers["color"] = "#e8c76d"
            a_markers["shape"] = "arrowDown"
            a_markers["text"] = trade.position_qty + " " + parseFloat(trade.pos_avg_price).toFixed(3)
            avgp_markers.push(a_markers)
        }

        //buy sell markery
        marker = {}
        marker["time"] = timestamp;
        // marker["position"] = (trade.order.side == "buy") ? "belowBar" : "aboveBar" 
        marker["position"] = (trade.order.side == "buy") ? "inBar" : "aboveBar" 
        marker["color"] = (trade.order.side == "buy") ? "blue" : "red"
        //marker["shape"] = (trade.order.side == "buy") ? "arrowUp" : "arrowDown"
        marker["shape"] = (trade.order.side == "buy") ? "circle" : "arrowDown"
        marker["text"] =  trade.qty + " " + trade.price
        markers.push(marker)

        //prevedeme iso data na timestampy
        trade.order.submitted_at = Date.parse(trade.order.submitted_at)/1000
        trade.order.filled_at = Date.parse(trade.order.filled_at)/1000
        trade.timestamp = Date.parse(trade.order.timestamp)/1000
        tradeDetails.set(timestamp, trade)

        //line pro buy/sell markery
        mline = {}
        mline["time"] = timestamp
        mline["value"] = trade.price
        markers_line.push(mline)

    // time: datesForMarkers[i].time,
    // position: 'aboveBar',
    // color: '#e91e63',
    // shape: 'arrowDown',
    // text: 'Sell @ ' + Math.floor(datesForMarkers[i].high + 2),
        
        
    });
    transformed["avgp_buy_line"] = avgp_buy_line 
    transformed["markers"] = markers
    transformed["markers_line"] = markers_line
    transformed["avgp_markers"] = avgp_markers
    //get additional indicators
    //TBD
    return transformed
}

function chart_archived_run(data) {
    if (chart !== null) {
        chart.remove()
    }

    //console.log("inside")
    var transformed_data = transform_data(data)
    //console.log(transformed_data)
    //tbd transform indicators
    //var markersData = transform_trades(data)

    // time: datesForMarkers[i].time,
    // position: 'aboveBar',
    // color: '#e91e63',
    // shape: 'arrowDown',
    // text: 'Sell @ ' + Math.floor(datesForMarkers[i].high + 2),
    document.getElementById("chart").style.display = "block"
    //initialize chart
    var chartOptions = { width: 1300, height: 600, leftPriceScale: {visible: true}}
    chart = LightweightCharts.createChart(document.getElementById('chart'), chartOptions);
    chart.applyOptions({ timeScale: { visible: true, timeVisible: true, secondsVisible: true }, crosshair: {
        mode: LightweightCharts.CrosshairMode.Normal, labelVisible: true
    }})
    var archCandlestickSeries = chart.addCandlestickSeries({ lastValueVisible: true, priceLineWidth:2, priceLineColor: "red", priceFormat: { type: 'price', precision: 2, minMove: 0.01 }});
    archCandlestickSeries.priceScale().applyOptions({
        scaleMargins: {
            top: 0.1, // highest point of the series will be 10% away from the top
            bottom: 0.4, // lowest point will be 40% away from the bottom
        },
    });

    var archVwapSeries = chart.addLineSeries({
        //    title: "vwap",
            color: '#2962FF',
            lineWidth: 1,
            lastValueVisible: false
        });

    var archVolumeSeries = chart.addHistogramSeries({title: "Volume", color: '#26a69a', priceFormat: {type: 'volume'}, priceScaleId: ''});
    archVolumeSeries.priceScale().applyOptions({
        // set the positioning of the volume series
        scaleMargins: {
            top: 0.7, // highest point of the series will be 70% away from the top
            bottom: 0,
        },
    });
    
    archVwapSeries.setData(transformed_data["vwap"])
    archCandlestickSeries.setData(transformed_data["bars"])
    archVolumeSeries.setData(transformed_data["volume"])


    var avgBuyLine = chart.addLineSeries({
        //    title: "avgpbuyline",
            color: '#e8c76d',
        //    color: 'transparent',
            lineWidth: 1,
            lastValueVisible: false
        });

    avgBuyLine.setData(transformed_data["avgp_buy_line"]);

    avgBuyLine.setMarkers(transformed_data["avgp_markers"])

    var markersLine = chart.addLineSeries({
          //  title: "avgpbuyline",
          //  color: '#d6d1c3',
            color: 'transparent',
            lineWidth: 1,
            lastValueVisible: false
        });

    markersLine.setData(transformed_data["markers_line"]);

    //console.log("markers")
    //console.log(transformed_data["markers"])

    markersLine.setMarkers(transformed_data["markers"])



    //TBD dynamicky
    //pokud je nazev atributu X_candles vytvorit candles
    //pokud je objekt Y_line pak vytvorit lajnu
    //pokud je objekt Z_markers pak vytvorit markers
        //pokud je Z = X nebo Y, pak markers dat na danou lajnu (priklad vvwap_line, avgp_line, avgp_markers)
    //udelat si nahodny vyber barev z listu

        //DO BUDOUCNA MARKERS
    // chart.subscribeCrosshairMove(param => {
    //     console.log(param.hoveredObjectId);
    // });
    

    //define tooltip
    const container1 = document.getElementById('chart');

    const toolTipWidth = 90;
    const toolTipHeight = 90;
    const toolTipMargin = 15;
    
    // Create and style the tooltip html element
    const toolTip = document.createElement('div');
    //width: 90px; , height: 80px; 
    toolTip.style = `position: absolute; display: none; padding: 8px; box-sizing: border-box; font-size: 12px; text-align: left; z-index: 1000; top: 12px; left: 12px; pointer-events: none; border: 1px solid; border-radius: 2px;font-family: -apple-system, BlinkMacSystemFont, 'Trebuchet MS', Roboto, Ubuntu, sans-serif; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;`;
    toolTip.style.background = 'white';
    toolTip.style.color = 'black';
    toolTip.style.borderColor = '#2962FF';
    container1.appendChild(toolTip);


    //TODO onlick zkopirovat timestamp param.time
    // chart.subscribeClick(param => {
    //     $('#trade-timestamp').val(param.time)
    //     //alert(JSON.safeStringify(param))
    //     //console.log(param.hoveredObjectId);
    // });

    //chart.subscribeCrosshairMove(param => {

    chart.subscribeClick(param => {
        $('#trade-timestamp').val(param.time)
        if (
            param.point === undefined ||
            !param.time ||
            param.point.x < 0 ||
            param.point.x > container1.clientWidth ||
            param.point.y < 0 ||
            param.point.y > container1.clientHeight
        ) {
            toolTip.style.display = 'none';
        } else {
            //vyber serie s jakou chci pracovat - muzu i dynamicky
            //je to mapa https://tradingview.github.io/lightweight-charts/docs/api/interfaces/MouseEventParams

            //key = series (key.seriestype vraci Line/Candlestick atp.)  https://tradingview.github.io/lightweight-charts/docs/api/interfaces/SeriesOptionsMap

            toolTip.style.display = 'none';
            toolTip.innerHTML = "";
            var data = param.seriesData.get(markersLine);
            if (data !== undefined) {
            //param.seriesData.forEach((value, key) => {
                //console.log("key",key)
                //console.log("value",value)
               
                //data = value
                //DOCASNE VYPNUTO
                toolTip.style.display = 'block';
                
                //console.log(JSON.safeStringify(key))
                if (toolTip.innerHTML == "") {
                    toolTip.innerHTML = `<div>${param.time}</div>`
                }
                var price = data.value
                // !== undefined ? data.value : data.close;


                toolTip.innerHTML += `<pre>${JSON.stringify(tradeDetails.get(param.time),null,2)}</pre><div>${price.toFixed(3)}</div>`;

                //inspirace
                // toolTip.innerHTML = `<div style="color: ${'#2962FF'}">Apple Inc.</div><div style="font-size: 24px; margin: 4px 0px; color: ${'black'}">
                // ${Math.round(100 * price) / 100}
                // </div><div style="color: ${'black'}">
                // ${dateStr}
                // </div>`;


                // Position tooltip according to mouse cursor position
                toolTip.style.left = param.point.x+120 + 'px';
                toolTip.style.top = param.point.y-100 + 'px';
            }
                //});
        }
    });




    chart.timeScale().fitContent();
    
    //TBD other dynamically created indicators

}



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
                //$('#chartArchive').append(JSON.stringify(data,null,2));
                console.log(JSON.stringify(data,null,2));
                chart_archived_run(data);
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


//https://www.w3schools.com/jsref/jsref_tolocalestring.asp
function format_date(datum) {
    //const options = { weekday: 'long', year: 'numeric', month: 'numeric', day: 'numeric', };
    const options = {dateStyle: "short", timeStyle: "short"}
    const date = new Date(datum);
    return date.toLocaleString('cs-CZ', options);
}

//stratin table
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
            targets: [3,4,7,8],
            render: function ( data, type, row ) {
                return format_date(data)
            },
            }],
        order: [[4, 'desc']],
        paging: true,
        lengthChange: false,
        // createdRow: function( row, data, dataIndex){
        //     if (is_running(data.id) ){
        //         alert("runner");
        //         $(row).addClass('highlight');
        //     }
        //}
        } );

//STRATIN and RUNNERS TABELS
$(document).ready(function () {
    //reaload hlavni tabulky

    stratinRecords.ajax.reload();
    runnerRecords.ajax.reload();

    $('#trade-timestamp').val(localStorage.getItem("trade_timestamp"));
    $('#trade-count').val(localStorage.getItem("trade_count"));
    $('#trade-symbol').val(localStorage.getItem("trade_symbol"));
    $('#trade-minsize').val(localStorage.getItem("trade_minsize"));
    $('#trade-filter').val(localStorage.getItem("trade_filter"));


    //disable buttons (enable on row selection)
    $('#button_pause').attr('disabled','disabled');
    $('#button_stop').attr('disabled','disabled');
    $('#button_edit').attr('disabled','disabled');
    $('#button_dup').attr('disabled','disabled');
    $('#button_copy').attr('disabled','disabled');
    $('#button_delete').attr('disabled','disabled');
    $('#button_run').attr('disabled','disabled');

    //selectable rows in stratin table
    $('#stratinTable tbody').on('click', 'tr', function () {
        if ($(this).hasClass('selected')) {
            $(this).removeClass('selected');
            $('#button_dup').attr('disabled','disabled');
            $('#button_copy').attr('disabled','disabled');
            $('#button_edit').attr('disabled','disabled');
            $('#button_delete').attr('disabled','disabled');
            $('#button_run').attr('disabled','disabled');
        } else {
            stratinRecords.$('tr.selected').removeClass('selected');
            $(this).addClass('selected');
            $('#button_dup').attr('disabled',false);
            $('#button_copy').attr('disabled',false);
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


   //button get historical trades
   $('#bt-trade').click(function () {
    event.preventDefault();
    $('#bt-trade').attr('disabled','disabled');
    $( "#trades-data").addClass("in");

    localStorage.setItem("trade_timestamp",$('#trade-timestamp').val());
    localStorage.setItem("trade_count",$('#trade-count').val());
    localStorage.setItem("trade_symbol",$('#trade-symbol').val());
    localStorage.setItem("trade_minsize",$('#trade-minsize').val());
    localStorage.setItem("trade_filter",$('#trade-filter').val());

    const rec = new Object()
    rec.timestamp_from = parseFloat($('#trade-timestamp').val())-parseInt($('#trade-count').val())
    rec.timestamp_to = parseFloat($('#trade-timestamp').val())+parseInt($('#trade-count').val())
    symbol = $('#trade-symbol').val()
    //jsonString = JSON.stringify(rec);
    //alert(JSON.stringify(rec))
    $.ajax({
        url:"/tradehistory/"+symbol+"/",
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-API-Key',
            API_KEY); },
        method:"GET",
        contentType: "application/json",
        dataType: "json",
        data: rec,
        success:function(data){							
            $('#bt-trade').attr('disabled', false);
            $('#trades-data').show();
            //$('#trades-data').text("")
            var minsize = parseInt($('#trade-minsize').val());
            //filter string to filter array
            var valueInserted = $("#trade-filter").val(); // "tag1,tag2,tag3, "two words""
            var filterList = valueInserted.split(",");  // ["tag1", "tag2", "tag3", "two words"]
            for (var i in filterList) {
                filterList[i] = filterList[i].trim();
            }

            console.log("filter list")
            console.log(filterList)
            console.log(minsize)
            var row = ""
            //zakrouhleno na milisekundy
            var puvodni = parseFloat(parseInt(parseFloat($('#trade-timestamp').val())*1000))/1000
            console.log(puvodni)
            $('#trades-data-table').html(row);
            data.forEach((tradeLine) => {
                //console.log(JSON.stringify(tradeLine))
                date = new Date(tradeLine.timestamp)
                timestamp = date.getTime()/1000
                console.log(timestamp)

                //trade contains filtered condition or size<minsize
                bg = (findCommonElements3(filterList, tradeLine.conditions) || (parseInt(tradeLine.size) < minsize) ? 'style="background-color: #e6e6e6;"' : '')

                row += '<tr role="row" '+ ((timestamp == puvodni) ? 'class="highlighted"' : '') +' ' + bg + '><td>' + timestamp + '</td><td>' + tradeLine.price + '</td>' +
                            '<td>' + tradeLine.size + '</td><td>' + tradeLine.id + '</td>' +
                            '<td>' + tradeLine.conditions + '</td><td>' + tradeLine.tape + '</td>' +
                            '<td>' + tradeLine.timestamp + '</td></tr>';
            
            });
            //console.log(row);
            $('#trades-data-table').html(row);
            // $('#trades-data').html(row)
        },
        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            window.alert(JSON.stringify(xhr));
            console.log(JSON.stringify(xhr));
            $('#bt-trade').attr('disabled', false);
        }
    })
});

    //on hover of each logline move timestamp to trade history input field
    //   $('.line').click(function () {
    //     timestamp = $(this).data("timestamp");
    //     console.log(timestamp);
    //     $('#trade-timestamp').val(timestamp);
    // })


    //button refresh
    $('#button_refresh').click(function () {
        runnerRecords.ajax.reload();
        stratinRecords.ajax.reload();
        archiveRecords.ajax.reload();
    })

    //button copy
    $('#button_copy').click(function () {
        event.preventDefault();
        $('#button_copy').attr('disabled','disabled');
        row = stratinRecords.row('.selected').data();
        const rec = new Object()
        rec.id2 = parseInt(row.id2);
        rec.name = row.name;
        rec.symbol = row.symbol;
        rec.class_name = row.class_name;
        rec.script = row.script;
        rec.open_rush = row.open_rush;
        rec.close_rush = row.close_rush;
        rec.stratvars_conf = row.stratvars_conf;
        rec.add_data_conf = row.add_data_conf;
        rec.note = row.note;
        rec.history = "";
        jsonString = JSON.stringify(rec, null, 2);
        navigator.clipboard.writeText(jsonString);
        $('#button_copy').attr('disabled', false);
    })

   //button duplicate
   $('#button_dup').click(function () {
    row = stratinRecords.row('.selected').data();
    event.preventDefault();
    $('#button_dup').attr('disabled','disabled');
    const rec = new Object()
    rec.id2 = parseInt(row.id2) + 1;
    rec.name = row.name + " copy";
    rec.symbol = row.symbol;
    rec.class_name = row.class_name;
    rec.script = row.script;
    rec.open_rush = row.open_rush;
    rec.close_rush = row.close_rush;
    rec.stratvars_conf = row.stratvars_conf;
    rec.add_data_conf = row.add_data_conf;
    rec.note = row.note;
    rec.history = "";
    jsonString = JSON.stringify(rec);
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
            $('#button_dup').attr('disabled', false);
            stratinRecords.ajax.reload();
        },
        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            window.alert(JSON.stringify(xhr));
            console.log(JSON.stringify(xhr));
            $('#button_dup').attr('disabled', false);
        }
    })
});

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
        $('#bt_from').val(localStorage.getItem("bt_from"));
        $('#bt_to').val(localStorage.getItem("bt_to"));
        $('#mode').val(localStorage.getItem("mode"));
        $('#account').val(localStorage.getItem("account"));
        $('#debug').val(localStorage.getItem("debug"));
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
        $('#action').val('delRecord');
        $('#save').val('Delete');

    });
    //json add button
    $('#button_add_json').click(function () {
        window.$('#jsonModal').modal('show');
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
        order: [[1, 'asc']],
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
    localStorage.setItem("bt_from", $('#bt_from').val());
    localStorage.setItem("bt_to", $('#bt_to').val());
    localStorage.setItem("mode", $('#mode').val());
    localStorage.setItem("account", $('#account').val());
    localStorage.setItem("debug", $('#debug').val());
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
            //pokud mame subscribnuto na RT                
            if ($('#subscribe').prop('checked')) {
                //subscribe input value gets id of current runner
                $('#runnerId').val($('#runid').val());
                $( "#bt-conn" ).trigger( "click" );
            }				
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
        //code for edit
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

//add json modal
$("#jsonModal").on('submit','#jsonForm', function(event){
    event.preventDefault();
    $('#json_add').attr('disabled','disabled');
    jsonString = $('#jsontext').val();
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
            $('#jsonForm')[0].reset();
            window.$('#jsonModal').modal('hide');				
            $('#json_add').attr('disabled', false);
            setTimeout(function () {
                runnerRecords.ajax.reload();
                stratinRecords.ajax.reload();
                }, 750)
        },
        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            window.alert(JSON.stringify(xhr));
            console.log(JSON.stringify(xhr));
            $('#json_add').attr('disabled', false);
        }
    })
});


//delete modal
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
