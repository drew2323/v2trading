
API_KEY = localStorage.getItem("api-key")
var chart = null
var colors = ["#8B1874","#B71375","#B46060","#61c740","#BE6DB7","#898121","#4389d9","#00425A","#B5D5C5","#e61957","#8B1874","#B71375","#B46060","#61c740","#BE6DB7","#898121","#4389d9","#00425A","#B5D5C5","#e61957"]
var reset_colors = ["#8B1874","#B71375","#B46060","#61c740","#BE6DB7","#898121","#4389d9","#00425A","#B5D5C5","#e61957","#8B1874","#B71375","#B46060","#61c740","#BE6DB7","#898121","#4389d9","#00425A","#B5D5C5","#e61957"]
var indList = []
var verticalSeries=null
var candlestickSeries = null
var volumeSeries = null
var vwapSeries = null
var statusBarConfig = JSON.parse(localStorage.getItem("statusBarConfig"));

if (statusBarConfig == null) {
  statusBarConfig = {}
}


const sorter = (a, b) => a.time > b.time ? 1 : -1;

indConfig = {}
settings = {}
settings
//ostatni indicatory nez vwap, volume a bary
indConfig = [ {name: "ema", titlevisible: false, embed: true, display: true, priceScaleId: "right", lastValueVisible: false},
              {name: "tick_volume", histogram: true, titlevisible: true, embed: true, display: true, priceScaleId: '', lastValueVisible: false},
              {name: "tick_price", titlevisible: true, embed: true, display: true, priceScaleId: "right", lastValueVisible: false},
              {name: "ivwap", titlevisible: true, embed: true, display: false, priceScaleId: "right", lastValueVisible: false},
              {name: "slope", titlevisible: true, embed: true, display: false, priceScaleId: "left", lastValueVisible: false},
              {name: "slopeNEW", titlevisible: true, embed: true, display: false, priceScaleId: "left", lastValueVisible: false},
              {name: "slope10", titlevisible: true, embed: true, display: true, priceScaleId: "left", lastValueVisible: false},
              {name: "slope20", titlevisible: true, embed: true, display: true, priceScaleId: "left", lastValueVisible: false},
              {name: "slope10puv", titlevisible: true, embed: true, display: true, priceScaleId: "left", lastValueVisible: false},
              {name: "slopeS", titlevisible: true, embed: true, display: true, priceScaleId: "left", lastValueVisible: false},
              {name: "slopeLP", titlevisible: true, embed: true, display: true, priceScaleId: "left", lastValueVisible: false},
              {name: "slopeMA", titlevisible: true, embed: true, display: true, priceScaleId: "left", lastValueVisible: false},
              {name: "slow_slope", titlevisible: true, embed: true, display: false, priceScaleId: "left", lastValueVisible: false},
              {name: "slow_slopeMA", titlevisible: true, embed: true, display: true, priceScaleId: "left", lastValueVisible: false},
              {name: "emaSlow", titlevisible: true, embed: true, display: true, priceScaleId: "right", lastValueVisible: false},
              {name: "emaFast", titlevisible: true, embed: true, display: true, priceScaleId: "right", lastValueVisible: false},
              {name: "RSI14", titlevisible: true, embed: true, display: true, priceScaleId: "middle", lastValueVisible: false},
              {name: "CRSI", titlevisible: true, embed: true, display: true, priceScaleId: "middle", lastValueVisible: false},
              {name: "aroon", titlevisible: true, embed: true, display: true, priceScaleId: "middle", lastValueVisible: false},
              {name: "apo", titlevisible: true, embed: true, display: true, priceScaleId: "middle", lastValueVisible: false},
              {name: "ppo", titlevisible: true, embed: true, display: true, priceScaleId: "middle", lastValueVisible: false},
              {name: "stoch2", titlevisible: true, embed: true, display: true, priceScaleId: "middle", lastValueVisible: false},
              {name: "sec_price", titlevisible: true, embed: true, display: true, priceScaleId: "right", lastValueVisible: false},]


function initialize_statusheader() {
    
    var rows = 2;
    var columns = 4;
    console.log(JSON.stringify(statusBarConfig))

    // Create the grid table
    var gridTable = document.getElementById('statusHeaderTool');

    var cntid = 0

    for (var i = 0; i < rows; i++) {
      var row = document.createElement('tr');

      for (var j = 0; j < columns; j++) {
        cntid++
        var cell = document.createElement('td');
        cell.className = "statustd";
        var div = document.createElement('div');
        var cellid = "status" + cntid
        div.id = cellid;
        
                
        var input = document.createElement('input');
        input.id = cntid;
        input.type = 'text';
        input.style.display = "none";
        if (statusBarConfig !== null && statusBarConfig[cntid]) {
            //div.style.backgroundColor = 'red';
            div.textContent = "set";
            input.value = statusBarConfig[cntid];
          }

        cell.addEventListener('click', function() {
          var inputValue = this.querySelector('input').value;
          //this.querySelector('div').textContent = inputValue;
          this.querySelector('div').style.display = 'none';
          this.querySelector('input').style.display = 'block';
          this.querySelector('input').focus();
        });

        input.addEventListener('blur', function() {
          this.style.display = 'none';
          //this.previousElementSibling.textContent = inputValue;
          this.previousElementSibling.style.display = 'block';
          if (this.value !== "") {
            statusBarConfig[this.id] = this.value;
            }
          else {
            delete statusBarConfig[this.id]
          }
          if (statusBarConfig[this.id]) {
            this.previousElementSibling.textContent = "set"
            //this.previousElementSibling.style.backgroundColor = 'red';
          }
          else {
            this.previousElementSibling.style.backgroundColor = 'transparent';
          }
          console.log("potom", JSON.stringify(statusBarConfig))
          localStorage.setItem("statusBarConfig", JSON.stringify(statusBarConfig));
        });

        cell.appendChild(div);
        cell.appendChild(input);
        row.appendChild(cell);
      }

      gridTable.appendChild(row);
    }
    


}


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
            var visibility = item.series.options().visible;
            if (ind !== undefined && visibility) { firstRow.innerHTML += name(item.name, color) + val(ind.value.toFixed(3), color)}
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
    candlestickSeries = chart.addCandlestickSeries({ lastValueVisible: false, priceLineWidth:1, priceLineColor: "red", priceFormat: { type: 'price', precision: 3, minMove: 0.005 }});
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

function remove_indicator_buttons() {
  var elem1 = document.getElementById("indicatorsButtons");
  elem1.remove()
}

function populate_indicator_buttons(def) {
	var buttonElement = document.createElement('div');
  buttonElement.id = "indicatorsButtons"
	buttonElement.classList.add('switcher');

    indList.forEach(function (item, index) {
		var itemEl = document.createElement('button');
		itemEl.innerText = item.name;
        itemEl.id = "IND"+index;
        itemEl.style.color = item.series.options().color;
		itemEl.classList.add('switcher-item');
    if (def) {
		itemEl.classList.add('switcher-active-item');
    }
		itemEl.addEventListener('click', function() {
			onItemClicked1(index);
		});
		buttonElement.appendChild(itemEl);
	});

  //create toggle all button
  var itemEl = document.createElement('button');
  itemEl.innerText = "all"
  itemEl.classList.add('switcher-item');
  if (def) {
  itemEl.classList.add('switcher-active-item');
  }
  itemEl.addEventListener('click', function() {
    onResetClicked();
  });
  buttonElement.appendChild(itemEl);

	function onResetClicked() {
    indList.forEach(function (item, index) {
      vis = true;
      const elem = document.getElementById("IND"+index);
      if (elem.classList.contains("switcher-active-item")) {
          vis = false;
      }      
      elem.classList.toggle("switcher-active-item");
      indList[index].series.applyOptions({
          visible: vis });
    })
  }

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

// function compareObjects(obj1, obj2) {
//     const diff = {};
  
//     for (let key in obj1) {
//       if (typeof obj1[key] === 'object' && typeof obj2[key] === 'object') {
//         if (Array.isArray(obj1[key]) && Array.isArray(obj2[key])) {
//           if (!arraysAreEqual(obj1[key], obj2[key])) {
//             diff[key] = obj2[key];
//           }
//         } else {
//           const nestedDiff = compareObjects(obj1[key], obj2[key]);
//           if (Object.keys(nestedDiff).length > 0) {
//             diff[key] = nestedDiff;
//           }
//         }
//       } else if (obj1[key] !== obj2[key]) {
//         diff[key] = obj2[key];
//       }
//     }
  
//     return diff;
//   }
  
function compareObjects(obj1, obj2) {
  const diff = {};

  for (let key in obj1) {
    if (!(key in obj2)) {
      diff[key] = obj1[key];
      continue;
    }

    if (typeof obj1[key] === 'object' && typeof obj2[key] === 'object') {
      if (Array.isArray(obj1[key]) && Array.isArray(obj2[key])) {
        if (!arraysAreEqual(obj1[key], obj2[key])) {
          diff[key] = obj2[key];
        }
      } else {
        const nestedDiff = compareObjects(obj1[key], obj2[key]);
        if (Object.keys(nestedDiff).length > 0) {
          diff[key] = nestedDiff;
        }
      }
    } else if (obj1[key] !== obj2[key]) {
      diff[key] = obj2[key];
    }
  }

  for (let key in obj2) {
    if (!(key in obj1)) {
      diff[key] = obj2[key];
    }
  }

  return diff;
}



  function arraysAreEqual(arr1, arr2) {
    if (arr1.length !== arr2.length) {
      return false;
    }
  
    for (let i = 0; i < arr1.length; i++) {
      if (typeof arr1[i] === 'object' && typeof arr2[i] === 'object') {
        const nestedDiff = compareObjects(arr1[i], arr2[i]);
        if (Object.keys(nestedDiff).length > 0) {
          return false;
        }
      } else if (arr1[i] !== arr2[i]) {
        return false;
      }
    }
  
    return true;
  }
  
  function generateHTML(obj, diff, indent = '') {
    let html = '';
  
    for (let key in obj) {
      const value = obj[key];
  
      if (typeof value === 'object' && value !== null) {
        const nestedDiff = diff[key] || {};
        const nestedIndent = indent + '  ';
        if (Array.isArray(value)) {
          html += `${indent}"${key}": [\n${generateHTMLArray(value, nestedDiff, nestedIndent)}${indent}],\n`;
        } else {
          html += `${indent}"${key}": {\n${generateHTML(value, nestedDiff, nestedIndent)}${indent}},\n`;
        }
      } else {
        if (key in diff) {
          html += `${indent}"${key}": <span style="background-color: yellow;">${JSON.stringify(value)}</span>,\n`;
        } else {
          html += `${indent}"${key}": ${JSON.stringify(value)},\n`;
        }
      }
    }
  
    return html;
  }
  
  function generateHTMLArray(arr, diff, indent) {
    let html = '';
  
    for (let i = 0; i < arr.length; i++) {
      const value = arr[i];
      if (typeof value === 'object' && value !== null) {
        const nestedDiff = diff[i] || {};
        const nestedIndent = indent + '  ';
        if (Array.isArray(value)) {
          html += `${indent}[\n${generateHTMLArray(value, nestedDiff, nestedIndent)}${indent}],\n`;
        } else {
          html += `${indent}{\n${generateHTML(value, nestedDiff, nestedIndent)}${indent}},\n`;
        }
      } else {
        if (i in diff) {
          html += `${indent}<span style="background-color: yellow;">${JSON.stringify(value)}</span>,\n`;
        } else {
          html += `${indent}${JSON.stringify(value)},\n`;
        }
      }
    }
  
    return html;
  }