var tradeDetails = new Map();
var toolTip = null
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

//render chart of archived runs
function chart_archived_run(archRecord, data) {
    if (chart !== null) {
        chart.remove()
        clear_status_header()
        if (toolTip !== null) {
            toolTip.style.display = 'none';
        }
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
    toolTip = document.createElement('div');
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


    //add status
    $("#statusRegime").text("ARCHIVED RUN")
    $("#statusName").text(archRecord.name)
    $("#statusMode").text(archRecord.mode)
    $("#statusAccount").text(archRecord.account)
    $("#statusStratvars").text(JSON.stringify(archRecord.stratvars,null,2))


    chart.timeScale().fitContent();
    
    //TBD other dynamically created indicators

}