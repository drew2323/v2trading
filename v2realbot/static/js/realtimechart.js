
function populate_real_time_chart() {
    if (chart !== null) {
        chart.remove();
        clear_status_header();
    }

    initialize_chart()
    intitialize_candles()
    initialize_vwap()
    initialize_volume()

    chart.subscribeClick(param => {
        //display timestamp in trade-timestamp input field
        $('#trade-timestamp').val(param.time)
    });

    chart.subscribeCrosshairMove((param) => {
        firstRow.style.color = 'white';
        update_chart_legend(param);
    });
}

function pad(n) {
	var s = ('0' + n);
	return s.substr(s.length - 2);
}
