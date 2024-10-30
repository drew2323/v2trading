var tradeDetails = new Map();
var toolTip = null
var CHART_SHOW_TEXT = get_from_config("CHART_SHOW_TEXT", false)
// const myLibrary = _export;
// const TOML = window['j-toml']
//console.log("TOML je", window)
console.log("CHART_SHOW_TEXT archchart", CHART_SHOW_TEXT)
// var vwapSeries = null
// var volumeSeries = null
var markersLine = null
var avgBuyLine = null
var profitLine = null
var slLine = []

//create function which for each ACCOUNT1, ACCOUNT2 or ACCOUNT3 returns color for buy and color for sell - which can be strings representing color
//HELPERS FUNCTION - will go to utils
/**
 * Returns an object containing the colors for buy and sell for the specified account.
 *
 * Parameters:
 *     account (string): The account for which to retrieve the colors (ACCOUNT1, ACCOUNT2, or ACCOUNT3).
 *
 * Returns:
 *     object: An object with 'buy' and 'sell' properties containing the corresponding color strings.
 * 
 * Account 1:
#FF6B6B, #FF9999
Account 2:
#4ECDC4, #83E8E1
Account 3:
#FFD93D, #FFE787
Account 4:
#6C5CE7, #A29BFE
Another option for colors:

#1F77B4 (Entry) and #AEC7E8 (Exit)
#FF7F0E (Entry) and #FFBB78 (Exit)
#2CA02C (Entry) and #98DF8A (Exit)
#D62728 (Entry) and #FF9896 (Exit)
    */
function getAccountColors(account) {
    const accountColors = {
        ACCOUNT1: { accid: 'A1', buy: '#FF7F0E', sell: '#FFBB78' },
        ACCOUNT2: { accid: 'A2',buy: '#1F77B4', sell: '#AEC7E8' },
        ACCOUNT3: { accid: 'A3',buy: '#2CA02C', sell: '#98DF8A' },
        ACCOUNT4: { accid: 'A4',buy: '#D62728', sell: '#FF9896' },
        ACCOUNT5: { accid: 'A5',buy: 'purple', sell: 'orange' }
    };
    return accountColors[account] || { buy: '#37cade', sell: 'red' };
}  

//TRANSFORM object returned from REST API get_arch_run_detail
//to series and markers required by lightweigth chart
//input array object bars = { high: [1,2,3], time: [1,2,3], close: [2,2,2]...}
//output array [{ time: 111, open: 11, high: 33, low: 333, close: 333},..]
function transform_data(data) {
    //console.log(data)
    var SHOW_SL_DIGITS = get_from_config("SHOW_SL_DIGITS", true)
    transformed = []
    //get basic bars, volume and vvwap
    var bars = []
    var volume = []
    var vwap = []

    //pokud mame tak projedeme ext_data pro dane klice a s nimi pracujeme
    var sl_line = []
    var sl_line_markers = []
    var sl_line_sada = []
    var sl_line_markers_sada = []
    //console.log(JSON.stringify(data.ext_data.sl_history, null, 2))
    prev_id = 0
    //cas of first record, nekdy jsou stejny - musim pridat setinku
    prev_cas = 0
    if ((data.ext_data !== null) && (data.ext_data.sl_history)) {
        ///sort sl_history according to order id string - i need all same order id together
        data.ext_data.sl_history.sort(function (a, b) {
            return a.id.localeCompare(b.id);
          });

        data.ext_data.sl_history.forEach((histRecord, index, array) => {
            
            //console.log("plnime")

            //nova sada
            if (prev_id !== histRecord.id) {
                if (prev_id !== 0) {
                    //push sadu do pole
                    sl_line.push(sl_line_sada)
                    sl_line_markers.push(sl_line_markers_sada)
                }
                //init nova sada
                sl_line_sada = []
                sl_line_markers_sada = []
                sline_color = "#f5aa42"
            }

            prev_id = histRecord.id

            //prevedeme iso data na timestampy
            cas = histRecord.time

            if (cas == prev_cas) {
                cas = cas + 0.001
            }

            prev_cas = cas

            //line pro buy/sell markery
            sline = {}
            sline["time"] = cas
            sline["value"] = histRecord.sl_val
            if (histRecord.account) {
                const accColors = getAccountColors(histRecord.account)
                sline_color = histRecord.direction == "long" ? accColors.buy : accColors.sell //idealne
                sline["color"] = sline_color
            }

            sl_line_sada.push(sline)

            //ZDE JSEM SKONCIL
            //COLOR SE NASTAVUJE V SERIES OPTIONS POZDEJI - nejak vymyslet

            sline_markers = {}
            sline_markers["time"] = cas
            sline_markers["position"] = "inBar" 
            sline_markers["color"] = sline_color
            //sline_markers["shape"] = "circle"
            //console.log("SHOW_SL_DIGITS",SHOW_SL_DIGITS)
            sline_markers["text"] = SHOW_SL_DIGITS ? histRecord.sl_val.toFixed(3) : ""
            sl_line_markers_sada.push(sline_markers)

            if (index === array.length - 1) {
                    //pro posledni zaznam push sadu do pole
                    sl_line.push(sl_line_sada)
                    sl_line_markers.push(sl_line_markers_sada)
            }

            });
        }


    //pomocne
    var last_time = 0
    var time = 0

    data.bars.time.forEach((element, index, array) => {
        sbars = {};
        svolume = {};
        svwap = {};

        //tento algoritmus z duplicit dela posloupnosti a srovna i pripadne nekonzistence
        //napr z .911 .911 .912 udela .911 .912 .913
        //TODO - možná dat do backendu agregatoru
        if (last_time>=element) {
            console.log("bars", "problem v case - zarovnano",time, last_time, element)
            
            data.bars.time[index] = data.bars.time[index-1] + 0.000001
        }

        last_time = data.bars.time[index]
        sbars["time"] = data.bars.time[index];
        sbars["close"] = data.bars.close[index]
        sbars["open"] = data.bars.open[index]
        sbars["high"] = data.bars.high[index]
        sbars["low"] = data.bars.low[index]


        svwap["time"] = data.bars.time[index];
        svwap["value"] = data.bars.vwap[index]

        svolume["time"] = data.bars.time[index];
        svolume["value"] = data.bars.volume[index]

        bars.push(sbars)
        vwap.push(svwap)
        volume.push(svolume)
    }); 
    transformed["bars"] = bars
    //console.log(bars)
    transformed["vwap"] = vwap
    transformed["volume"] = volume
    var bars = []
    var volume = []
    var vwap = []


    if ((data.ext_data !== null) && (data.ext_data.dailyBars)) {
        data.ext_data.dailyBars.time.forEach((element, index, array) => {
            sbars = {};
            svolume = {};
            svwap = {};

            sbars["time"] = element;
            sbars["close"] = data.ext_data.dailyBars.close[index]
            sbars["open"] = data.ext_data.dailyBars.open[index]
            sbars["high"] = data.ext_data.dailyBars.high[index]
            sbars["low"] = data.ext_data.dailyBars.low[index]


            svwap["time"] = element
            svwap["value"] = data.ext_data.dailyBars.vwap[index]

            svolume["time"] = element
            svolume["value"] = data.ext_data.dailyBars.volume[index]

            bars.push(sbars)
            vwap.push(svwap)
            volume.push(svolume)
        }); 
        transformed["dailyBars"] = {}
        transformed["dailyBars"]["bars"] = bars
        transformed["dailyBars"]["vwap"] = vwap
        transformed["dailyBars"]["volume"] = volume
        var bars = []
        var volume = []
        var vwap = []
    }


    //get markers - avgp line for all buys
    var avgp_buy_line = []
    var avgp_markers = []
    var sum_profit_line = []
    var markers = []
    var markers_line = []
    var last_timestamp = 0.1
    var iterator = 0.002
    data.trades.forEach((trade, index, array) => {
        obj = {};
        a_markers = {}
        //tady z predchozi verze muze byt string (pak je to date v iso) a nebo v novejsi uz mame timestamp

        timestamp = (typeof trade.order.filled_at === 'string') ? Date.parse(trade.order.filled_at)/1000 : trade.order.filled_at
        //light chart neumi vice zaznamu ve stejny cas
        //protoze v BT se muze stat vice tradu v jeden cas, testujeme stejne hodnoty a pripadne pricteme jednu ms
        //tradu s jednim casem muze byt za sebou vic, proto iterator 
        if (last_timestamp > timestamp) {
            console.log("NEKONZISTENCE RAZENI",last_timestamp, timestamp)
            console.log("aktualni trade", JSON.stringify(trade,null,2))
            console.log("předchozí trade", JSON.stringify(data.trades[index-1],null,2))
        }
        if (last_timestamp == timestamp) {
            last_timestamp = timestamp
            console.log("DUPLICITA tradu aktual/predchozi/nasledujici", trade, data.trades[index-1], data.trades[index+1])
            console.log("původní timestamp je ",timestamp)
            timestamp = parseFloat(timestamp) + iterator
            console.log("nový timestamp je ",timestamp)
            iterator += 0.001
        }
        else {
            last_timestamp = timestamp
            iterator = 0.002
        }
        
        //AVG BUY LINE - zatim docasne vypiname
        if (((trade.order.side == "buy") || (trade.order.side == "sell")) && 1==2) {
                //avgp lajnu vytvarime jen pokud je v tradeventu prumerna cena
                if ((trade.pos_avg_price !== null) && (trade.pos_avg_price !== 0)) {
                //line pro avgp markers
                obj["time"] = timestamp;
                obj["value"] = trade.pos_avg_price;
                avgp_buy_line.push(obj)

                //avgp markers pro prumernou cenu aktualnich pozic
                a_markers["time"] = timestamp
                a_markers["position"] = "aboveBar"
                a_markers["color"] = "#e8c76d"
                a_markers["shape"] = "arrowDown"
                //if (CHART_SHOW_TEXT) 
                //a_markers["text"] = trade.position_qty + " " + parseFloat(trade.pos_avg_price).toFixed(3)
                //a_markers["text"] = CHART_SHOW_TEXT ? trade.position_qty + "/" + parseFloat(trade.pos_avg_price).toFixed(3) :trade.position_qty
                avgp_markers.push(a_markers)
            }
        }
        //PROFITLINE
        if ((trade.order.side == "buy") || (trade.order.side == "sell")) {
                //avgp lajnu vytvarime jen pokud je v tradeventu prumerna cena
            if ((trade.profit_sum !== null)) {
                //line pro avgp markers
                obj["time"] = timestamp;
                obj["value"] = trade.profit_sum.toFixed(1);
                sum_profit_line.push(obj)

                //avgp markers pro prumernou cenu aktualnich pozic
                // a_markers["time"] = timestamp
                // a_markers["position"] = "aboveBar"
                // a_markers["color"] = "#e8c76d"
                // a_markers["shape"] = "arrowDown"
                // a_markers["text"] = trade.profit_sum.toFixed(1);
                // //if (CHART_SHOW_TEXT) 
                // //a_markers["text"] = trade.position_qty + " " + parseFloat(trade.pos_avg_price).toFixed(3)
                // //a_markers["text"] = CHART_SHOW_TEXT ? trade.position_qty + "/" + parseFloat(trade.pos_avg_price).toFixed(3) :trade.position_qty
                // avgp_markers.push(a_markers)
            }
        }      

        const { accid: accountId,buy: buyColor, sell: sellColor } = getAccountColors(trade.account);

        //buy sell markery
        marker = {}
        marker["time"] = timestamp;
        // marker["position"] = (trade.order.side == "buy") ? "belowBar" : "aboveBar" 
        marker["position"] = (trade.order.side == "buy") ? "aboveBar" : "aboveBar" 
        marker["color"] = (trade.order.side == "buy") ? buyColor : sellColor
        //marker["shape"] = (trade.order.side == "buy") ? "arrowUp" : "arrowDown"
        marker["shape"] = (trade.order.side == "buy") ? "arrowUp" : "arrowDown"
        //marker["text"] =  trade.qty + "/" + trade.price
        qt_optimized = (trade.order.qty % 1000 === 0) ? (trade.order.qty / 1000).toFixed(1) + 'K' : trade.order.qty
  
        marker["text"] = accountId + " " //account shortcut
        if (CHART_SHOW_TEXT) {
            //včetně qty
            //marker["text"] =  qt_optimized + "@" + trade.price
                
            //bez qty
            marker["text"] +=  trade.price
            closed_trade_marker_and_profit = (trade.profit) ? "c" + trade.profit.toFixed(1) + "/" + trade.profit_sum.toFixed(1) : "c"
            marker["text"] += (trade.position_qty == 0) ? closed_trade_marker_and_profit : ""
        } else {
            closed_trade_marker_and_profit = (trade.profit) ? "c" + trade.profit.toFixed(1) + "/" + trade.profit_sum.toFixed(1) : "c"
            marker["text"] += (trade.position_qty == 0) ? closed_trade_marker_and_profit : trade.price.toFixed(3)
        }

        markers.push(marker)

        //prevedeme iso data na timestampy
        //open bud zde je iso string (predchozi verze) nebo rovnou float - podporime oboji
        trade.order.submitted_at = (typeof trade.order.submitted_at === 'string') ? Date.parse(trade.order.submitted_at)/1000 : trade.order.submitted_at
        trade.order.filled_at = (typeof trade.order.filled_at === 'string') ? Date.parse(trade.order.filled_at)/1000 : trade.order.filled_at
        trade.timestamp = (typeof trade.timestamp  === 'string') ? Date.parse(trade.order.timestamp)/1000 : trade.order.timestamp
        tradeDetails.set(timestamp, trade)

        //line pro buy/sell markery
        mline = {}
        mline["time"] = timestamp
        mline["value"] = trade.price
        markers_line.push(mline)

    // time: datesForMarkers[i].time,
    // position: 'aboveBar',
    // color: '#e91e63',
    // shape: 'arrowDown',
    // text: 'Sell @ ' + Math.floor(datesForMarkers[i].high + 2),     
        
    });

    //pro jistotu jeste seradime podle casu
    //v BT se muze predbehnout a lightweight to pak nezobrazi
    markers.sort(sorter)
    markers_line.sort(sorter)
    avgp_buy_line.sort(sorter)
    avgp_markers.sort(sorter)
    sum_profit_line.sort(sorter)

    transformed["avgp_buy_line"] = avgp_buy_line
    transformed["sum_profit_line"] = sum_profit_line 
    transformed["avgp_markers"] = avgp_markers
    transformed["markers"] = markers
    transformed["markers_line"] = markers_line
    transformed["sl_line"] = sl_line
    transformed["sl_line_markers"] = sl_line_markers
    //console.log("naplnene", sl_line, sl_line_markers)
    //console_log(JSON.stringify(transformed["sl_line"],null,2))
    //console_log(JSON.stringify(transformed["sl_line_markers"],null,2))
    //get additional indicators
    return transformed
}

//unit: Min, Hour, Day, Week, Month
//prepares data before displaying archived chart - fetch history bars if necessary
function prepare_data(archRunner, timeframe_amount, timeframe_unit, archivedRunnerDetail) {
   req = {}
   req["symbol"] = archRunner.symbol

    if (archRunner.mode == "backtest") {
        req["datetime_object_from"] = archRunner.bt_from
        req["datetime_object_to"] = archRunner.bt_to
    }
    else 
    {
        req["datetime_object_from"] = archRunner.started
        req["datetime_object_to"] = archRunner.stopped
    }
    console.log("datum pred",req.datetime_object_from)
    //pridame z obou stran 1 minutu - kvuli zobrazeni na frontendu,
    req["datetime_object_from"] = subtractMinutes(new Date(req.datetime_object_from),1).toISOString()
    req["datetime_object_to"] = addMinutes(new Date(req.datetime_object_to),1).toISOString()
    console.log("datum po", req.datetime_object_from)
    req["timeframe_amount"] = timeframe_amount
    req["timeframe_unit"] = timeframe_unit
    $.ajax({
        url:"/history_bars/",
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-API-Key',
                API_KEY); },
        method:"GET",
        contentType: "application/json",
        data: req,
        success:function(data){
            //console.log("one minute bars before", JSON.stringify(data))
            data.map((el)=>{
                cas = new Date(el.timestamp)
                el.time = cas.getTime()/1000;
                delete el.timestamp
                });
            //console.log("one min bars_after_transformation", JSON.stringify(data))
            oneMinuteBars = data
            chart_archived_run(archRunner, archivedRunnerDetail, oneMinuteBars);
            //call function to continue
            //return data
            //$("#statusStratvars").text(JSON.stringify(data.stratvars,null,2))
        },
        error: function(xhr, status, error) {
            oneMinuteBars = null
            chart_archived_run(archRunner, archivedRunnerDetail, oneMinuteBars);
            var err = eval("(" + xhr.responseText + ")");
            window.alert(JSON.stringify(xhr));
            console.log(JSON.stringify(xhr));
        }
    })  
}

//pomocna sluzba pro naplneni indListu a charting indikatoru
function chart_indicators(data, visible, offset) {
    console.log(data)
    //console.log("indikatory", JSON.stringify(data.indicators,null,2))
    //podobne v livewebsokcets.js - dat do jedne funkce
    if (data.hasOwnProperty("indicators")) { 
        // console.log("jsme uvnitr indikatoru")

        //vraci se pole indicatoru, kazdy se svoji casovou osou (time) - nyni standard indikatory a cbar indikatory
        var indicatorList = data.indicators

        //ze stratvars daneho runnera si dotahneme nastaveni indikatoru - pro zobrazeni v tooltipu

        //TOML parse
        //console.log("PUVODNI", data.archRecord.stratvars_toml)
        var stratvars_toml = TOML.parse(data.archRecord.stratvars_toml)
        

        //console.log("ZPETNE STRINGIFIED", TOML.stringify(TOML.parse(data.archRecord.stratvars_toml), {newline: '\n'}))
        //indicatory
        //console.log("indicatory TOML", stratvars_toml.stratvars.indicators)
        indId = 1
        var multiOutsCnf = {}
        indicatorList.forEach((indicators, index, array) => {

            //var indicators = data.indicators
            //index 0 - bar indikatory
            //index 1 - tick based indikatory
            //if there are indicators it means there must be at least two keys (time which is always present)
            if (Object.keys(indicators).length > 1) {
                for (const [key, value] of Object.entries(indicators)) {
                    if (key !== "time") {
                            //get cnf of indicator to display in the button tooltip
                            var cnf = null
                            //pokud je v nastaveni scale, pouzijeme tu
                            var scale = null
                            var instant = null
                            var returns = null
                            //console.log(key)
                            //zkusime zda nejde o instantni indikator z arch runneru
                            if ((data.ext_data !== null) && (data.ext_data.instantindicators)) {
                                let instantIndicator = data.ext_data.instantindicators.find(indicator => indicator.name == key);
                                //console.log("nalezen", key)
                                if (instantIndicator) {
                                    cnf = instantIndicator.toml
                                    scale = TOML.parse(cnf).scale
                                    instant = 1
                                    returns = TOML.parse(cnf).returns
                                }
                            }
                            //pokud nenalezeno, pak bereme standard
                            //pozor ted nebereme z addedInds
                            if (!cnf) {
                                if (stratvars_toml.stratvars.indicators[key]) {
                                    cnf = "#[stratvars.indicators."+key+"]"+TOML.stringify(stratvars_toml.stratvars.indicators[key], {newline: '\n'})
                                    scale = stratvars_toml.stratvars.indicators[key].scale
                                    returns = stratvars_toml.stratvars.indicators[key].returns
                                    }
                                }
                            //     //kontriolujeme v addedInds
                            //     if (addedInds[key]) {
                            //         cnf = addedInds[key]
                            //         scale = TOML.parse(cnf).scale
                            //         instant = 1
                            //       }
                            //       //a az potom bereme normos
                            //       else
                            //       {
                            //       cnf = "#[stratvars.indicators."+key+"]"+TOML.stringify(stratvars_toml.stratvars.indicators[key], {newline: '\n'})
                            //       scale = stratvars_toml.stratvars.indicators[key].scale
                            //       //cnf = TOML.stringify(stratvars_toml.stratvars.indicators[key], {newline: '\n'})
                            //       //a = TOML.parse(cnf)
                            //       //console.log("PARSED again",a)
                            //       }
                            // } 

                            //pro multioutput childs dotahneme scale z parenta
                            if (multiOutsCnf.hasOwnProperty(key)) {
                                scale = multiOutsCnf[key];
                            }

                            //initialize indicator and store reference to array
                            var obj = {name: key, type: index, series: null, cnf:cnf, instant: instant, returns: returns, indId:indId++}
    
                            //pokud jde o multioutput parenta ukladam scale parenta pro children
                            //varianty -  scale je jeden, ukladam jako scale pro vsechny parenty
                            //         -  scale je list - pouzijeme pro kazdy output scale v listu na stejnem indexu jako output
                            if (returns) {
                                returns.forEach((returned, index, array) => {
                                    //
                                    if (Array.isArray(scale)) {
                                        multiOutsCnf[returned] = scale[index]
                                    }
                                    else {
                                        multiOutsCnf[returned] = scale
                                    }
                                })
                            }                        //start
                            //console.log(key)
                            //get configuation of indicator to display
                            conf = get_ind_config(key, index)

                            //pokud neni v configuraci - zobrazujeme defaultne

                            //INIT INDICATOR BASED on CONFIGURATION

                            //DO BUDOUCNA zde udelat sorter a pripadny handling duplicit jako
                            //funkci do ktere muzu zavolat vse co pujde jako data do chartu

                            //MOVE TO UTILS ro reuse??
                            //if (conf && conf.display) {
                            if (conf && conf.embed) {

                                //tranform data do správného formátru
                                items = []
                                //var last = null
                                var last_time = 0
                                var time = 0

                                //tento algoritmus z duplicit dela posloupnosti a srovna i pripadne nekonzistence
                                //napr z .911 .911 .912 udela .911 .912 .913
                                value.forEach((element, index, array) => {
                                    item = {}
                                    //debug
                                    //TOTO odstranit po identifikovani chyby
                                    //if (indicators.time[index] !== undefined) {
                                        //{console.log("problem",key,last)}
                                    time = indicators.time[index]

                                    //pokud je nastaveny offset (zobrazujeme pouze bod vzdaleny N sekund od posledniho)
                                    //vynechavame prvni iteraci, aby se nam naplnil last_time
                                    if (offset && last_time !==0) {
                                        if (last_time + offset > time) {
                                            return;
                                        }
                                    }


                                    if (last_time>=time) {
                                        console.log(key, "problem v case - zarovnano",time, last_time, element)
                                        
                                        indicators.time[index] = indicators.time[index-1] + 0.000001
                                    }
                                    item["time"] = indicators.time[index]
                                    item["value"] = element

                                    last_time = indicators.time[index]

                                    if ((element == null) || (indicators.time[index] == null)) {
                                    console.log("probelem u indikatoru",key, "nekonzistence", element, indicators.time[index]) 
                                    }

                                    //console.log("objekt indicatoru",item)
                                    items.push(item)
                                        //debug
                                    //last = item
                                    // }
                                    // else
                                    // {
                                    //     console.log("chybejici cas", key)
                                    // }
                                });

                                //SERADIT PRO JISTOTU
                                //items.sort(sorter)

                                //FIND DUPLICITIES
                                // last_time = 0
                                // items.forEach((element, index, array) => {
                                //     if (last_time >= element.time) {
                                //         console.log("je duplicita/nekonzistence v ", element.time, element.value)
                                //     }
                                //     last_time = element.time
                                // })
                                

                                if (conf.embed)  {

                                    if (conf.histogram) {

                                        obj.series = chart.addHistogramSeries({
                                            title: (conf.titlevisible?key:""),
                                            color: colors.shift(),
                                            priceFormat: {type: 'volume'},
                                            priceScaleId: (scale)?scale:conf.priceScaleId,
                                            lastValueVisible: conf.lastValueVisible,
                                            visible: conf.display});
                                        
                                        obj.series.priceScale().applyOptions({
                                            // set the positioning of the volume series
                                            scaleMargins: {
                                                top: 0.7, // highest point of the series will be 70% away from the top
                                                bottom: 0,
                                            },
                                        });

                                    }
                                    else {
                                        var barva = colors.shift()
                                        obj.series = chart.addLineSeries({
                                            color: barva,
                                            priceScaleId: (scale)?scale:conf.priceScaleId,
                                            title: (conf.titlevisible?key:""),
                                            lineWidth: 1,
                                            visible: conf.display
                                        });   

                                        // //existuje statinds se stejnym klicem - bereme z nej minimum slope
                                        // a = data.statinds[key]
                                        // console.log("pro klic" + key + ":"+a, JSON.stringify(a,null,2))
                                        // console.log(data.statinds[key].minimum_slope)
                                        // console.log(JSON.stringify(data.statinds,null,2))
                                        //console.log((key in data.statinds), data.statinds, key)
                                        if (key in data.statinds) {
                                            //natvrdo nakreslime lajnu pro min angle
                                            //TODO predelat na configuracne
                                            const minSlopeLineOptopns = {
                                                price: data.statinds[key].minimum_slope,
                                                color: barva,
                                                lineWidth: 1,
                                                lineStyle: 2, // LineStyle.Dotted
                                                axisLabelVisible: true,
                                                title: "min",
                                            };
                                
                                            const minSlopeLine = obj.series.createPriceLine(minSlopeLineOptopns);

                                            const maxSlopeLineOptopns = {
                                                price: data.statinds[key].maximum_slope,
                                                color: barva,
                                                lineWidth: 1,
                                                lineStyle: 2, // LineStyle.Dotted
                                                axisLabelVisible: true,
                                                title: "max",
                                            };
                                
                                            const maxSlopeLine = obj.series.createPriceLine(maxSlopeLineOptopns);



                                        }
                                }


                                }
                                //INDICATOR on new pane
                                else { console.log("not implemented")}


                            //console.log("v chartovani",activatedButtons)
                            //pokud existuje v aktivnich pak zobrazujeme jako aktivni
                            if ((activatedButtons) && (activatedButtons.includes(obj.name))) {
                                //console.log("true",active?active:conf.display)
                                active = true
                            }
                            else {active = false}
                            
                            //pro main s multioutputem nezobrazujeme
                            if (returns) {
                                active = false
                            }
                            //add options
                            obj.series.applyOptions({
                                visible: active?active:visible,
                                lastValueVisible: false,
                                priceLineVisible: false,
                            });

                            //DEBUG
                            // if (key == 'tick_price') {
                            //     console.log("problem tu",JSON.stringify(items,null,2))
                            // }
                            //add data
                            obj.series.setData(items)

                            // add to indList array - pole zobrazovanych indikatoru    
                            indList.push(obj);   
                        }
                    }
                }
            }
        })
    }

    //sort by type first (0-bar,1-cbar inds) and then alphabetically
    // indList.sort((a, b) => {
    //     if (a.type !== b.type) {
    //         return a.type - b.type;
    //     } else {
    //         let nameA = a.name.toUpperCase();
    //         let nameB = b.name.toUpperCase();
    //         if (nameA < nameB) {
    //             return -1;
    //         } else if (nameA > nameB) {
    //             return 1;
    //         } else {
    //             // If uppercase names are equal, compare original names to prioritize uppercase
    //             return a.name < b.name ? -1 : 1;
    //         }
    //     }
    // });

    //SORTING tak, aby multioutputs atributy byly vzdy na konci dane skupiny (tzn. v zobrazeni jsou zpracovany svými rodiči)
    // Step 1: Create a Set of all names in 'returns' arrays
    const namesInReturns = new Set();
    indList.forEach(item => {
    if (Array.isArray(item.returns)) {
        item.returns.forEach(name => namesInReturns.add(name));
    }
    });

    // Step 2: Custom sort function
    indList.sort((a, b) => {
    // First, sort by 'type'
    if (a.type !== b.type) {
        return a.type - b.type;
    }

    // For items with the same 'type', apply secondary sorting
    const aInReturns = namesInReturns.has(a.name);
    const bInReturns = namesInReturns.has(b.name);

    if (aInReturns && !bInReturns) return 1;  // 'a' goes after 'b'
    if (!aInReturns && bInReturns) return -1; // 'a' goes before 'b'

    // If both or neither are in 'returns', sort alphabetically by 'name'
    return a.name.localeCompare(b.name);
    });



    //puvodni funkce
    // indList.sort((a, b) => {
    //     const nameA = a.name.toUpperCase(); // ignore upper and lowercase
    //     const nameB = b.name.toUpperCase(); // ignore upper and lowercase
    //     if (nameA < nameB) {
    //         return -1;
    //     }
    //     if (nameA > nameB) {
    //         return 1;
    //     }
    //     // names must be equal
    //     return 0;

    // });
    //vwap a volume zatim jen v detailnim zobrazeni
    if (!offset) {
        //display vwap and volume
        initialize_vwap()
        vwapSeries.setData(data.transformed_data["vwap"])

        initialize_volume()
        volumeSeries.setData(data.transformed_data["volume"])
        console.log("volume") 
    }       
}

//pomocna
function remove_indicators() {
    //reset COLORS
    colors = reset_colors.slice()

    //remove CUSTOMS indicators if exists
    indList.forEach((element, index, array) => {
        if (element.series) {
            //console.log(element.series, "tady series")
            chart.removeSeries(element.series);
        }
    }
    );
    indList = [];
    //remove BASIC indicators
    if (vwapSeries) {
        chart.removeSeries(vwapSeries)
        vwapSeries = null;
    }
    if (volumeSeries) {
        chart.removeSeries(volumeSeries)
        volumeSeries = null;
    }
}

//switch to interval pomocna funkce
function switch_to_interval(interval, data, extra) {
    store_activated_buttons_state(extra);

    if (!data) {
        window.alert("no data switch to interval")
    }

    //prip prpenuti prepisujeme candlestick a markery
    if (candlestickSeries) {
        last_range = chart.timeScale().getVisibleRange()
        chart.removeSeries(candlestickSeries);
        candlestickSeries = null
    }
    else {
        last_range = null
    }

    intitialize_candles()
    candlestickSeries.setData(data.AllCandleSeriesesData.get(interval));

    var containerlower = document.getElementById('lowercontainer');
    remove_indicators();
    btnElement = document.getElementById("indicatorsButtons")
    if (btnElement) {
        containerlower.removeChild(btnElement);
    }

    if (interval == data.native_resolution) {
        //indicators are in native resolution only
        chart_indicators(data, false);
        var indbuttonElement = populate_indicator_buttons(false);   
    }
    else {
        //na nepuvodnim grafu zobrazit jako offset a zobrazit jako neviditelne 
        chart_indicators(data,false,30)
        //buttonky jako vypnute
        var indbuttonElement = populate_indicator_buttons(false);
    }
    containerlower.append(indbuttonElement);



    display_buy_markers(data);
    //TADY JSEM SKONCIL - toto  nize predelat na hide button pro display bar markers
    // btnElement = document.getElementById("pricelineButtons")
    // var indbuttonElement = populate_indicator_buttons(false);
    // if (btnElement) {
    //     container1.removeChild(btnElement);
    // }
    //container1.append(indbuttonElement);   

    if (last_range) {
        chart.timeScale().setVisibleRange(last_range);
    }
}

//displays (redraws) buy markers
function display_buy_markers(data) {

    transformed_data = data.transformed_data
    // if (profitLine) {
    //     console.log(profitLine)
    //     chart.removeSeries(profitLine)
    //     console.log("nd")
    // }

    if (avgBuyLine) {
        chart.removeSeries(avgBuyLine)
    }

    if (markersLine) {
        chart.removeSeries(markersLine)
    }

    if (slLine) {
        slLine.forEach((series, index, array) => {
            chart.removeSeries(series)
        })
        slLine=[]

    }
    // if (slLine) {
    //     chart.removeSeries(slLine)
    // }      

    //console.log("avgp_buy_line",JSON.stringify(transformed_data["avgp_buy_line"],null,2))
    //console.log("avgp_markers",JSON.stringify(transformed_data["avgp_markers"],null,2))

    //if (transformed_data["sl_line"].length > 0) {
    //console.log(JSON.stringify(transformed_data["sl_line"]), null,2)
    //xx - ted bude slLine pole
    transformed_data["sl_line"].forEach((slRecord, index, array) => {

        //console.log("uvnitr")
        slLine_temp = chart.addLineSeries({
            //    title: "avgpbuyline",
                color: slRecord[0]["color"] ? slRecord[0]["color"] : '#e4c76d',
            //    color: 'transparent',
                lineWidth: 1,
                lastValueVisible: false
            });

            slLine_temp.applyOptions({
            lastValueVisible: false,
            priceLineVisible: false,
        });

        slLine_temp.setData(slRecord);
        slLine_temp.setMarkers(transformed_data["sl_line_markers"][index]);
        slLine.push(slLine_temp)

        //xx
    })

    //}

    if (transformed_data["sum_profit_line"].length > 0) {
        profitLine = chart.addLineSeries({
            //    title: "avgpbuyline", e8c76d
                color: '#99912b',
            //    color: 'transparent',
                lineWidth: 1,
                lastValueVisible: false
            });

            profitLine.applyOptions({
            lastValueVisible: false,
            priceLineVisible: false,
            priceScaleId: "own",
            visible: false
        });


        profitLine.setData(transformed_data["sum_profit_line"]);
        //profitLine.setMarkers(transformed_data["sum_profit_line_markers"]);
    }


    if (transformed_data["avgp_buy_line"].length > 0) {
        avgBuyLine = chart.addLineSeries({
            //    title: "avgpbuyline",
                color: '#e8c76d',
            //    color: 'transparent',
                lineWidth: 1,
                lastValueVisible: false
            });

        avgBuyLine.applyOptions({
            lastValueVisible: false,
            priceLineVisible: false,
        });


        avgBuyLine.setData(transformed_data["avgp_buy_line"]);
        avgBuyLine.setMarkers(transformed_data["avgp_markers"]);
    }

    markersLine = chart.addLineSeries({
        //  title: "avgpbuyline",
        //  color: '#d6d1c3',
            color: 'transparent',
            lineWidth: 1,
            lastValueVisible: false
        });

    //console.log("markers_line",JSON.stringify(transformed_data["markers_line"],null,2))
    //console.log("markers",JSON.stringify(transformed_data["markers"],null,2))

    markersLine.setData(transformed_data["markers_line"]);
    markersLine.setMarkers(transformed_data["markers"])

    const container1 = document.getElementById('chart');

    //chart.subscribeCrosshairMove(param => {
    chart.subscribeCrosshairMove(param => {
        //LEGEND SECTIOIN
        firstRow.style.color = 'white';
        update_chart_legend(param);

        //TOOLTIP SECTION
        //$('#trade-timestamp').val(param.time)
        if (
            param.point === undefined ||
            !param.time ||
            param.point.x < 0 ||
            param.point.x > container1.clientWidth ||
            param.point.y < 0 ||
            param.point.y > container1.clientHeight
        ) {
            toolTip.style.display = 'none';
        } else {
            //vyber serie s jakou chci pracovat - muzu i dynamicky
            //je to mapa https://tradingview.github.io/lightweight-charts/docs/api/interfaces/MouseEventParams

            //key = series (key.seriestype vraci Line/Candlestick atp.)  https://tradingview.github.io/lightweight-charts/docs/api/interfaces/SeriesOptionsMap

            toolTip.style.display = 'none';
            toolTip.innerHTML = "";
            var data = param.seriesData.get(markersLine);
            var data2 = param.seriesData.get(avgBuyLine);
            var profitdata = param.seriesData.get(profitLine);
            if ((data !== undefined) || (data2 !== undefined)) {
            //param.seriesData.forEach((value, key) => {
                //console.log("key",key)
                //console.log("value",value)
            
                //data = value
                //DOCASNE VYPNUTO
                toolTip.style.display = 'block';
                
                //console.log(JSON.safeStringify(key))
                // if (toolTip.innerHTML == "") {
                //     toolTip.innerHTML = `<div>${param.time}</div>`
                // }
                buy_price = 0
                //u sell markeru nemame avgBuyLine
                if (data2 !== undefined) {
                    buy_price = parseFloat(data2.value).toFixed(3)
                }

                toolTip.innerHTML += `<div>POS:${tradeDetails.get(param.time).position_qty}/${buy_price}</div><div>T:${tradeDetails.get(param.time).order.qty}/${data.value}</div>`;
                if (profitdata !== undefined) {
                    toolTip.innerHTML += `<div>P:${parseFloat(profitdata.value).toFixed(1)}</div>`
                }
                    //inspirace
                // toolTip.innerHTML = `<div style="color: ${'#2962FF'}">Apple Inc.</div><div style="font-size: 24px; margin: 4px 0px; color: ${'black'}">
                // ${Math.round(100 * price) / 100}
                // </div><div style="color: ${'black'}">
                // ${dateStr}
                // </div>`;


                // Position tooltip according to mouse cursor position
                toolTip.style.left = param.point.x+120 + 'px';
                toolTip.style.top = param.point.y + 'px';
            }
                //});
        }
    });
}

//render chart of archived runs
function chart_archived_run(archRecord, data, oneMinuteBars) {
    cleanup_chart()

    var transformed_data = transform_data(data)

    data["transformed_data"] = transformed_data
    data["archRecord"] = archRecord

    //initialize resolutions
    data["native_resolution"] = data.bars.resolution[0]+"s"
    //console.log("native", native_resolution)
 
    //available intervals zatim jen 1m
    var intervals = [data.native_resolution, '1m', '1d'];
    
    var dailyData = null
    if (transformed_data["dailyBars"]) {
        dailyData = transformed_data["dailyBars"]["bars"]
    }
    //zkusime daily data dat do minuty
    //console.log("daily", dailyData)

    nativeData  = transformed_data["bars"]
    //console.log("native")

    //get one minute data
    //tbd prepare volume
    //console.log("oneMinuteData",oneMinuteBars)

    data["AllCandleSeriesesData"] = new Map([
        [data.native_resolution, nativeData ],
        ["1m", dailyData?dailyData.concat(oneMinuteBars):oneMinuteBars],
        ["1d", dailyData ],
      ]);

    //dame si data do globalni, abychom je mohli pouzivat jinde (trochu prasarna, predelat pak)
    archData = data

   var switcherElement = createSimpleSwitcher(intervals, intervals[1], switch_to_interval, data);

    //define tooltip
    const container1 = document.getElementById('chart');
    const containerlower = document.getElementById('lowercontainer');

    const toolTipWidth = 90;
    const toolTipHeight = 90;
    const toolTipMargin = 15;
    
    // Create and style the tooltip html element
    toolTip = document.createElement('div');
    //width: 90px; , height: 80px; 
    toolTip.style = `position: absolute; display: none; padding: 8px; box-sizing: border-box; font-size: 12px; text-align: left; z-index: 1000; top: 12px; left: 12px; pointer-events: none; border: 1px solid; border-radius: 2px;font-family: -apple-system, BlinkMacSystemFont, 'Trebuchet MS', Roboto, Ubuntu, sans-serif; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;`;
    toolTip.style.backgroundColor = '#2d323e';
    toolTip.style.color = '#babfcd';
    toolTip.style.borderColor = "#a7a9b0";
    //'#2962FF';
    container1.appendChild(toolTip);
    //initialize chart
    document.getElementById("chart").style.display = "block"

    initialize_chart()

    containerlower.append(switcherElement)

    candlestickSeries = null

    //v pripade, ze neprojde get bars, nastavit na intervals[0]
    switch_to_interval(intervals[1], data)
    chart.timeScale().fitContent();

    chart.subscribeClick(param => {
        $('#trade-timestamp').val(param.time)
        //toggle_vertical_line(param.time);
        if (archRecord.ilog_save == true) {
            fetch_log_data(param.time, archRecord.id);
            }
        if (
            param.point === undefined ||
            !param.time ||
            param.point.x < 0 ||
            param.point.x > container1.clientWidth ||
            param.point.y < 0 ||
            param.point.y > container1.clientHeight
        ) {
            toolTip.style.display = 'none';
        } else {
            //vyber serie s jakou chci pracovat - muzu i dynamicky
            //je to mapa https://tradingview.github.io/lightweight-charts/docs/api/interfaces/MouseEventParams

            //key = series (key.seriestype vraci Line/Candlestick atp.)  https://tradingview.github.io/lightweight-charts/docs/api/interfaces/SeriesOptionsMap

            toolTip.style.display = 'none';
            toolTip.innerHTML = "";
            var data = param.seriesData.get(markersLine);
            if (data !== undefined) {
            //param.seriesData.forEach((value, key) => {
                //console.log("key",key)
                //console.log("value",value)
               
                //data = value
                //DOCASNE VYPNUTO
                toolTip.style.display = 'block';
                
                //console.log(JSON.safeStringify(key))
                if (toolTip.innerHTML == "") {
                    toolTip.innerHTML = `<div>${param.time}</div>`
                }
                var price = data.value
                // !== undefined ? data.value : data.close;


                toolTip.innerHTML += `<pre>${JSON.stringify(tradeDetails.get(param.time),null,2)}</pre><div>${price.toFixed(3)}</div>`;

                //console.log("toolTip.innerHTML",toolTip.innerHTML)

                //inspirace
                // toolTip.innerHTML = `<div style="color: ${'#2962FF'}">Apple Inc.</div><div style="font-size: 24px; margin: 4px 0px; color: ${'black'}">
                // ${Math.round(100 * price) / 100}
                // </div><div style="color: ${'black'}">
                // ${dateStr}
                // </div>`;


                // Position tooltip according to mouse cursor position
                toolTip.style.left = param.point.x+120 + 'px';
                toolTip.style.top = param.point.y-100 + 'px';
            }
                //});
        }
    });


    //add status
    $("#statusArchId").text(archRecord.id)
    $("#statusRegime").text("PAST RUN: "+archRecord.id)
    $("#statusName").text(archRecord.name)
    $("#statusMode").text(archRecord.mode)
    $("#statusAccount").text(archRecord.account)
    $("#statusIlog").text("Logged:" + archRecord.ilog_save)
    $("#statusStratvars").text(((archRecord.strat_json)?archRecord.strat_json:archRecord.stratvars),null,2)
    $("#statusSettings").text(JSON.stringify(archRecord.settings,null,2) + JSON.stringify(data.ext_data,null,2))
    
//mezitim se master zmenil //test /novy test

}


function fetch_log_data(timestamp, runner_id) {
    timestamp_from = timestamp - 20
    timestamp_to = timestamp + 20
    req = {}
    req["runner_id"] = runner_id;
    req["timestamp_from"] = timestamp_from;
    req["timestamp_to"] = timestamp_to;
    $.ajax({
        url:"/archived_runners_log/"+runner_id,
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-API-Key',
                API_KEY); },
        method:"GET",
        contentType: "application/json",
        data: req,
        success:function(data){
            //console.log("archived logs", JSON.stringify(data))
            display_log(data, timestamp)
        },
        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            //window.alert(JSON.stringify(xhr));
            console.log("Chyb pri dotazeni logu", JSON.stringify(xhr));
        }
    })  
}

function display_log(iterLogList, timestamp) {
        //console.log("Incoming logline object")


        var lines = document.getElementById('lines')
        var line = document.createElement('div')
        line.classList.add("line")
        const newLine = document.createTextNode("---------------")
        line.appendChild(newLine)
        lines.appendChild(line)

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

            highlighted = (parseInt(logLine.time) == parseInt(timestamp)) ? "highlighted" : ""
            logcnt++;
            hdr = logLine.time + " " + logLine.event + ' - '+ (logLine.message == undefined ? "" : logLine.message)
            hdr = Prism.highlight(hdr, Prism.languages.log, 'log');

            row = '<div data-bs-toggle="collapse" class="'+ highlighted + '" onclick="set_timestamp(' + logLine.time + ')" data-bs-target="#rec'+logcnt+'">'
            +hdr + '</div>'
            str_row = JSON.stringify(logLine.details, null, 2)
            //row_detail = '<div id="rec'+logcnt+'" data-toggle="collapse" data-target="#rec'+logcnt+'"class="collapse pidi"><pre>' + str_row + '</pre></div>'

            const html = Prism.highlight(str_row, Prism.languages.json, 'json');
            //console.log("tady", html)
            row_detail = '<div id="rec'+logcnt+'" class="collapse pidi"><pre><code class="language-log">' + html + '</code></pre></div>'

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
