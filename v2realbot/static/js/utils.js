
API_KEY = localStorage.getItem("api-key")
var chart = null
var colors = ["#8B1874","#B71375","#B46060","#61c740","#BE6DB7","#898121","#4389d9","#00425A","#B5D5C5","#e61957"]
var reset_colors = colors
var indList = []

indConfig = {}
settings = {}
settings
//ostatni indicatory nez vwap, volume a bary
indConfig = [ {name: "ema", titlevisible: false, embed: true, display: true, priceScaleId: "right", lastValueVisible: false},
              {name: "slope", titlevisible: true, embed: true, display: false, priceScaleId: "left", lastValueVisible: false},
              {name: "slopeMA", titlevisible: true, embed: true, display: true, priceScaleId: "left", lastValueVisible: false},]

function get_ind_config(indName) {
    const i = indConfig.findIndex(e => e.name === indName);
    if (i>-1)
        {
            return indConfig[i]
        }
    return null
}


//LEGEND INIT
var legendlist = document.getElementById('legend');
var firstRow = document.createElement('div');
firstRow.innerHTML = '-';
// firstRow.style.color = 'white';
legendlist.appendChild(firstRow);

function update_chart_legend(param) {

    function name(val) {
        return '<div class="legendItemName">' + val + '</>' 
    }
    function val(val) {
        return '<div class="legendItemValue">' + val + '</>'
    }

    if (param.time) {
        firstRow.innerHTML = "";
        //BASIC INDICATORS
        const bars = param.seriesData.get(candlestickSeries);
        if (bars !== undefined) {
            firstRow.innerHTML += name("O") + val(bars.open) + name("H") + val(bars.high) + name("L") + val(bars.low) + name("C") + val(bars.close)
        }       
        
        const volumes = param.seriesData.get(volumeSeries);
        if (volumes !== undefined) {
            firstRow.innerHTML += name("Vol") +val(volumes.value)
        } 
        const data = param.seriesData.get(vwapSeries);
        if (data !== undefined) {
            const vwap = data.value !== undefined ? data.value : data.close;
            firstRow.innerHTML += name('vwap') + val(vwap.toFixed(2))
        }
        //ADDITIONAL CUSTOM INDICATORS
        //iterate of custom indicators dictionary to get values of custom lines
        // var customIndicator = {name: key, series: null}
        indList.forEach(function (item) {
            var ind = param.seriesData.get(item.series)
            if (ind !== undefined) { firstRow.innerHTML += name(item.name) + val(ind.value.toFixed(3))}
        }); 
    }
    else {
    firstRow.innerHTML = '';
    }
}

function initialize_chart() {
    $('#chartContainerInner').addClass("show");
    //PUVODNI BILY MOD
    //var chartOptions = { width: 1045, height: 600, leftPriceScale: {visible: true}}

    //TMAVY MOD
    var chartOptions = { width: 1080,
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

//https://www.w3schools.com/jsref/jsref_tolocalestring.asp
function format_date(datum) {
    //const options = { weekday: 'long', year: 'numeric', month: 'numeric', day: 'numeric', };
    const options = {dateStyle: "short", timeStyle: "short"}
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