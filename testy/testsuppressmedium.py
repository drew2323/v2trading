import numpy as np
import matplotlib.pyplot as plt
from v2realbot.controller.services import get_archived_runner_details_byID
from v2realbot.common.model import RunArchiveDetail
from scipy.signal import argrelextrema
import mplfinance

id = "e74b5d35-6552-4dfc-ba59-2eda215af292"

res, val = get_archived_runner_details_byID(id)
if res < 0:
    print(res)

detail = RunArchiveDetail(**val)
# detail.indicators[0]
price_series = np.array(detail.bars["vwap"])
df = {}
highs = np.array(detail.bars["high"])
lows = np.array(detail.bars["low"])

np_high = np.array(detail.bars["high"])
np_low = np.array(detail.bars["low"])
price_series = detail.bars["vwap"]
timestamps = detail.bars["time"]

prices = []
#TODO pridat k indikatorum convert to numpy, abych mohl pouzivat numpy operace v expressionu

# func = "prices[-1] if np.all(prices[-1] > prices[-2:]) else 0"
# #func = "prices[-2] if len(prices) >= 3 and prices[-2] > prices[-3] and prices[-2] > prices[-1] else None"
# for price in price_series:
#     prices.append(price)
#     print(eval(func))

class Sup_Res_Finder():
    def __init__(self, s=None):
        if s is None:
            self.s = np.mean(np.diff(np.concatenate([[np.nan], np.highs, [np.nan]], axis=0)))
        else:
            self.s = s

    def isSupport(self, lows, i):
        support = lows[i] < lows[i-1] and lows[i] < lows[i+1] \
            and lows[i+1] < lows[i+2] and lows[i-1] < lows[i-2]

        return support

    def isResistance(self, highs, i):
        resistance = highs[i] > highs[i-1] and highs[i] > highs[i+1] \
            and highs[i+1] > highs[i+2] and highs[i-1] > highs[i-2]

        return resistance

    def find_levels(self, highs, lows):
        levels = []

        for i in range(2, len(lows) - 2):
            if self.isSupport(lows, i):
                l = lows[i]

                if not np.any([abs(l - x) < self.s for x in levels]):
                    levels.append((i, l))

            elif self.isResistance(highs, i):
                l = highs[i]

                if not np.any([abs(l - x) < self.s for x in levels]):
                    levels.append((i, l))

        return levels

def plot_ohlc_with_support_resistance(bars, s=None):
    highs = np.array(bars['high'])
    lows = np.array(bars['low'])

    finder = Sup_Res_Finder(s=s)
    levels = finder.find_levels(highs, lows)

    fig, ax = plt.subplots()

    # Plot the candlesticks

    ax.plot(bars['time'], highs, color='green', linestyle='-', linewidth=0.8)
    ax.plot(bars['time'], lows, color='red', linestyle='-', linewidth=0.8)
    ax.fill_between(bars['time'], highs, lows, color='green' if highs[0] > lows[0] else 'red', alpha=0.5)

    # Plot the support and resistance levels

    for level in levels:
        ax.hlines(level[1], level[0] - 0.5, level[0] + 0.5, color='black', linewidth=1)

    ax.set_xlabel('Time')
    ax.set_ylabel('Price')
    ax.set_title('OHLC Chart with Support and Resistance Levels')

    plt.show()


plot_ohlc_with_support_resistance(detail.bars, 0.05)

# print(price_series)
# # Find local maxima and minima using the optimized function.
# maxima_indices = argrelextrema(price_series, np.greater)[0]
# minima_indices = argrelextrema(price_series, np.less)[0]
# print(maxima_indices)
# print(minima_indices)
# # # Find local maxima and minima
# # maxima_indices = argrelextrema(price_series, np.greater)[0]
# # minima_indices = argrelextrema(price_series, np.less)[0]

# Plot the price series with local maxima and minima
# plt.figure(figsize=(10, 6))
# plt.plot(range(len(price_series)), price_series, label='Price Series')
# plt.scatter(maxima_indices, price_series[maxima_indices], color='r', label='Local Maxima', zorder=5)
# plt.scatter(minima_indices, price_series[minima_indices], color='g', label='Local Minima', zorder=5)
# plt.xlabel('Time')
# plt.ylabel('Price')
# plt.title('Price Series with Local Maxima and Minima')
# plt.legend()
# plt.show()

# # Print the indices of local maxima and minima
# print("Local Maxima Indices:", maxima_indices)
# print("Local Minima Indices:", minima_indices)
