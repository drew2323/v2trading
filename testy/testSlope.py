
sma = list

sma = [28.90, 28.91, 28.91, 28.92, 28.97, 28.99]
slope_lookback = 4
roc_lookback = 4

slope = (sma[-1] - sma[-slope_lookback])/slope_lookback
roc = ((sma[-1] - sma[-roc_lookback])/sma[-roc_lookback])*100

print(slope)


# -1 až 0 klesání
# 0 až 1 stoupání