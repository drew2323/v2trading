var tradeDetails = new Map();
var toolTip = null
var CHART_SHOW_TEXT = false
// var vwapSeries = null
// var volumeSeries = null
var markersLine = null
var avgBuyLine = null
//TRANSFORM object returned from RESTA PI get_arch_run_detail
//to series and markers required by lightweigth chart
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
    var last_timestamp = 0.1
    var iterator = 0.002
    data.trades.forEach((trade, index, array) => {
        obj = {};
        a_markers = {}
        timestamp = Date.parse(trade.order.filled_at)/1000
        //light chart neumi vice zaznamu ve stejny cas
        //protoze v BT se muze stat vice tradu v jeden cas, testujeme stejne hodnoty a pripadne pricteme jednu ms
        //tradu s jednim casem muze byt za sebou vic, proto iterator 
        if (last_timestamp > timestamp) {
            console.log("NEKONZISTENCE RAZENI",last_timestamp, timestamp)
            console.log("aktualni trade", JSON.stringify(trade,null,2))
            console.log("předchozí trade", JSON.stringify(data.trades[index-1],null,2))
        }
        if (last_timestamp == timestamp) {
            last_timestamp = timestamp
            console.log("DUPLICITA tradu aktual/predchozi/nasledujici", trade, data.trades[index-1], data.trades[index+1])
            console.log("původní timestamp je ",timestamp)
            timestamp = parseFloat(timestamp) + iterator
            console.log("nový timestamp je ",timestamp)
            iterator += 0.001
        }
        else {
            last_timestamp = timestamp
            iterator = 0.002
        }

        if (trade.order.side == "buy") {
                //avgp lajnu vytvarime jen pokud je v tradeventu prumerna cena
                if (trade.pos_avg_price !== null) {
                //line pro avgp markers
                obj["time"] = timestamp;
                obj["value"] = trade.pos_avg_price;
                avgp_buy_line.push(obj)

                //avgp markers pro prumernou cenu aktualnich pozic
                a_markers["time"] = timestamp
                a_markers["position"] = "aboveBar"
                a_markers["color"] = "#e8c76d"
                a_markers["shape"] = "arrowDown"
                //if (CHART_SHOW_TEXT) 
    //          a_markers["text"] = trade.position_qty + " " + parseFloat(trade.pos_avg_price).toFixed(3)
                a_markers["text"] = CHART_SHOW_TEXT ? trade.position_qty + "/" + parseFloat(trade.pos_avg_price).toFixed(3) :trade.position_qty
                avgp_markers.push(a_markers)
            }
        }

        //buy sell markery
        marker = {}
        marker["time"] = timestamp;
        // marker["position"] = (trade.order.side == "buy") ? "belowBar" : "aboveBar" 
        marker["position"] = (trade.order.side == "buy") ? "inBar" : "aboveBar" 
        marker["color"] = (trade.order.side == "buy") ? "#37cade" : "red"
        //marker["shape"] = (trade.order.side == "buy") ? "arrowUp" : "arrowDown"
        marker["shape"] = (trade.order.side == "buy") ? "circle" : "arrowDown"
        //marker["text"] =  trade.qty + "/" + trade.price
        marker["text"] =  CHART_SHOW_TEXT ? trade.qty + "/" + trade.price : trade.qty
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

    //pro jistotu jeste seradime podle casu
    //v BT se muze predbehnout a lightweight to pak nezobrazi
    const sorter = (a, b) => a.time > b.time ? 1 : -1;

    markers.sort(sorter)
    markers_line.sort(sorter)
    avgp_buy_line.sort(sorter)
    avgp_markers.sort(sorter)

    transformed["avgp_buy_line"] = avgp_buy_line 
    transformed["avgp_markers"] = avgp_markers
    transformed["markers"] = markers
    transformed["markers_line"] = markers_line

    //get additional indicators
    return transformed
}

//unit: Min, Hour, Day, Week, Month
//prepares data before displaying archived chart - fetch history bars if necessary
function prepare_data(archRunner, timeframe_amount, timeframe_unit, archivedRunnerDetail) {
   req = {}
   req["symbol"] = archRunner.symbol

    if (archRunner.mode == "backtest") {
        req["datetime_object_from"] = archRunner.bt_from
        req["datetime_object_to"] = archRunner.bt_to
    }
    else 
    {
        req["datetime_object_from"] = archRunner.started
        req["datetime_object_to"] = archRunner.stopped
    }
    console.log("datum pred",req.datetime_object_from)
    //pridame z obou stran 1 minutu - kvuli zobrazeni na frontendu,
    req["datetime_object_from"] = subtractMinutes(new Date(req.datetime_object_from),1).toISOString()
    req["datetime_object_to"] = addMinutes(new Date(req.datetime_object_to),1).toISOString()
    console.log("datum po", req.datetime_object_from)
    req["timeframe_amount"] = timeframe_amount
    req["timeframe_unit"] = timeframe_unit
    $.ajax({
        url:"/history_bars/",
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-API-Key',
                API_KEY); },
        method:"GET",
        contentType: "application/json",
        data: req,
        success:function(data){
            //console.log("one minute bars before", JSON.stringify(data))
            data.map((el)=>{
                cas = new Date(el.timestamp)
                el.time = cas.getTime()/1000;
                delete el.timestamp
                });
            //console.log("one min bars_after_transformation", JSON.stringify(data))
            oneMinuteBars = data
            chart_archived_run(archRunner, archivedRunnerDetail, oneMinuteBars);
            //call function to continue
            //return data
            //$("#statusStratvars").text(JSON.stringify(data.stratvars,null,2))
        },
        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            window.alert(JSON.stringify(xhr));
            console.log(JSON.stringify(xhr));
        }
    })  
}

//render chart of archived runs
function chart_archived_run(archRecord, data, oneMinuteBars) {
    cleanup_chart()

    var transformed_data = transform_data(data)

    //initialize resolutions
    var native_resolution = data.bars.resolution[0]+"s"
    //console.log("native", native_resolution)
 
    //available intervals zatim jen 1m
    var intervals = [native_resolution, '1m'];
    nativeData  = transformed_data["bars"]
    //get one minute data
    //tbd prepare volume
    //console.log("oneMinuteData",oneMinuteBars)

    var AllCandleSeriesesData = new Map([
        [native_resolution, nativeData ],
        ["1m", oneMinuteBars ],
      ]);

   var switcherElement = createSimpleSwitcher(intervals, intervals[1], switch_to_interval);

    //define tooltip
    const container1 = document.getElementById('chart');

    const toolTipWidth = 90;
    const toolTipHeight = 90;
    const toolTipMargin = 15;
    
    // Create and style the tooltip html element
    toolTip = document.createElement('div');
    //width: 90px; , height: 80px; 
    toolTip.style = `position: absolute; display: none; padding: 8px; box-sizing: border-box; font-size: 12px; text-align: left; z-index: 1000; top: 12px; left: 12px; pointer-events: none; border: 1px solid; border-radius: 2px;font-family: -apple-system, BlinkMacSystemFont, 'Trebuchet MS', Roboto, Ubuntu, sans-serif; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;`;
    toolTip.style.backgroundColor = '#2d323e';
    toolTip.style.color = '#babfcd';
    toolTip.style.borderColor = "#a7a9b0";
    //'#2962FF';
    container1.appendChild(toolTip);
    //initialize chart
    document.getElementById("chart").style.display = "block"

    initialize_chart()

    container1.append(switcherElement)

    candlestickSeries = null

    switch_to_interval(intervals[1])
    chart.timeScale().fitContent();

    function switch_to_interval(interval) {
        //prip prpenuti prepisujeme candlestick a markery
        if (candlestickSeries) {
            last_range = chart.timeScale().getVisibleRange()
            chart.removeSeries(candlestickSeries);
            candlestickSeries = null
        }
        else {
            last_range = null
        }

        intitialize_candles()
        candlestickSeries.setData(AllCandleSeriesesData.get(interval));

        if (interval == native_resolution) {
            //indicators are in native resolution only
            display_indicators(data);
            var indbuttonElement = populate_indicator_buttons();
            container1.append(indbuttonElement);      
        }
        else {
            remove_indicators();
            btnElement = document.getElementById("indicatorsButtons")
            if (btnElement) {
                container1.removeChild(btnElement);
            }
        }

        display_buy_markers();

        if (last_range) {
            chart.timeScale().setVisibleRange(last_range);
        }
    }

    //TBD
    //pro kazdy identifikator zobrazime button na vypnuti zapnuti
    //vybereme barvu pro kazdy identifikator
    //zjistime typ idenitfikatoru - zatim right vs left
    function display_indicators(data) {
        console.log("indikatory", JSON.stringify(data.indicators,null,2))
        //podobne v livewebsokcets.js - dat do jedne funkce
        if (data.hasOwnProperty("indicators")) { 
            // console.log("jsme uvnitr indikatoru")
            var indicators = data.indicators
            //if there are indicators it means there must be at least two keys (time which is always present)
            if (Object.keys(indicators).length > 1) {
                for (const [key, value] of Object.entries(indicators)) {
                    if (key !== "time") {
                            //initialize indicator and store reference to array
                            var obj = {name: key, series: null}
    
                            //start
                            //console.log(key)
                            //get configuation of indicator to display
                            conf = get_ind_config(key)

                            //INIT INDICATOR BASED on CONFIGURATION

                            //MOVE TO UTILS ro reuse??
                            if (conf && conf.display) {

                                //tranform data do správného formátru
                                items = []
                                //var last = null
                                value.forEach((element, index, array) => {
                                    item = {}
                                    //debug
                                    //TOTO odstranit po identifikovani chyby
                                    //if (indicators.time[index] !== undefined) {
                                        //{console.log("problem",key,last)}
                                    item["time"] = indicators.time[index]
                                    item["value"] = element
                                    //console.log("objekt indicatoru",item)
                                    items.push(item)
                                        //debug
                                    //last = item
                                    // }
                                    // else
                                    // {
                                    //     console.log("chybejici cas", key)
                                    // }
                                });

                                if (conf.embed)  {
                                    obj.series = chart.addLineSeries({
                                        color: colors.shift(),
                                        priceScaleId: conf.priceScaleId,
                                        title: (conf.titlevisible?conf.name:""),
                                        lineWidth: 1
                                    });   

                                    //toto nejak vymyslet konfiguracne, additional threshold lines
                                    if (key == "slopeMA") {
                                        //natvrdo nakreslime lajnu pro min angle
                                        //TODO predelat na configuracne
                                        const minSlopeLineOptopns = {
                                            price: data.statinds.angle.minimum_slope,
                                            color: '#b67de8',
                                            lineWidth: 1,
                                            lineStyle: 2, // LineStyle.Dotted
                                            axisLabelVisible: true,
                                            title: "max:",
                                        };
                            
                                        const minSlopeLine = obj.series.createPriceLine(minSlopeLineOptopns);
                                    }
                                }
                                //INDICATOR on new pane
                                else { console.log("not implemented")}
                            
                            //add options
                            obj.series.applyOptions({
                                lastValueVisible: false,
                                priceLineVisible: false,
                            });

                            //console.log("problem tu",items)
                            //add data
                            obj.series.setData(items)

                            // add to indList array - pole zobrazovanych indikatoru    
                            indList.push(obj);   
                        }
                    }
                }
            }
        }

        //display vwap and volume
        initialize_vwap()
        vwapSeries.setData(transformed_data["vwap"])

        initialize_volume()
        volumeSeries.setData(transformed_data["volume"])
        console.log("volume")        
    }

    function remove_indicators() {
        //reset COLORS
        colors = reset_colors

        //remove CUSTOMS indicators if exists
        indList.forEach((element, index, array) => {
            chart.removeSeries(element.series);
        }
        );
        indList = [];
        //remove BASIC indicators
        if (vwapSeries) {
            chart.removeSeries(vwapSeries)
        }
        if (volumeSeries) {
            chart.removeSeries(volumeSeries)
        }
    }

    //displays (redraws) buy markers
    function display_buy_markers() {
        if (avgBuyLine) {
            chart.removeSeries(avgBuyLine)
        }

        if (markersLine) {
            chart.removeSeries(markersLine)
        }      

        //console.log("avgp_buy_line",JSON.stringify(transformed_data["avgp_buy_line"],null,2))
        //console.log("avgp_markers",JSON.stringify(transformed_data["avgp_markers"],null,2))

        if (transformed_data["avgp_buy_line"].length > 0) {
            avgBuyLine = chart.addLineSeries({
                //    title: "avgpbuyline",
                    color: '#e8c76d',
                //    color: 'transparent',
                    lineWidth: 1,
                    lastValueVisible: false
                });

            avgBuyLine.applyOptions({
                lastValueVisible: false,
                priceLineVisible: false,
            });


            avgBuyLine.setData(transformed_data["avgp_buy_line"]);
            avgBuyLine.setMarkers(transformed_data["avgp_markers"]);
        }

        markersLine = chart.addLineSeries({
            //  title: "avgpbuyline",
            //  color: '#d6d1c3',
                color: 'transparent',
                lineWidth: 1,
                lastValueVisible: false
            });

        //console.log("markers_line",JSON.stringify(transformed_data["markers_line"],null,2))
        //console.log("markers",JSON.stringify(transformed_data["markers"],null,2))
    
       markersLine.setData(transformed_data["markers_line"]);
       markersLine.setMarkers(transformed_data["markers"])

        //chart.subscribeCrosshairMove(param => {
            chart.subscribeCrosshairMove(param => {
                //LEGEND SECTIOIN
                firstRow.style.color = 'white';
                update_chart_legend(param);

                //TOOLTIP SECTION
                //$('#trade-timestamp').val(param.time)
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
                    var data2 = param.seriesData.get(avgBuyLine);
                    if ((data !== undefined) || (data2 !== undefined)) {
                    //param.seriesData.forEach((value, key) => {
                        //console.log("key",key)
                        //console.log("value",value)
                    
                        //data = value
                        //DOCASNE VYPNUTO
                        toolTip.style.display = 'block';
                        
                        //console.log(JSON.safeStringify(key))
                        // if (toolTip.innerHTML == "") {
                        //     toolTip.innerHTML = `<div>${param.time}</div>`
                        // }
                        buy_price = 0
                        //u sell markeru nemame avgBuyLine
                        if (data2 !== undefined) {
                            buy_price = parseFloat(data2.value).toFixed(3)
                        }

                        toolTip.innerHTML += `<div>POS:${tradeDetails.get(param.time).position_qty}/${buy_price}</div><div>T:${tradeDetails.get(param.time).qty}/${data.value}</div>`;
        
                        //inspirace
                        // toolTip.innerHTML = `<div style="color: ${'#2962FF'}">Apple Inc.</div><div style="font-size: 24px; margin: 4px 0px; color: ${'black'}">
                        // ${Math.round(100 * price) / 100}
                        // </div><div style="color: ${'black'}">
                        // ${dateStr}
                        // </div>`;
        
        
                        // Position tooltip according to mouse cursor position
                        toolTip.style.left = param.point.x+120 + 'px';
                        toolTip.style.top = param.point.y + 'px';
                    }
                        //});
                }
            });
    }

    chart.subscribeClick(param => {
        $('#trade-timestamp').val(param.time)
        //toggle_vertical_line(param.time);
        if (archRecord.ilog_save == true) {
            fetch_log_data(param.time, archRecord.id);
            }
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

                console.log("toolTip.innerHTML",toolTip.innerHTML)

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


    //add status
    $("#statusRegime").text("PAST RUN: "+archRecord.id)
    $("#statusName").text(archRecord.name)
    $("#statusMode").text(archRecord.mode)
    $("#statusAccount").text(archRecord.account)
    $("#statusIlog").text("Logged:" + archRecord.ilog_save)
    $("#statusStratvars").text(((archRecord.strat_json)?archRecord.strat_json:archRecord.stratvars),null,2)
    $("#statusSettings").text(JSON.stringify(archRecord.settings,null,2))
    
    //TBD other dynamically created indicators

}


function fetch_log_data(timestamp, runner_id) {
    timestamp_from = timestamp - 20
    timestamp_to = timestamp + 20
    req = {}
    req["runner_id"] = runner_id;
    req["timestamp_from"] = timestamp_from;
    req["timestamp_to"] = timestamp_to;
    $.ajax({
        url:"/archived_runners_log/"+runner_id,
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-API-Key',
                API_KEY); },
        method:"GET",
        contentType: "application/json",
        data: req,
        success:function(data){
            //console.log("archived logs", JSON.stringify(data))
            display_log(data, timestamp)
        },
        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            //window.alert(JSON.stringify(xhr));
            console.log("Chyb pri dotazeni logu", JSON.stringify(xhr));
        }
    })  
}

function display_log(iterLogList, timestamp) {
        //console.log("Incoming logline object")

        var lines = document.getElementById('lines')
        var line = document.createElement('div')
        line.classList.add("line")
        const newLine = document.createTextNode("---------------")
        line.appendChild(newLine)
        lines.appendChild(line)

        iterLogList.forEach((logLine) => {
            //console.log("logline item")
            //console.log(JSON.stringify(logLine,null,2))

            // <div class="line">
            //     <div data-toggle="collapse" data-target="#rec1">12233 <strong>Event</strong></div>
            //     <div id="rec1" class="collapse">
            //     Detaila mozna structured
            //     Lorem ipsum dolor sit amet, consectetur adipisicing elit,
            //     sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam,
            //     quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
            //     </div>
            // </div>

            highlighted = (parseInt(logLine.time) == parseInt(timestamp)) ? "highlighted" : ""
            logcnt++;
            row = '<div data-bs-toggle="collapse" class="'+ highlighted + '" onclick="set_timestamp(' + logLine.time + ')" data-bs-target="#rec'+logcnt+'">'+logLine.time + " " + logLine.event + ' - '+ (logLine.message == undefined ? "" : logLine.message) +'</div>'
            str_row = JSON.stringify(logLine.details, null, 2)
            //row_detail = '<div id="rec'+logcnt+'" data-toggle="collapse" data-target="#rec'+logcnt+'"class="collapse pidi"><pre>' + str_row + '</pre></div>'

            row_detail = '<div id="rec'+logcnt+'" class="collapse pidi"><pre>' + str_row + '</pre></div>'

            var lines = document.getElementById('lines')
            var line = document.createElement('div')
            line.classList.add("line")
            line.dataset.timestamp = logLine.time
            
            line.insertAdjacentHTML( 'beforeend', row );
            line.insertAdjacentHTML( 'beforeend', row_detail );
            //line.appendChild(newLine)
            //var pre = document.createElement("span")
            //pre.classList.add("pidi")
            //const stLine = document.createTextNode(str_row)
            //pre.appendChild(stLine)
            //line.appendChild(pre)
            lines.appendChild(line)
        });
        $('#messages').animate({
            scrollTop: $('#lines')[0].scrollHeight}, 2000);

}