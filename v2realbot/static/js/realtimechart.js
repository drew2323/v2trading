
function populate_real_time_chart() {
    cleanup_chart()
    initialize_chart()
    intitialize_candles()
    initialize_vwap()
    initialize_volume()
    initialize_statusheader()

    chart.subscribeClick(param => {
        //display timestamp in trade-timestamp input field
        $('#trade-timestamp').val(param.time);
        toggle_vertical_line(param.time);
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
