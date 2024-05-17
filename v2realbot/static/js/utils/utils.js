//general util functions all accross


API_KEY = localStorage.getItem("api-key")
var chart = null

//puvodni mene vyrazne barvy
// var colors  = ["#8B1874","#B71375","#B46060","#61c740","#BE6DB7","#898121","#4389d9","#B5D5C5","#e61957","#7B0E60","#9B2888","#BD38A0","#A30F68","#6E0B50","#CA2183","#E6319B","#A04C54","#643848","#CA7474","#E68D8D","#4F9C34","#3B7128","#73DF4D","#95EF65","#A857A4","#824690","#D087CC","#FF3775","#E2A1DF","#79711B","#635D17","#99912B","#B1A73D","#3779C9","#A60F3B","#2B68B3","#5599ED","#77A9F7","#004C67","#00687D","#A1C6B5","#8CC6A5","#C9E6D5","#E4F6EA","#D2144A","#FA2463","#8B1874","#B71375","#B46060","#61c740","#BE6DB7","#898121","#4389d9","#B5D5C5","#e61957","#7B0E60","#9B2888","#BD38A0","#A30F68","#6E0B50","#CA2183","#E6319B","#A04C54","#643848","#CA7474","#E68D8D","#4F9C34","#3B7128","#73DF4D","#95EF65","#A857A4","#824690","#D087CC","#FF3775","#E2A1DF","#79711B","#635D17","#99912B","#B1A73D","#3779C9","#A60F3B","#2B68B3","#5599ED","#77A9F7","#004C67","#00687D","#A1C6B5","#8CC6A5","#C9E6D5","#E4F6EA","#D2144A","#FA2463"];
// var reset_colors  = ["#8B1874","#B71375","#B46060","#61c740","#BE6DB7","#898121","#4389d9","#B5D5C5","#e61957","#7B0E60","#9B2888","#BD38A0","#A30F68","#6E0B50","#CA2183","#E6319B","#A04C54","#643848","#CA7474","#E68D8D","#4F9C34","#3B7128","#73DF4D","#95EF65","#A857A4","#824690","#D087CC","#FF3775","#E2A1DF","#79711B","#635D17","#99912B","#B1A73D","#3779C9","#A60F3B","#2B68B3","#5599ED","#77A9F7","#004C67","#00687D","#A1C6B5","#8CC6A5","#C9E6D5","#E4F6EA","#D2144A","#FA2463","#8B1874","#B71375","#B46060","#61c740","#BE6DB7","#898121","#4389d9","#B5D5C5","#e61957","#7B0E60","#9B2888","#BD38A0","#A30F68","#6E0B50","#CA2183","#E6319B","#A04C54","#643848","#CA7474","#E68D8D","#4F9C34","#3B7128","#73DF4D","#95EF65","#A857A4","#824690","#D087CC","#FF3775","#E2A1DF","#79711B","#635D17","#99912B","#B1A73D","#3779C9","#A60F3B","#2B68B3","#5599ED","#77A9F7","#004C67","#00687D","#A1C6B5","#8CC6A5","#C9E6D5","#E4F6EA","#D2144A","#FA2463"];

// function generateColorPalette(numColors) {
//   const palette = [];
//   let lastColor = null;
//   for (let i = 0; i < numColors; i++) {
//       let color = generateRandomColor();
//       while (isColorDark(color) || areColorsTooSimilar(color, lastColor)) {
//           color = generateRandomColor();
//       }
//       lastColor = color;
//       palette.push(color);
//   }
//   return palette;
// }

// function generateRandomColor() {
//     const letters = '0123456789ABCDEF';
//     let color = '#';
//     for (let i = 0; i < 6; i++) {
//         color += letters[Math.floor(Math.random() * 16)];
//     }
//     return color;
// }

// function areColorsTooSimilar(color1, color2) {
//   if (!color1 || !color2) {
//       return false;
//   }
//   // Calculate the color difference
//   const diff = parseInt(color1.substring(1), 16) - parseInt(color2.substring(1), 16);
//   // Define a threshold for color difference (you can adjust this value)
//   const threshold = 500;
//   return Math.abs(diff) < threshold;
// }

// function isColorDark(color) {
//     const hexColor = color.replace("#", "");
//     const r = parseInt(hexColor.substr(0, 2), 16);
//     const g = parseInt(hexColor.substr(2, 2), 16);
//     const b = parseInt(hexColor.substr(4, 2), 16);
//     const brightness = (r * 299 + g * 587 + b * 114) / 1000;
//     return brightness < 128 || brightness > 140; // You can adjust the threshold for what you consider 'dark'
// }

// colors = generateColorPalette(255)
// reset_colors = colors

// console.log(`"${colors.join("\", \"")}"`); 

// // pekne vygenrovane pomoci kodu vyse
var colors = ["#63AA57", "#8F8AB0", "#4CAA4E", "#E24AEE", "#D06AA6", "#7891BA", "#A39A34", "#8A94A2", "#8887A7", "#61BB2F", "#FD569D", "#1EB6E1",
"#379AC9", "#FD6F2E", "#8C9858", "#39A4A3", "#6D97F4", "#1ECB01", "#FA5B16", "#A6891C", "#48CF10", "#D27B26", "#D56B55", "#FE3AB8", "#E35C51",
"#EC4FE6", "#E250A3", "#BA618E", "#1BC074", "#C57784", "#888BC5", "#4FA452", "#80885C", "#B97272", "#33BF98", "#B7961D", "#A07284", "#02E54E",
"#AF7F35", "#F852EF", "#6D955B", "#E0676E", "#F73DEC", "#CE53FD", "#9773D3", "#649E81", "#D062CE", "#AB73E7", "#A4729C", "#E76A07", "#E85CCB",
"#A16FB1", "#4BB859", "#B25EE2", "#8580CE", "#A275EF", "#AC9245", "#4D988D", "#B672C9", "#4CA96E", "#C9873E", "#5BB147", "#10C783", "#D7647D",
"#CB893A", "#A586BA", "#28C0A2", "#61A755", "#0EB7C5", "#2DADBC", "#17BB71", "#2BC733", "#2BB890", "#F04EF8", "#699580", "#A88809", "#EB3FF6",
"#A75ED3", "#859171", "#BB6285", "#81A147", "#AD7CD2", "#65B630", "#C9616C", "#BD5EFA", "#7A9F30", "#2AB6AB", "#FC496A", "#687FC7", "#DB40E7",
"#07BCE9", "#509F63", "#EC4FDD", "#A079BE", "#C17297", "#E447C2", "#E95AD9", "#9FA01E", "#7E86CF", "#21E316", "#1CABF9", "#17C24F", "#9C9254",
"#C97994", "#4BA9DA", "#0DD595", "#13BEA8", "#C2855D", "#DF6C13", "#60B370", "#0FC3F6", "#C1830E", "#3AC917", "#0EBBB0", "#CC50B4", "#B768EC",
"#D47F49", "#B47BC5", "#38ADBD", "#05DC53", "#44CD4E", "#838E65", "#49D70F", "#2DADBE", "#2CB0C9", "#DA703E", "#06B5CA", "#7BAF3E", "#918E79",
"#2AA5E5", "#C37F5E", "#07B8C9", "#4CBA27", "#E752C6", "#7F93B2", "#4798CD", "#45AA4C", "#4DB666", "#7683A7", "#758685", "#4B9FAD", "#9280FD",
"#6682DD", "#42ACBE", "#C1609F", "#D850DB", "#649A62", "#54CC22", "#AD81C1", "#BF7A43", "#0FCEA5", "#D06DAF", "#87799B", "#4DA94E", "#2FD654",
"#07D587", "#21CF0C", "#03CF34", "#42C771", "#D563CD", "#6D9E9A", "#C76C59", "#68B368", "#11BCE5", "#0DCFB3", "#9266D8", "#BF67F6", "#88A04E",
"#73BE17", "#67B437", "#8586E4", "#9F8749", "#479CA5", "#CC777E", "#4FAF46", "#9D9836", "#918DAF", "#D167B8", "#6F9DA5", "#2BB167", "#16B8BC",
"#B4861F", "#A08487", "#67B357", "#5CAA5C", "#20CA49", "#D18813", "#15D63F", "#C8618F", "#887E92", "#21C457", "#4EA8CE", "#53BE49", "#5A86D5",
"#BD7E4E", "#27B0A1", "#33CF42", "#709083", "#38A8DE", "#4CA762", "#1EA4FF", "#DE3EE4", "#70A860", "#39A3C8", "#6BBB39", "#F053F4", "#8C7FB5",
"#969F21", "#B19841", "#E57148", "#C25DA7", "#6DA979", "#B27D73", "#7F9786", "#41AC99", "#C58848", "#948F9E", "#6BB620", "#81AB3B", "#09DE44",
"#43A9D2", "#41B0D7", "#20ACAA", "#649FCB", "#CD8345", "#A88669", "#3EA5E7", "#F36A19", "#E06B48", "#8388BD", "#EC6153", "#639082", "#52CA32",
"#878BAA", "#02BCDB", "#828FD9", "#3DC07F", "#29D46A", "#9C7CC1", "#EB7713", "#F95F6A", "#E25F4C", "#589994", "#D45AB7", "#DE66AB", "#B8715F",
"#E850F4", "#FB6420", "#C2832C", "#6383C5", "#D57A58", "#EF652C", "#02D71A", "#ED664D", "#60A526"]

var reset_colors = colors.slice()

var indList = []
var verticalSeries=null
var candlestickSeries = null
var volumeSeries = null
var vwapSeries = null
var statusBarConfig = JSON.parse(localStorage.getItem("statusBarConfig"));
if (statusBarConfig == null) {
  statusBarConfig = {}
}

var index_ind = 0


const sorter = (a, b) => a.time > b.time ? 1 : -1;
var ind_editor = null
var indConfig = null
settings = {}
settings
//ostatni indicatory nez vwap, volume a bary
var indConfig_default = [ {name: "ema", titlevisible: false, embed: true, display: true, priceScaleId: "right", lastValueVisible: false},
              {name: "ema20", titlevisible: false, embed: true, display: true, priceScaleId: "right", lastValueVisible: false},              
              {name: "tick_volume", histogram: true, titlevisible: true, embed: true, display: true, priceScaleId: '', lastValueVisible: false},
              {name: "tick_price", titlevisible: true, embed: true, display: true, priceScaleId: "right", lastValueVisible: false},
              {name: "ivwap", titlevisible: true, embed: true, display: false, priceScaleId: "right", lastValueVisible: false},
              {name: "slope", titlevisible: true, embed: true, display: false, priceScaleId: "left", lastValueVisible: false},
              {name: "slopeNEW", titlevisible: true, embed: true, display: false, priceScaleId: "left", lastValueVisible: false},
              {name: "slope10", titlevisible: true, embed: true, display: true, priceScaleId: "left", lastValueVisible: false},
              {name: "slope20", titlevisible: true, embed: true, display: true, priceScaleId: "left", lastValueVisible: false},
              {name: "slope10MA", titlevisible: true, embed: true, display: true, priceScaleId: "left", lastValueVisible: false},
              {name: "slope20MA", titlevisible: true, embed: true, display: true, priceScaleId: "left", lastValueVisible: false},
              {name: "slope30", titlevisible: true, embed: true, display: true, priceScaleId: "left", lastValueVisible: false},
              {name: "slope30MA", titlevisible: true, embed: true, display: true, priceScaleId: "left", lastValueVisible: false},
              {name: "slopeLP", titlevisible: true, embed: true, display: true, priceScaleId: "left", lastValueVisible: false},
              {name: "slopeMA", titlevisible: true, embed: true, display: true, priceScaleId: "left", lastValueVisible: false},
              {name: "slope720", titlevisible: true, embed: true, display: true, priceScaleId: "left", lastValueVisible: false},
              {name: "slope720MA", titlevisible: true, embed: true, display: true, priceScaleId: "left", lastValueVisible: false},
              {name: "slow_slope", titlevisible: true, embed: true, display: false, priceScaleId: "left", lastValueVisible: false},
              {name: "slow_slopeMA", titlevisible: true, embed: true, display: true, priceScaleId: "left", lastValueVisible: false},
              {name: "emaSlow", titlevisible: true, embed: true, display: true, priceScaleId: "right", lastValueVisible: false},
              {name: "emaFast", titlevisible: true, embed: true, display: true, priceScaleId: "right", lastValueVisible: false},
              {name: "RSI14", titlevisible: true, embed: true, display: true, priceScaleId: "middle", lastValueVisible: false},
              {name: "RSI14MA", titlevisible: true, embed: true, display: true, priceScaleId: "middle", lastValueVisible: false},
              {name: "CRSI", titlevisible: true, embed: true, display: true, priceScaleId: "middle", lastValueVisible: false},
              {name: "aroon", titlevisible: true, embed: true, display: true, priceScaleId: "middle", lastValueVisible: false},
              {name: "apo", titlevisible: true, embed: true, display: true, priceScaleId: "middle", lastValueVisible: false},
              {name: "ppo", titlevisible: true, embed: true, display: true, priceScaleId: "middle", lastValueVisible: false},
              {name: "stoch2", titlevisible: true, embed: true, display: true, priceScaleId: "middle", lastValueVisible: false},
              {name: "sec_price", titlevisible: true, embed: true, display: true, priceScaleId: "right", lastValueVisible: false},]
//console.log(JSON.stringify(indConfig_default, null,null, 2))

function initialize_statusheader() {
    
    var rows = 2;
    var columns = 4;
    console.log("initialiting statusheader")
    console.log(JSON.stringify(statusBarConfig))

    // Create the grid table
    var gridTable = document.getElementById('statusHeaderTool');
    gridTable.style.display = 'flex';

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

//pokud neni v configuraci vracime default, pro tickbased (1) vracime embed false pokud je globalni ()
function get_ind_config(indName, tick_based = 0) {

    //def settings
    def = {name: "ema", titlevisible: false, embed: true, display: true, priceScaleId: "middle", lastValueVisible: false}


    //WORKAROUND to DISABLE TICK INDS - skip config
    var hideTickIndicators = localStorage.getItem('hideTickIndicators');
    console.log("jsme v IND CONFIG. hodnota hideTickIndicators =",hideTickIndicators)
    //pokud jde tick_based a mam v local storage nastaveno hideTickInds pak nastavuju embed na false - coz nezobrazi tickindikatory
   
    if ((tick_based == 1) && hideTickIndicators && hideTickIndicators == "true") {
      def.embed = false
      console.log("pro",indName,"vracime embed false")
      return def
    }
    //END WORKAROUND    

    if (indConfig == null) {
      indConfig = get_from_config("indConfig", indConfig_default)
    }

    const i = indConfig.findIndex(e => e.name === indName);
    if (i>-1)
        {
            return indConfig[i]
        }
    return def
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
          if (item.series) {
            var ind = param.seriesData.get(item.series)
            var color = item.series.options().color;
            var visibility = item.series.options().visible;
            if (ind !== undefined && visibility) { firstRow.innerHTML += name(item.name, color) + val(ind.value.toFixed(3), color)}
          }
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
        slLine = []
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
    var chartOptions = { width: 1024,
        height: 480,
        leftPriceScale: {visible: true},
        layout: {
            background: {
                type: 'solid',
                // color: '#2a2e39',
                color: '#151824'
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
    chart.applyOptions({ timeScale: { visible: true, timeVisible: true, secondsVisible: true, minBarSpacing: 0.003}, crosshair: {
        mode: LightweightCharts.CrosshairMode.Normal, labelVisible: true
    }})
    console.log("chart intiialized")
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

//pomocna funkce pro vytvoreni buttonu indiaktoru
function create_indicator_button(item, def, noaction = false) {
      // //div pro kazdy button
      // var buttonContainer = document.createElement('div');
      // buttonContainer.classList.add('button-container');
  
      index = item.indId

      var itemEl = document.createElement('button');
      itemEl.innerText = item.name;
          itemEl.id = "IND"+item.indId;
          itemEl.title = item.cnf
          itemEl.style.color = item.series.options().color;
          //pokud jde o pridanou on the fly - vybarvime jinak
          if (item.instant) {
            itemEl.style.outline = "solid 1px"
          }
      itemEl.classList.add('switcher-item');
      if (def) {
      itemEl.classList.add('switcher-active-item');
      }
  
      // //jeste vytvorime pod tim overlay a nad to az dame linky
      // // Create the overlay element.
      // const overlay = document.createElement("div");
      // overlay.id = "OVR"+index;
      // overlay.classList.add("overlayLayer");
      // overlay.classList.add("hidden");
  
      // // Create the action buttons.
      // const actionShow = document.createElement("div");
      // actionShow.id = "actionShow";
      // actionShow.textContent = "Show";
  
      //nepouzivat pro urcite pripady (napr. u hlavnich multioutputu indikatoru) - pouze nese predpis(right click) a left clickem zobrazi outputy
      if (!noaction) {
        itemEl.addEventListener('click', function() {
          onItemClickedToggle(item.indId);
        });
      }
  
      // const actionEdit = document.createElement("div");
      // actionEdit.id = "actionEdit";
      // actionEdit.textContent = "Edit";
  
      itemEl.addEventListener('contextmenu', function(e) {
        //edit modal zatim nemame
        onItemClickedEdit(e, item.indId);
      });
  
      // // Append the action buttons to the overlay.
      // overlay.appendChild(actionShow);
      // overlay.appendChild(actionEdit);
  
      // // Add a hover listener to the button.
      // itemEl.addEventListener("mouseover", toggleOverlay(index));
      // itemEl.addEventListener("mouseout", toggleOverlay(index));
  
      // buttonContainer.appendChild(itemEl)
      // buttonContainer.appendChild(overlay)
      return itemEl
}

//pomocne funkce
function onResetClicked() {
  indList.forEach(function (item, index) {
    vis = true;
    const elem = document.getElementById("IND"+item.indId);
    if (elem.classList.contains("switcher-active-item")) {
        vis = false;
    }      
    elem.classList.toggle("switcher-active-item");
    if (obj.series) {
    obj.series.applyOptions({
        visible: vis });
    }
  })
  store_activated_buttons_state();
}


function generateIndicators(e) {
  store_activated_buttons_state();

  ind_tom = ""
  indList.forEach(function (item, index) {
    if (activatedButtons.includes(item.name)) {
      console.log(item)
      ind_tom += "\n[stratvars.indicators."+item.name+"]\n" + item.cnf
    }
  });

  if (ind_editor) {
    ind_editor.dispose()
  }
  require(["vs/editor/editor.main"], () => {
    ind_editor = monaco.editor.create(document.getElementById('indicatorTOML_editor'), {
        value: ind_tom,
        language: 'toml',
        theme: 'tomlTheme-dark',
        automaticLayout: true
    });
    });
  $('#deleteIndicatorButton').hide();
  $('#saveIndicatorButton').hide();
  window.$('#indicatorModal').modal('show');
}

//editace indikatoru, vcetne vytvoreni noveho
function onItemClickedEdit(e, index) {
  if (ind_editor) {
    ind_editor.dispose()
  }
  title = `#[stratvars.indicators.name]
  `
  const elem = document.getElementById("IND"+index);
  //console.log("element",elem)
  //jde o update
  if (elem) {
    elem.classList.replace('switcher-item', 'switcher-item-highlighted');
    $('#indicatorName').val(elem.textContent)
    $('#indicatorNameTitle').text(elem.textContent)
    title = elem.title
  }
  //jde o novy zaznam - davame pryc delete
  else {
    $('#deleteIndicatorButton').hide();
  }
  e.preventDefault()
  //$('#stratvar_id').val(row.id);
  $('#indicatorId').val(index)

  require(["vs/editor/editor.main"], () => {
      ind_editor = monaco.editor.create(document.getElementById('indicatorTOML_editor'), {
          value: title,
          language: 'toml',
          theme: 'tomlTheme-dark',
          automaticLayout: true
      });
      });
  window.$('#indicatorModal').modal('show');
}

//togle profit line
function profitLineToggle() {
  vis = true;
  const elem = document.getElementById("profitLine");
  if (elem.classList.contains("switcher-active-item")) {
      vis = false;
  }      
  elem.classList.toggle("switcher-active-item");
  //v ifu kvuli workaroundu
  if (profitLine) {
    profitLine.applyOptions({
      visible: vis });
  }
}

//togle go wide
function toggleWide() {
  width = 1600;
  const elem = document.getElementById("goWide");
  const msgContainer = document.getElementById("msgContainer");
  const msgContainerInner = document.getElementById("msgContainerInner");
  const clrButton = document.getElementById("clrButton");

  if (elem.classList.contains("switcher-active-item")) {
      width = 1024;
      msgContainer.removeAttribute("style");
      msgContainerInner.removeAttribute("style");
      clrButton.removeAttribute("style");
  } else
  {
    msgContainer.style.display = "block"
    msgContainerInner.style.display = "none"
    clrButton.style.display = "none"
  }      
  elem.classList.toggle("switcher-active-item");

  if (chart) {
    chart.applyOptions({ width: width});
    chart.timeScale().fitContent();
  }
}

//togle profit line
function toggleVolume() {
  vis = true;
  const elem = document.getElementById("volToggle");
  if (elem.classList.contains("switcher-active-item")) {
      vis = false;
  }      
  elem.classList.toggle("switcher-active-item");
  //v ifu kvuli workaroundu
  if (volumeSeries) {
    volumeSeries.applyOptions({
      visible: vis });
  }
}

//togle profit line
function toggleTick() {
  const elem = document.getElementById("tickToggle");
  if (elem.classList.contains("switcher-active-item")) {
    localStorage.setItem('hideTickIndicators', 'false');
  }
  else {
    localStorage.setItem('hideTickIndicators', 'true');
  }     
  elem.classList.toggle("switcher-active-item");

  //toggle repaint - click on change resolution
  var activeButton = document.querySelector('#changeResolution .switcher-active-item');

  // Click the button programmatically
  if (activeButton) {
      activeButton.click();
  }

}

//togle profit line
function mrkLineToggle() {
  vis = true;
  const elem = document.getElementById("mrkLine");
  if (elem.classList.contains("switcher-active-item")) {
      vis = false;
  }      
  elem.classList.toggle("switcher-active-item");
  //v ifu kvuli workaroundu
  if (markersLine) {
    markersLine.applyOptions({
      visible: vis });
  }
  if (slLine) {
    slLine.forEach((series, index, array) => {
      series.applyOptions({
        visible: vis });
    })
  }
}


function get_ind_by_id(indId) {
  return indList.find(obj => obj.indId === indId);
}

//toggle indiktoru
function onItemClickedToggle(index) {
      vis = true;
      const elem = document.getElementById("IND"+index);
      if (elem.classList.contains("switcher-active-item")) {
          vis = false;
      }      
      elem.classList.toggle("switcher-active-item");
      //v ifu kvuli workaroundu
      obj = get_ind_by_id(index)
      if (obj.series) {
        //console.log(obj.name, obj.series)
        obj.series.applyOptions({
            visible: vis });
      }
      //zatim takto workaround, pak vymyslet systemove pro vsechny tickbased indikatory
      tickIndicatorList = ["tick_price", "tick_volume"]
      if (tickIndicatorList.includes(obj.name)) {
        if (!vis && obj.series) {
          //console.log("pred", obj.name, obj.series)
          chart.removeSeries(obj.series)
          chart.timeScale().fitContent();
          obj.series = null
          //console.log("po", obj.name, obj.series)
        }
      }

}

//obalka pro collapsovatelny multioutput indicator button
function create_multioutput_button(item, def, active) {
  //encapsulating dic
  var multiOutEl = document.createElement('div');
  //multiOutEl.id = "tickIndicatorsButtons"
  multiOutEl.classList.add('multiOut');
  multiOutEl.classList.add('switcher-item');
  //pouze def - u main indikatoru nepamatujeme stav a pozadujeme noaction pro leftclick
  //def||active - ani def
  itemEl = create_indicator_button(item, false, true);
  //hlavni button ridi expand/collapse
  itemEl.setAttribute('data-bs-toggle', 'collapse');
  itemEl.setAttribute('data-bs-target', '.'+item.name);
  itemEl.setAttribute('aria-expanded', 'true');
  itemEl.setAttribute('role', 'button');
  //itemEl.setAttribute('aria-controls', 'IND6 IND7 IND8');            
  //itemEl.style.outline = 'dotted';
  itemEl.style.marginRight = '0px'

  //prirazeni mainu do divu
  multiOutEl.appendChild(itemEl); 
  
  //pokud nektery z multivstupu je aktivni, pak nastavuju vse expanded
  const isAnyActive = activatedButtons.some(element => item.returns.includes(element));

  item.returns.forEach(function (output_name,index) {
    active = false
    //find and process multioutput parameters
    const foundObject = indList.find(obj => obj.name == output_name);
    if (foundObject) {

      //aplikujeme remembered state
      if ((activatedButtons) && (activatedButtons.includes(output_name))) {
        active = true
      }

      console.log(foundObject.content); // Access and use the content
      itemEl = create_indicator_button(foundObject, def||active);

      itemEl.classList.add('collapse')
      //pokud je aktivni jakykoliv, expandujeme vsechny
      if (active || isAnyActive) {
        itemEl.classList.add('show')
      }
      itemEl.classList.add(item.name)
      itemEl.style.marginRight = '0px'

      multiOutEl.appendChild(itemEl);  
    }
  });

  return multiOutEl
}

//funkce pro vytvoreni buttonku indikatoru
function populate_indicator_buttons(def) {

  //vytvoreni outer button divu
	var buttonElement = document.createElement('div');
  buttonElement.id = "indicatorsButtons"
	buttonElement.classList.add('switcher');

  //incializujeme i div pro cbar indikator sekci
	var tickButtonElement = document.createElement('div');
  tickButtonElement.id = "tickIndicatorsButtons"
	tickButtonElement.classList.add('tickButtons');

    already_processed = [];
    //iterace nad indikatory a vytvareni buttonků
    indList.forEach(function (item, index) {
      index_ind = item.indId
      if (!already_processed.includes(item.name)) {
        active = false

        if ((activatedButtons) && (activatedButtons.includes(item.name))) {
          active = true
        }
        //bar indikatory jsou serazeny na zacarku
        if (item.type == 0) {
          //pokud jde o multiinput, pridame ihned souvisejici mutiinputy a vse dame do stejneho divu
          //(Object.keys(data[0]).length > 0)
          if (item.returns && item.returns.length > 0) {
            //prirazeni multiOut do buttonu
            multiOutEl = create_multioutput_button(item, def, active)

            buttonElement.appendChild(multiOutEl);  
            already_processed = already_processed.concat(item.returns)
          }
          else {
            //vytvoreni buttonku
            itemEl = create_indicator_button(item, def||active);
            //prirazeni do divu
            buttonElement.appendChild(itemEl);
          }
        }
        //ted zbyvaji tick barové a ty dáme do separátního divu
        else
        {
          //oper nejdriv multiinput
          if (item.returns && item.returns.length > 0) {

            //prirazeni multiOut do buttonu
            multiOutEl = create_multioutput_button(item, def, active)
            tickButtonElement.appendChild(multiOutEl);  
            already_processed = already_processed.concat(item.returns)
          }
          //standardni non multiinput
          else {
          //vytvoreni buttonku
          itemEl = create_indicator_button(item, def||active);
          tickButtonElement.appendChild(itemEl)
        }
      }
    }
	  });

    //nakonec pripojime cely div s tick based indicatory
    buttonElement.appendChild(tickButtonElement);

	var funcButtonElement = document.createElement('div');
  funcButtonElement.id = "funcIndicatorsButtons"
	funcButtonElement.classList.add('funcButtons');


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
  funcButtonElement.appendChild(itemEl);

  //button pro toggle profitu
  var itemEl = document.createElement('button');
  itemEl.innerText = "prof"
  itemEl.classList.add('switcher-item');
  itemEl.style.color = "#99912b"
  itemEl.id = "profitLine"
  itemEl.addEventListener('click', function(e) {
    profitLineToggle();
  });
  funcButtonElement.appendChild(itemEl);

    //button pro toggle fullscreenu
    var itemEl = document.createElement('button');
    itemEl.innerText = "wide"
    itemEl.classList.add('switcher-item');
    itemEl.style.color = "#99912b"
    itemEl.id = "goWide"
    itemEl.addEventListener('click', function(e) {
      toggleWide();
    });
    funcButtonElement.appendChild(itemEl);

    //button pro toggle fullscreenu
    var itemEl = document.createElement('button');
    itemEl.innerText = "vol"
    itemEl.classList.add('switcher-item');
    itemEl.classList.add('switcher-active-item');
    itemEl.style.color = "#99912b"
    itemEl.id = "volToggle"
    itemEl.addEventListener('click', function(e) {
      toggleVolume();
    });
    funcButtonElement.appendChild(itemEl);

    //button pro disable tickIndicatoru
    var itemEl = document.createElement('button');
    itemEl.innerText = "ticks off"
    itemEl.classList.add('switcher-item');
    var hideTickIndicators = localStorage.getItem('hideTickIndicators');
    console.log("init button, hodnota hideTickIndicators", hideTickIndicators)
    if (hideTickIndicators && hideTickIndicators == "true") {
      itemEl.classList.add('switcher-active-item');
    }
    itemEl.style.color = "#e0676e"
    itemEl.id = "tickToggle"
    itemEl.addEventListener('click', function(e) {
      toggleTick();
    });
    funcButtonElement.appendChild(itemEl);

  // //button pro toggle markeru nakupu/prodeju
  var itemEl = document.createElement('button');
  itemEl.innerText = "mrk"
  itemEl.classList.add('switcher-item');
  itemEl.classList.add('switcher-active-item');
  // if ((activatedButtons) && (!activatedButtons.includes("mrk"))) {
  // }
  // else {

  // }


  itemEl.style.color = "#99912b"
  itemEl.id = "mrkLine"

  // // Create an icon element
  // const iconEl = document.createElement('i');
  // // Set the icon class
  // iconEl.classList.add('bi');
  // iconEl.classList.add('bi-rainbow'); // Replace `icon-name` with the name of the icon you want to use
  // // Append the icon element to the button element
  // itemEl.appendChild(iconEl);

  itemEl.addEventListener('click', function(e) {
    mrkLineToggle();
  });

  funcButtonElement.appendChild(itemEl);

  //create plus button to create new button
  var itemEl = document.createElement('button');
  itemEl.innerText = "+"
  itemEl.classList.add('switcher-item');
  //na tomto je navesena jquery pro otevreni modalu
  itemEl.id = "button_addindicator"
  itemEl.addEventListener('click', function(e) {
    index_ind++
    onItemClickedEdit(e, index_ind);
  });
  funcButtonElement.appendChild(itemEl);

   //save indicator buttons - will generate indicators to stratvars
   var itemEl = document.createElement('button');
   itemEl.innerText = "generate"
   itemEl.classList.add('switcher-item');
   //na tomto je navesena jquery pro otevreni modalu
   itemEl.id = "save_indicators"
   itemEl.addEventListener('click', function(e) {
     index_ind++
     generateIndicators(e);
   });
   funcButtonElement.appendChild(itemEl);

   buttonElement.appendChild(funcButtonElement)

  return buttonElement;
}


//range switch pro chart https://jsfiddle.net/TradingView/qrb9a850/
function createSimpleSwitcher(items, activeItem, activeItemChangedCallback, data) {
	var switcherElement = document.createElement('div');
	switcherElement.classList.add('switcher');
  switcherElement.id = "changeResolution"
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
		// if (item === activeItem) {
		// 	return;
		// }

		intervalElements.forEach(function(element, index) {
			element.classList.toggle('switcher-active-item', items[index] === item);
		});

		activeItem = item;

		activeItemChangedCallback(item, data);
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
  // Convert input date to Eastern Time
  var dateInEastern = new Date(someDate.toLocaleString('en-US', { timeZone: 'America/New_York' }));
  //console.log("vstupuje ",someDate)
  //console.log("americky ",dateInEastern)
  // Get today's date in Eastern Time
  var todayInEastern = new Date(new Date().toLocaleString('en-US', { timeZone: 'America/New_York' }));

  return dateInEastern.getDate() === todayInEastern.getDate() &&
    dateInEastern.getMonth() === todayInEastern.getMonth() &&
    dateInEastern.getFullYear() === todayInEastern.getFullYear();
}  
//  function isToday(someDate) {
  
//     const today = new Date()
//     return someDate.getDate() == today.getDate() &&
//       someDate.getMonth() == today.getMonth() &&
//       someDate.getFullYear() == today.getFullYear()
//   }

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
    $("#statusArchId").text("")
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
Mousetrap.bind('q', function() { 
  $( "#button_report" ).trigger( "click" );
});

Mousetrap.bind('e', function() { 
    $( "#button_edit" ).trigger( "click" );
});
// Mousetrap.bind('a', function() { 
//     $( "#button_add" ).trigger( "click" );
// });
Mousetrap.bind('d', function() { 
    $( "#button_delete_arch" ).trigger( "click" );
});
Mousetrap.bind('b', function() { 
  $( "#button_delete_batch" ).trigger( "click" );
});
Mousetrap.bind('c', function() { 
    $( "#button_copy" ).trigger( "click" );
});
Mousetrap.bind('y', function() { 
  $( "#button_run" ).trigger( "click" );
});
Mousetrap.bind('r', function() { 
    $( "#button_runagain_arch" ).trigger( "click" );
});
Mousetrap.bind('p', function() { 
    $( "#button_pause" ).trigger( "click" );
});
Mousetrap.bind('s', function() { 
    $( "#button_edit_stratvars" ).trigger( "click" );
});
Mousetrap.bind('a', function() { 
  $( "#button_edit_arch" ).trigger( "click" );
});
Mousetrap.bind('j', function() { 
    $( "#button_add_json" ).trigger( "click" );
});
Mousetrap.bind('x', function() { 
    $( "#button_delete" ).trigger( "click" );
});
Mousetrap.bind('w', function() { 
  $( "#button_show_arch" ).trigger( "click" );
});

//ENTERS
// Mousetrap.bind('enter', function() { 
//   $( "#deletearchive" ).trigger( "click" );
// });
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