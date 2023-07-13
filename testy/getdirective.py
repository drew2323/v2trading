#ROZPRACOVANE pri vytvareni OR/AND dynamickych buysignalu
# indicator.ema
#     length = 3
#     buy_if_below = 15
#     OR.buy_if_below = 15 #totozne s predchozim, staci kdyz jedna podminka plati
#     AND.buy_if_below = 15 #musi platiti vsechny podminky u vsech  indikatoru




#TOTO dodelat

#nejspis v INITU nahrat vsechny buysignal directivy do jednoho dictu
#a ten pouzivat v celem lifecyclu

#tato funkce by je mohla vytvorit
# vysledek: {'AND': [('ema', 'ema20')], 'OR': []}

#tato funkce vytvori dictionary typu podminek (OR/AND) a indikatoru s direktivami buy_if
# do OR jsou dane i bez prefixu
# {'AND': [('nazev indikatoru', 'nazev direktivy', 'hodnotadirektivy')], 'OR': []}
def get_indicators_with_buy_directive():
    starts_with = "buy_if"
    reslist = dict(AND=[], OR=[])

    for indname, indsettings in vars["indicators"].items():
        for option,value in indsettings.items():
                if option.startswith(starts_with):
                    reslist["OR"].append((indname, option, value))
                if option == "AND":
                    #vsechny buy direktivy, ktere jsou pod AND
                    for key, val in value.items():
                        if key.startswith(starts_with):
                            reslist["AND"].append((indname, key, val))
                if option == "OR" :
                    #vsechny buy direktivy, ktere jsou pod OR
                    for key, val in value.items():
                        if key.startswith(starts_with):
                            reslist["OR"].append((indname, key, val))
    return reslist     


vars = {'maxpozic': 2000, 'def_mode_from': 2000, 'chunk': 100, 'profit': 0.014, 'def_profit': 0.01, 'max_profit': 0.03, 'vykladka': 1, 'curve': [0.03, 0.01, 0.01, 0.0, 0.02, 0.02, 0.01, 0.01, 0.01, 0.03, 0.01, 0.01, 0.01, 0.04, 0.01, 0.01, 0.01, 0.05, 0.01, 0.01, 0.01, 0.01, 0.06, 0.01, 0.01, 0.01, 0.01], 'curve_def': [0.02, 0.03, 0.02, 0, 0, 0.02, 0, 0, 0, 0.02], 'ticks2reset': 0.06, 'consolidation_bar_count': 5, 'first_buy_market': True, 'first_buy_market_def_mode': False, 'market_buy_multiplier': 1, 'rsi_dont_buy_above': 70, 'bigwave_slope_above': 0.12, 'minimum_slope': -0.1, 'open_rush': 30, 'close_rush': 30, 'lastbuy_offset': 5, 'last_buy_offset_reset_after_sell': False, 'buy_only_on_confirmed': False, 'indicators': {'ema': {'type': 'EMA', 'source': 'close', 'length': 5, 'on_confirmed_only': False, 'AND': {'buy_if_crossed_down': 'ema20'}}, 'ema20': {'type': 'EMA', 'source': 'close', 'length': 20, 'on_confirmed_only': False}, 'RSI14': {'type': 'RSI', 'RSI_length': 14, 'source': 'vwap', 'MA_length': 5}, 'slope': {'type': 'slope', 'on_confirmed_only': False, 'MA_length': 5, 'slope_lookback': 10, 'lookback_offset': 3, 'minimum_slope': -0.1, 'maximum_slope': 0.2}, 'slopeLP': {'type': 'slopeLP', 'on_confirmed_only': False, 'leftpoint': 'baropen', 'slope_lookback': 8, 'lookback_offset': 4, 'minimum_slope': -0.09, 'maximum_slope': 0.2}, 'slope10': {'type': 'slope', 'on_confirmed_only': False, 'MA_length': 5, 'slope_lookback': 60, 'lookback_offset': 20, 'minimum_slope': -0.1, 'maximum_slope': 0.45}, 'slope20': {'type': 'slope', 'on_confirmed_only': False, 'MA_length': 5, 'slope_lookback': 120, 'lookback_offset': 25, 'minimum_slope': -0.1, 'dont_buy_above': 0.3, 'maximum_slope': 0.45}}, 'sell_protection': {'enabled': False, 'slopeMA_rising': 2, 'rsi_not_falling': 3}, 'sell_in_progress': False, 'mode': None, 'last_tick_price': 48.41, 'last_50_deltas': [0.027251, 2.050578, 0.205957, 2.226359, 0.00071, 4.034629, 0.0, 0.387769, 2.779256, 1.735168, 1.208257, 0.729469, 1.215035, 2.510941, 4.126465, 0.0, 0.89464, 0.863604, 0.363522, 0.808834, 3.007671, 1.450134, 5.292132, 2.532213, 0.0, 2.185073, 3.185483, 1.664617, 1.972669, 1.552979, 0.45697, 1.370411, 1.125679, 0.0, 0.390609, 0.770417, 0.050253, 1.652531, 0.729488, 0.788619, 0.873404, 1.013351, 0.045697, 2.992692, 4.046475, 0.165393, 0.0, 5.635894, 0.0, 3.558663], 'last_tick_volume': 200, 'next_new': 1, 'lastbuyindex': 103, 'last_update_time': 1689001643.057809, 'reverse_position_waiting_amount': 0, 'pendingbuys': {}, 'limitka': None, 'limitka_price': None, 'jevylozeno': 0, 'blockbuy': 0, 'ticks2reset_backup': 0.06}

a = get_indicators_with_buy_directive()
print(a)