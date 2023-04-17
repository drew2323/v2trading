const momentumIndicatorNames = ["roc", "slope"]
var indList = []
var ws = null;
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
        //var messages = document.getElementById('messages')
        //var message = document.createElement('li')
        //var content = document.createTextNode(event.data)
        //message.appendChild(content)
        //messages.appendChild(message)

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
                                    title: key,
                                    lineWidth: 1,
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