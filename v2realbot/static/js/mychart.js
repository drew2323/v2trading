//const chartOptions = { layout: { textColor: 'black', background: { type: 'solid', color: 'white' } } };
const chartOptions = { width: 1045, height: 600, leftPriceScale: {visible: true}}
const chart = LightweightCharts.createChart(document.getElementById('chart'), chartOptions);
chart.applyOptions({ timeScale: { visible: true, timeVisible: true, secondsVisible: true }, crosshair: {
    mode: LightweightCharts.CrosshairMode.Normal, labelVisible: true
}})
const candlestickSeries = chart.addCandlestickSeries({ lastValueVisible: true, priceLineWidth:2, priceLineColor: "red", priceFormat: { type: 'price', precision: 2, minMove: 0.01 }});
candlestickSeries.priceScale().applyOptions({
    scaleMargins: {
        top: 0.1, // highest point of the series will be 10% away from the top
        bottom: 0.4, // lowest point will be 40% away from the bottom
    },
});


const volumeSeries = chart.addHistogramSeries({title: "Volume", color: '#26a69a', priceFormat: {type: 'volume'}, priceScaleId: ''});
volumeSeries.priceScale().applyOptions({
    // set the positioning of the volume series
    scaleMargins: {
        top: 0.7, // highest point of the series will be 70% away from the top
        bottom: 0,
    },
});

const vwapSeries = chart.addLineSeries({
//    title: "vwap",
    color: '#2962FF',
    lineWidth: 1,
    lastValueVisible: false
})

chart.timeScale().fitContent();

//TBD dynamicky zobrazovat vsechny indikatory
//document.getElementById('chart').style.display = 'inline-block';
var legendlist = document.getElementById('legend');
var firstRow = document.createElement('div');
firstRow.innerText = '-';
// firstRow.style.color = 'white';
legendlist.appendChild(firstRow);

function pad(n) {
	var s = ('0' + n);
	return s.substr(s.length - 2);
}

chart.subscribeCrosshairMove((param) => {
	if (param.time) {
		const data = param.seriesData.get(vwapSeries);
		const vwap = data.value !== undefined ? data.value : data.close;
        const bars = param.seriesData.get(candlestickSeries);
        const volumes = param.seriesData.get(volumeSeries);
        firstRow.innerText = "";
        //iterate of custom indicators dictionary to get values of custom lines
        // var customIndicator = {name: key, series: null}
        indList.forEach(function (item) {
            const ind = param.seriesData.get(item.series)
            firstRow.innerText += item.name + " " + ind.value + " ";
        });

		firstRow.innerText += ' vwap' + '  ' + vwap.toFixed(2) + " O" + bars.open + " H" + bars.high + " L" + bars.low + " C" + bars.close + " V" + volumes.value + "";
	}
  else {
  	firstRow.innerText = '-';
  }
});
