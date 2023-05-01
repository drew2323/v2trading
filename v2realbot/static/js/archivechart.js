var tradeDetails = new Map();
var toolTip = null
var CHART_SHOW_TEXT = false
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
    data.trades.forEach((trade, index, array) => {
        obj = {};
        a_markers = {}
        timestamp = Date.parse(trade.order.filled_at)/1000
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
                if (CHART_SHOW_TEXT) 
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
        marker["color"] = (trade.order.side == "buy") ? "#cfcbc2" : "red"
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
    transformed["avgp_buy_line"] = avgp_buy_line 
    transformed["markers"] = markers
    transformed["markers_line"] = markers_line
    transformed["avgp_markers"] = avgp_markers
    //get additional indicators
    //TBD
    return transformed
}

//unit: Min, Hour, Day, Week, Month
//prepare data before displaying archived chart - fetch history bars if necessary
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
            console.log("one minute bars", JSON.stringify(data))
            data.map((el)=>{
                cas = new Date(el.timestamp)
                el.time = cas.getTime()/1000;
                delete el.timestamp
                });
            console.log("one min bars_after_transformation", JSON.stringify(data))
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
    if (chart !== null) {
        chart.remove()
        clear_status_header()
        if (toolTip !== null) {
            toolTip.style.display = 'none';
        }
    }

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
    toolTip.style.background = 'white';
    toolTip.style.color = 'black';
    toolTip.style.borderColor = '#2962FF';
    container1.appendChild(toolTip);
    //initialize chart
    document.getElementById("chart").style.display = "block"

    var chartOptions = { width: 1300,
                        height: 600,
                        leftPriceScale: {visible: true},
                        layout: {
                            background: {
                                type: 'solid',
                                color: '#000000',
                            },
                            textColor: '#d1d4dc',
                        },
                        grid: {
                            vertLines: {
                                visible: true,
                                color: "#434d46"
                            },
                            horzLines: {
                                color: "#667069",
                                visible:true
                            },
	                    },
                    }
    chart = LightweightCharts.createChart(container1, chartOptions);
    chart.applyOptions({ timeScale: { visible: true, timeVisible: true, secondsVisible: true }, crosshair: {
        mode: LightweightCharts.CrosshairMode.Normal, labelVisible: true
    }})

    container1.append(switcherElement)

    var archCandlestickSeries = null

    switch_to_interval(intervals[1])
    chart.timeScale().fitContent();

    function switch_to_interval(interval) {
        //prip prenuti prepisujeme candlestick a markery

        if (archCandlestickSeries) {
            last_range = chart.timeScale().getVisibleRange()
            chart.removeSeries(archCandlestickSeries);
            archCandlestickSeries = null
        }
        else {
            last_range = null
        }
        archCandlestickSeries = chart.addCandlestickSeries({ lastValueVisible: true, priceLineWidth:2, priceLineColor: "red", priceFormat: { type: 'price', precision: 2, minMove: 0.01 }});
        archCandlestickSeries.priceScale().applyOptions({
            scaleMargins: {
                top: 0.1, // highest point of the series will be 10% away from the top
                bottom: 0.4, // lowest point will be 40% away from the bottom
            },
        });
        archCandlestickSeries.setData(AllCandleSeriesesData.get(interval));
        if (last_range) {
            chart.timeScale().setVisibleRange(last_range);
        }
    }

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
    
    console.log("avgp_buy_line",transformed_data["avgp_buy_line"])
    console.log("avgp_markers",transformed_data["avgp_markers"])

    if (transformed_data["avgp_buy_line"].length > 0) {
        var avgBuyLine = chart.addLineSeries({
            //    title: "avgpbuyline",
                color: '#e8c76d',
            //    color: 'transparent',
                lineWidth: 1,
                lastValueVisible: false
            });
        avgBuyLine.setData(transformed_data["avgp_buy_line"]);
        avgBuyLine.setMarkers(transformed_data["avgp_markers"])
    }

    var markersLine = chart.addLineSeries({
          //  title: "avgpbuyline",
          //  color: '#d6d1c3',
            color: 'transparent',
            lineWidth: 1,
            lastValueVisible: false
        });
    markersLine.setData(transformed_data["markers_line"]);
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
    



    //TODO onlick zkopirovat timestamp param.time
    // chart.subscribeClick(param => {
    //     $('#trade-timestamp').val(param.time)
    //     //alert(JSON.safeStringify(param))
    //     //console.log(param.hoveredObjectId);
    // });

    //TODO
    // - legend
    // - identifikatory
    // - volume


    //chart.subscribeCrosshairMove(param => {
        chart.subscribeCrosshairMove(param => {
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


    //add status
    $("#statusRegime").text("ARCHIVED RUN")
    $("#statusName").text(archRecord.name)
    $("#statusMode").text(archRecord.mode)
    $("#statusAccount").text(archRecord.account)
    $("#statusStratvars").text(JSON.stringify(archRecord.stratvars,null,2))

    
    //TBD other dynamically created indicators

}