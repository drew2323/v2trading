
API_KEY = localStorage.getItem("api-key")
var chart = null
var colors = ["#8B1874","#B71375","#B46060","#61c740","#BE6DB7","#898121","#4389d9","#00425A","#B5D5C5","#e61957"]
var reset_colors = colors
var indList = []
var verticalSeries=null
var candlestickSeries = null
var volumeSeries = null
var vwapSeries = null

indConfig = {}
settings = {}
settings
//ostatni indicatory nez vwap, volume a bary
indConfig = [ {name: "ema", titlevisible: false, embed: true, display: true, priceScaleId: "right", lastValueVisible: false},
              {name: "slope", titlevisible: true, embed: true, display: false, priceScaleId: "middle", lastValueVisible: false},
              {name: "slopeMA", titlevisible: true, embed: true, display: true, priceScaleId: "middle", lastValueVisible: false},
              {name: "emaSlow", titlevisible: true, embed: true, display: true, priceScaleId: "right", lastValueVisible: false},
              {name: "emaFast", titlevisible: true, embed: true, display: true, priceScaleId: "right", lastValueVisible: false},
              {name: "RSI14", titlevisible: true, embed: true, display: true, priceScaleId: "left", lastValueVisible: false},
              {name: "RSI5", titlevisible: true, embed: true, display: true, priceScaleId: "left", lastValueVisible: false},
              {name: "aroon", titlevisible: true, embed: true, display: true, priceScaleId: "left", lastValueVisible: false},
              {name: "apo", titlevisible: true, embed: true, display: true, priceScaleId: "left", lastValueVisible: false},
              {name: "ppo", titlevisible: true, embed: true, display: true, priceScaleId: "left", lastValueVisible: false},
              {name: "stoch2", titlevisible: true, embed: true, display: true, priceScaleId: "left", lastValueVisible: false},
              {name: "stoch1", titlevisible: true, embed: true, display: true, priceScaleId: "left", lastValueVisible: false},]

function get_ind_config(indName) {
    const i = indConfig.findIndex(e => e.name === indName);
    if (i>-1)
        {
            return indConfig[i]
        }
    return null
}

function toggle_vertical_line(time) {
    if (verticalSeries) {
        chart.removeSeries(verticalSeries)
    }
    verticalSeries = chart.addHistogramSeries({
        priceScaleId: '',
        color: 'rgba(128, 128, 255, 0.25)',
        scaleMargins: { top: 0, bottom: 0 },
        lastValueVisible: false,      
      })
    verticalSeries.setData([{ time: time, value: 1 }])
}

//LEGEND INIT
var legendlist = document.getElementById('legend');
var firstRow = document.createElement('div');
firstRow.innerHTML = '-';
// firstRow.style.color = 'white';
legendlist.appendChild(firstRow);

function update_chart_legend(param) {

    function name(val, color = null) {
        color = (color)?' style="color: '+ color + ';"' : ""; 
        return '<div class="legendItemName" ' + color + '>' + val + '</>'
    }
    function val(val, color = null) {
        color = (color)?' style="color: '+ color + ';"' : ""; 
        return '<div class="legendItemValue" ' + color + '>' + val + '</>'
    }

    if (param.time) {
        firstRow.innerHTML = "";
        //BASIC INDICATORS
        const bars = param.seriesData.get(candlestickSeries);
        if (bars !== undefined) {
            //console.log(JSON.stringify(candlestickSeries.options()))
            var color = candlestickSeries.options().upColor;
            firstRow.innerHTML += name("O", color) + val(bars.open) + name("H", color) + val(bars.high) + name("L", color) + val(bars.low) + name("C") + val(bars.close)
        }       
        
        const volumes = param.seriesData.get(volumeSeries);
        if (volumes !== undefined) {
            var color = volumeSeries.options().color;
            firstRow.innerHTML += name("Vol", color) +val(volumes.value)
        } 
        const data = param.seriesData.get(vwapSeries);
        if (data !== undefined) {
            var color = vwapSeries.options().color;
            const vwap = data.value !== undefined ? data.value : data.close;
            firstRow.innerHTML += name('vwap', color) + val(vwap.toFixed(2))
        }
        //ADDITIONAL CUSTOM INDICATORS
        //iterate of custom indicators dictionary to get values of custom lines
        // var customIndicator = {name: key, series: null}
        indList.forEach(function (item) {
            var ind = param.seriesData.get(item.series)
            var color = item.series.options().color;
            if (ind !== undefined) { firstRow.innerHTML += name(item.name, color) + val(ind.value.toFixed(3), color)}
        }); 
    }
    else {
    firstRow.innerHTML = '';
    }
}

function subtractMinutes(date, minutes) {
    date.setMinutes(date.getMinutes() - minutes);
  
    return date;
  }

function addMinutes(date, minutes) {
date.setMinutes(date.getMinutes() + minutes);

return date;
}

//remove previous chart if exists and intiialize chart variables
function cleanup_chart() {
    if (chart) {
        console.log("cleanup")
        chart.remove()
        clear_status_header()
        chart = null
        indList = [];
        markersLine = null
        avgBuyLine = null
        volumeSeries = null
        vwapSeries = null
        verticalSeries=null
        if (toolTip) {
            toolTip.style.display = 'none';
        }
    }
    $( ".switcher" ).remove();
    $('#button_clearlog').hide();
}

function initialize_chart() {
    $('#chartContainerInner').addClass("show");
    $('#button_clearlog').show();
    //PUVODNI BILY MOD
    //var chartOptions = { width: 1045, height: 600, leftPriceScale: {visible: true}}

    //TMAVY MOD
    var chartOptions = { width: 1080,
        height: 600,
        leftPriceScale: {visible: true},
        layout: {
            background: {
                type: 'solid',
                color: '#2a2e39',
            },
            textColor: '#d1d4dc',
        },
        grid: {
            vertLines: {
                visible: true,
                color: "#434651"
            },
            horzLines: {
                color: "#434651",
                visible:true
            },
        },
    }

    chart = LightweightCharts.createChart(document.getElementById('chart'), chartOptions);
    chart.applyOptions({ timeScale: { visible: true, timeVisible: true, secondsVisible: true }, crosshair: {
        mode: LightweightCharts.CrosshairMode.Normal, labelVisible: true
    }})
}

//mozna atributy last value visible
function intitialize_candles() {
    candlestickSeries = chart.addCandlestickSeries({ lastValueVisible: false, priceLineWidth:1, priceLineColor: "red", priceFormat: { type: 'price', precision: 2, minMove: 0.01 }});
    candlestickSeries.priceScale().applyOptions({
        scaleMargins: {
            top: 0.1, // highest point of the series will be 10% away from the top
            bottom: 0.4, // lowest point will be 40% away from the bottom
        },
    });
    candlestickSeries.applyOptions({
        lastValueVisible: true,
        priceLineVisible: true,
    });

}

function initialize_volume() {
    volumeSeries = chart.addHistogramSeries({title: "Volume", color: '#26a69a', priceFormat: {type: 'volume'}, priceScaleId: ''});
    volumeSeries.priceScale().applyOptions({
        // set the positioning of the volume series
        scaleMargins: {
            top: 0.7, // highest point of the series will be 70% away from the top
            bottom: 0,
        },
    });
}

function initialize_vwap() {
    vwapSeries = chart.addLineSeries({
        //    title: "vwap",
            color: '#2962FF',
            lineWidth: 1,
            lastValueVisible: false,
            priceLineVisible: false
        })
}


function populate_indicator_buttons() {
	var buttonElement = document.createElement('div');
    buttonElement.id = "indicatorsButtons"
	buttonElement.classList.add('switcher');

    indList.forEach(function (item, index) {
		var itemEl = document.createElement('button');
		itemEl.innerText = item.name;
        itemEl.id = "IND"+index;
        itemEl.style.color = item.series.options().color;
		itemEl.classList.add('switcher-item');
		itemEl.classList.add('switcher-active-item');
		itemEl.addEventListener('click', function() {
			onItemClicked1(index);
		});
		buttonElement.appendChild(itemEl);
	});

	function onItemClicked1(index) {
        vis = true;
        const elem = document.getElementById("IND"+index);
        if (elem.classList.contains("switcher-active-item")) {
            vis = false;
        }      
        elem.classList.toggle("switcher-active-item");
        indList[index].series.applyOptions({
            visible: vis });
	}
    return buttonElement;
}


//range switch pro chart https://jsfiddle.net/TradingView/qrb9a850/
function createSimpleSwitcher(items, activeItem, activeItemChangedCallback) {
	var switcherElement = document.createElement('div');
	switcherElement.classList.add('switcher');

	var intervalElements = items.map(function(item) {
		var itemEl = document.createElement('button');
		itemEl.innerText = item;
		itemEl.classList.add('switcher-item');
		itemEl.classList.toggle('switcher-active-item', item === activeItem);
		itemEl.addEventListener('click', function() {
			onItemClicked(item);
		});
		switcherElement.appendChild(itemEl);
		return itemEl;
	});

	function onItemClicked(item) {
		if (item === activeItem) {
			return;
		}

		intervalElements.forEach(function(element, index) {
			element.classList.toggle('switcher-active-item', items[index] === item);
		});

		activeItem = item;

		activeItemChangedCallback(item);
	}

	return switcherElement;
}

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

 function isToday(someDate) {
    const today = new Date()
    return someDate.getDate() == today.getDate() &&
      someDate.getMonth() == today.getMonth() &&
      someDate.getFullYear() == today.getFullYear()
  }

//https://www.w3schools.com/jsref/jsref_tolocalestring.asp
function format_date(datum, markettime = false, timeonly = false) {
    //const options = { weekday: 'long', year: 'numeric', month: 'numeric', day: 'numeric', };
    // date.toLocaleString('en-US', {
    //     timeZone: 'America/New_York',
    //   })
    //'Europe/Berlin'
    var options = {}
    if (timeonly) {
        options = {hour: '2-digit',   hour12: false, minute: '2-digit'}
    }
    else {
        options = {dateStyle: "short", timeStyle: "short"}  
    }

    if (markettime) {
        options["timeZone"] = 'America/New_York'
    }
    const date = new Date(datum);
    return date.toLocaleString('cs-CZ', options);
}

function clear_status_header() {
    $("#statusRegime").text("")
    $("#statusName").text("")
    $("#statusMode").text("")
    $("#statusAccount").text("")
    $("#statusIlog").text("")
    $("#statusStratvars").text("")
    //clear previous logs from rt
    $("#lines").empty()
}

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