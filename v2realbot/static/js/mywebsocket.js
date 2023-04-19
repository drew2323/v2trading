const momentumIndicatorNames = ["roc", "slope"]
var indList = []
var pbiList = []
var ws = null;
var positionsPriceLine = null
var limitkaPriceLine = null
function connect(event) {
    var runnerId = document.getElementById("runnerId")
    try {
        ws = new WebSocket("ws://"+ window.location.hostname +":8000/runners/" + runnerId.value + "/ws?api_key=" + API_KEY);
    }
    catch (err) {
        console.log("nejaky error" + err)
    }
    ws.onopen = function(event) {
        document.getElementById("status").textContent = "Connected to" + runnerId.value
        document.getElementById("bt-disc").style.display = "initial"
        document.getElementById("bt-conn").style.display = "none"
        document.getElementById("chart").style.display = "block"
    }
    ws.onmessage = function(event) {
        var parsed_data = JSON.parse(event.data)

        console.log(JSON.stringify(parsed_data))

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
            console.log("Incoming logline object")

            var lines = document.getElementById('lines')
            var line = document.createElement('div')
            line.classList.add("line")
            const newLine = document.createTextNode("-----------------NEXT ITER------------------")
            line.appendChild(newLine)
            lines.appendChild(line)

            iterLogList.forEach((logLine) => {
                console.log("logline item")
                console.log(JSON.stringify(logLine,null,2))
                row = logLine.time + " <strong>" + logLine.event + "</strong>:" + logLine.message;
                str_row = JSON.stringify(logLine.details, null, 2)
                var lines = document.getElementById('lines')
                var line = document.createElement('div')
                line.classList.add("line")
                //const newLine = document.createTextNode(row)
                line.insertAdjacentHTML( 'beforeend', row );
                //line.appendChild(newLine)
                var pre = document.createElement("span")
                pre.classList.add("pidi")
                const stLine = document.createTextNode(str_row)
                pre.appendChild(stLine)
                line.appendChild(pre)
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
                console.log(pbiList)
                pbiList.forEach((line) => {
                    candlestickSeries.removePriceLine(line)
                });
                pbiList = []
            }

            //zobrazime pendingbuys a ulozime instance do pole
            console.log("pred loopem")
            for (const [orderid, price] of Object.entries(pendingbuys)) {
                console.log("v loopu", price)
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
                color: 'black',
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

        if (parsed_data.hasOwnProperty("indicators")) { 
            var indicators = parsed_data.indicators
            //if there are indicators it means there must be at least two keys (except time which is always present)
            if (Object.keys(indicators).length > 1) {
                for (const [key, value] of Object.entries(indicators)) {
                    if (key !== "time") {
                        //if indicator exists in array, initialize it and store reference to array
                        const searchObject= indList.find((obj) => obj.name==key);
                        if (searchObject == undefined) {
                            console.log("object new - init and add")
                            var obj = {name: key, series: null}
                            if (momentumIndicatorNames.includes(key)) {
                                obj.series = chart.addLineSeries({
                                    priceScaleId: 'left',
                                    title: key,
                                    lineWidth: 1,
                                })                               
                            }
                            else {
                                obj.series = chart.addLineSeries({
                                    //title: key,
                                    lineWidth: 1,
                                    lastValueVisible: false
                                })
                            }
                            obj.series.update({
                                time: indicators.time,
                                value: value});
                            indList.push(obj)
                        }
                        //indicator exists in an array, let update it
                        else {
                        console.log("object found - update")
                        searchObject.series.update({
                            time: indicators.time,
                            value: value
                        });
                        }
                    }
                
                    console.log(`${key}: ${value}`);
                }
            }
        //chart.timeScale().fitContent();
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