const momentumIndicatorNames = ["roc", "slope", "slopeMA"]
var pbiList = []
var ws = null;
var logcnt = 0
var positionsPriceLine = null
var limitkaPriceLine = null
var angleSeries = 1

//get details of runner to populate chart status
//fetch necessary - it could be initiated by manually inserting runnerId
function populate_rt_status_header(runnerId) {
    $.ajax({
        url:"/runners/"+runnerId,
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-API-Key',
                API_KEY); },
        method:"GET",
        contentType: "application/json",
        success:function(data){
            //console.log(JSON.stringify(data))
            //add status on chart
            $("#statusRegime").text("REALTIME: "+data.id)
            $("#statusName").text(data.run_name)
            $("#statusMode").text(data.run_mode)
            $("#statusAccount").text(data.run_account)
            //$("#statusStratvars").text(JSON.stringify(data.stratvars,null,2))
        },
        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            window.alert(JSON.stringify(xhr));
            //console.log(JSON.stringify(xhr));
        }
    })    
}


function connect(event) {
    var runnerId = document.getElementById("runnerId")
    try {
        ws = new WebSocket("ws://"+ window.location.hostname +":8000/runners/" + runnerId.value + "/ws?api_key=" + API_KEY);
    }
    catch (err) {
        console.log("nejaky error" + err)
    }
    ws.onopen = function(event) {
        populate_real_time_chart()
        document.getElementById("status").textContent = "Connected to" + runnerId.value
        document.getElementById("bt-disc").style.display = "initial"
        document.getElementById("bt-conn").style.display = "none"
        document.getElementById("chart").style.display = "block"
        populate_rt_status_header(runnerId.value)
    }
    ws.onmessage = function(event) {
        var parsed_data = JSON.parse(event.data)

        //console.log(JSON.stringify(parsed_data))

        //check received data and display lines
        if (parsed_data.hasOwnProperty("bars")) {
            var bar = parsed_data.bars 
            candlestickSeries.update(bar);
            volumeSeries.update({
                time: bar.time,
                value: bar.volume
            });
            vwapSeries.update({
                time: bar.time,
                value: bar.vwap
            });
        }

        if (parsed_data.hasOwnProperty("bars")) {
            // console.log("mame bary")
            var bar = parsed_data.bars 
            candlestickSeries.update(bar);
            volumeSeries.update({
                time: bar.time,
                value: bar.volume
            });
            vwapSeries.update({
                time: bar.time,
                value: bar.vwap
            });
        }

        //loglist
        if (parsed_data.hasOwnProperty("iter_log")) { 
            iterLogList = parsed_data.iter_log
            //console.log("Incoming logline object")

            // var lines = document.getElementById('lines')
            // var line = document.createElement('div')
            // line.classList.add("line")
            // const newLine = document.createTextNode("---------------")
            // line.appendChild(newLine)
            // lines.appendChild(line)

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


                logcnt++;
                row = '<div data-bs-toggle="collapse" onclick="set_timestamp(' + logLine.time + ')" data-bs-target="#rec'+logcnt+'">'+logLine.time + " " + logLine.event + ' - '+ (logLine.message == undefined ? "" : logLine.message) +'</div>'
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

        //limitka
        if (parsed_data.hasOwnProperty("limitka")) { 
            limitka = parsed_data.limitka
            const limitkaLine = {
                price: limitka.price,
                color: '#1ed473',
                lineWidth: 1,
                lineStyle: 1, // LineStyle.Dotted
                axisLabelVisible: true,
                title: "SELL:XX",
            };

            if (limitkaPriceLine !== null) {
                candlestickSeries.removePriceLine(limitkaPriceLine)
            }
            limitkaPriceLine = candlestickSeries.createPriceLine(limitkaLine);
        }


        if (parsed_data.hasOwnProperty("pendingbuys")) {
            pendingbuys = parsed_data.pendingbuys

            //vymazeme vsechny predchozi instance pendingbuys
            if (pbiList.length) {
                //console.log(pbiList)
                pbiList.forEach((line) => {
                    candlestickSeries.removePriceLine(line)
                });
                pbiList = []
            }

            //zobrazime pendingbuys a ulozime instance do pole
            //console.log("pred loopem")
            for (const [orderid, price] of Object.entries(pendingbuys)) {
                //console.log("v loopu", price)
                const pbLine = {
                    price: parseFloat(price),
                    color: "#e3a059",
                    lineWidth: 1,
                    lineStyle: 1, // LineStyle.Dotted
                    axisLabelVisible: true,
                    title: "BUY:",
                };

                pbLineInstance = candlestickSeries.createPriceLine(pbLine);
                pbiList.push(pbLineInstance)
            }

        }

        if (parsed_data.hasOwnProperty("positions")) { 
            positions = parsed_data.positions
            const posLine = {
                price: positions.avgp,
                color: '#918686',
                lineWidth: 1,
                lineStyle: 1, // LineStyle.Dotted
                axisLabelVisible: true,
                title: "POS:"+positions.positions,
            };

            if (positionsPriceLine !== null) {
                candlestickSeries.removePriceLine(positionsPriceLine)
            }
            positionsPriceLine = candlestickSeries.createPriceLine(posLine);
        }

        if (parsed_data.hasOwnProperty("statinds")) { 
            // console.log("got static indicators")
            var statinds = parsed_data.statinds
            if (Object.keys(statinds).length > 0) {
                    // console.log("got static indicators")
                    // console.log(JSON.stringify(statinds))

                    for (const [klic, hodnota] of Object.entries(statinds)) {
                        // console.log(JSON.stringify(klic))
                        // console.log(JSON.stringify(hodnota))
                        //TODO predelat na configuracni klice vizualizacni dotahovane z backendu, ktere namapuji vybrane stratvars na typ vizualizace 
                        if (klic === "angle") {

                            //nejsou vsechny hodnoty
                            if (Object.keys(hodnota).length > 1)  {
                                // console.log("angle nalezen");
                                // console.log(JSON.stringify(hodnota));
                                if (angleSeries !== 1) {
                                    // console.log("angle neni jedna" + toString(angleSeries))
                                    chart.removeSeries(angleSeries)
                                }
                                
                                angleSeries = chart.addLineSeries({
                                    //title: key,
                                    lineWidth: 2,
                                    lineStyle: 2,
                                    color: "#d432e6",
                                    lastValueVisible: false,
                                    priceLineVisible: false,
                                    priceLineWidth: 0,
                                    priceLineStyle: 3
                                })
                                dataPoints = [{time: hodnota.lookbacktime, value: hodnota.lookbackprice},{ time: hodnota.time, value: hodnota.price}]
                                // console.log("pridano")
                                // console.log(toString(dataPoints))
                                angleSeries.setData(dataPoints)
                            }
                        }
                    }









                }
        }

        if (parsed_data.hasOwnProperty("indicators")) { 
            // console.log("jsme uvnitr indikatoru")
            var indicators = parsed_data.indicators
            //if there are indicators it means there must be at least two keys (except time which is always present)
            if (Object.keys(indicators).length > 1) {
                for (const [key, value] of Object.entries(indicators)) {
                    if (key !== "time") {
                        //if indicator doesnt exists in array, initialize it and store reference to array
                        const searchObject= indList.find((obj) => obj.name==key);
                        if (searchObject == undefined) {
                            //console.log("object new - init and add")
                            var obj = {name: key, series: null}

                            //get configuation of indicator to display
                            conf = get_ind_config(key)

                            //INIT INDICATOR BASED on CONFIGURATION

                            //MOVE TO UTILS ro reuse??
                            if (conf && conf.display) {
                                if (conf.embed)  {
                                    obj.series = chart.addLineSeries({
                                        color: colors.shift(),
                                        priceScaleId: conf.priceScaleId,
                                        lastValueVisible: conf.lastValueVisible,
                                        title: (conf.titlevisible?conf.name:""),
                                        lineWidth: 1
                                    });   

                                    //tady add data
                                    obj.series.update({
                                        time: indicators.time,
                                        value: value});
                                    indList.push(obj);

                                    //toto nejak vymyslet konfiguracne, additional threshold lines
                                    if (key == "slopeMA") {
                                        //natvrdo nakreslime lajnu pro min angle
                                        //TODO predelat na configuracne
                                        const minSlopeLineOptopns = {
                                            price: parsed_data.statinds.angle.minimum_slope,
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
                            }
                        }
                        //indicator exists in an array, lets update it
                        else {
                        //console.log("object found - update")
                        //tady add data
                        searchObject.series.update({
                            time: indicators.time,
                            value: value
                        });
                        }
                    }
                }
            }
        }
    }
    ws.onclose = function(event) {
        document.getElementById("status").textContent = "Disconnected from" + runnerId.value
        document.getElementById("bt-disc").style.display = "none"
        document.getElementById("bt-conn").style.display = "initial"
    }
    event.preventDefault()
}
function disconnect(event) {
    ws.close()
    document.getElementById("bt-disc").style.display = "none"
    document.getElementById("bt-conn").style.display = "block"
    event.preventDefault()
}
function sendMessage(event) {
    var input = document.getElementById("messageText")
    ws.send(input.value)
    input.value = ''
    event.preventDefault()
}