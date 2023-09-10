def is_rising_trend(price_list):
    """
    This function determines whether prices are consistently creating higher highs and higher lows.

    Args:
        price_list: A list of prices.

    Returns:
        True if the prices are in a rising trend, False otherwise.
    """

    if len(price_list) < 2:
        return False
    #
    global last_last_low
    global last_high
    global last_low
    global last_last_high
    global last_last_low
    last_high = price_list[0]
    last_low = None
    last_last_high = price_list[0]
    last_last_low = price_list[0]
    print(price_list)

    for i in range(1, len(price_list)):
        print("processing",price_list[i])

        #pokud je dalsi rostouci
        if price_list[i] > price_list[i-1]:
            #je vetsi nez LH - stává se LH
            if price_list[i] > last_high:
                #last_last_high = last_high
                last_high = price_list[i]
                #print("nova last last high",last_last_high)
                print("nove last high",last_high)

        #pokud je klesajici
        elif price_list[i] < price_list[i-1]:
        
            #pokud je cena nad last last jsme ok
            if price_list[i] > last_last_low:
                if last_low is None or price_list[i] < last_low:
                    if last_low is not None:
                        #vytvorime nove last last low
                        last_last_low = last_low
                        print("nova last last low",last_last_low)
                        #rovnou porovname cenu zda neklesla
                        if price_list[i] < last_last_low:
                            print("kleslo pod last last low")
                            return False
                    #mame nove last low
                    last_low = price_list[i]
                    print("nove last low",last_low)
            else:
                print("kleslo pod last last low, neroste")
                return False

    print("funkce skoncila, stale roste")
    return True

# Example usage:
#price_list = [1,2,3,2,2.5,3,1.8,4,5,4,4.5,4.3,4.8,4.5,6]


price_list = [
        # -0.0106,
        # -0.001,
        # 0.0133,
        # 0.0116,
        # 0.0075,
        -0.015,
        -0.0142,
        -0.0071,
        -0.0077,
        -0.0083,
        0.0016,
        0.0266,
        0.0355,
        0.0455,
        0.0563,
        0.1064,
        0.1283,
        0.1271,
        0.1277,
        0.1355,
        0.152,
        0.1376,
        0.1164,
        0.1115,
        0.102,
        0.0808,
        0.0699,
        0.0625,
        0.0593,
        0.0485,
        0.0323,
        0.0382,
        0.0403,
        0.0441,
        0.0526,
        0.0728,
        0.0841,
        0.1029,
        0.1055,
        0.0964,
        0.0841,
        0.0677,
        0.0782,
        0.0877,
        0.1099,
        0.1215,
        0.1379,
        0.1234,
        0.1,
        0.0949,
        0.1133,
        0.1428,
        0.1525,
        0.166,
        0.1788,
        0.1901,
        0.1967,
        0.2099,
        0.2407,
        0.2719,
        0.2897,
        0.3101,
        0.331,
        0.328,
        0.3241,
        0.3258,
        0.3275,
        0.3188,
        0.3071,
        0.2942,
        0.2939,
        0.277,
        0.2498,
        0.2464,
        0.2413,
        0.2377,
        0.2112,
        0.2076,
        0.2018,
        0.1975,
        0.1814,
        0.1776,
        0.1761,
        0.1868,
        0.1961,
        0.2016,
        0.2313,
        0.2485,
        0.2668,
        0.2973,
        0.3278,
        0.3581,
        0.3893,
        0.3997,
        0.4176,
        0.4285,
        0.4369,
        0.4457,
        0.4524,
        0.4482,
        0.4439,
        0.4302,
        0.4205,
        0.4278,
        0.4345,
        0.4403,
        0.4504,
        0.4523,
        0.461,
        0.4649,
        0.4618,
        0.4675,
        0.4724]


result = is_rising_trend(price_list)
print(result)  # This will print [(4, 60), (7, 62)] for the provided example

