import numpy as np
import matplotlib.pyplot as plt
from v2realbot.controller.services import get_archived_runner_details_byID
from v2realbot.common.model import RunArchiveDetail
from scipy.signal import argrelextrema

id = "c5ae757f-6bdd-4d1f-84a8-98bdaad65a28"

res, val = get_archived_runner_details_byID(id)
if res < 0:
    print(res)

detail = RunArchiveDetail(**val)
# detail.indicators[0]
price_series = np.array(detail.bars["vwap"])
#price_series = detail.bars["vwap"]
timestamps = detail.bars["time"]

prices = []
#TODO pridat k indikatorum convert to numpy, abych mohl pouzivat numpy operace v expressionu


def get_local_maxima_numpy(
    series: np.ndarray,
    debug=False,
) -> np.ndarray:
    """calculate local maximal point"""
    if series.size == 0:
        return np.array([])

    # Calculate the difference between adjacent elements.
    diff = np.diff(series)

    # Find the indices of the elements where the difference changes sign from positive to negative.
    high_index = np.where((diff[:-1] >= 0) & (diff[1:] < 0))[0] + 1

    # Return a NumPy array containing the local maxima.
    return high_index#series[high_index]

def get_local_minima_numpy(
    series: np.ndarray,
    debug=False,
) -> np.ndarray:
    """calculate local maximal point"""
    if series.size == 0:
        return np.array([])

    # Calculate the difference between adjacent elements.
    diff = np.diff(series)

    # Find the indices of the elements where the difference changes sign from positive to negative.
    low_index = np.where((diff[:-1] <= 0) & (diff[1:] > 0))[0] + 1

    # Return a NumPy array containing the local maxima.
    return low_index#series[high_index]

def get_local_minima(prices):
    return prices[-2] if len(prices) >= 3 and prices[-2] > prices[-3] and prices[-2] > prices[-1] else None

# iter_prices = []
# for price in detail.bars["vwap"]:
#     iter_prices.append(price)
#     get_local_minima(iter_prices)
    
def calculate_support_resistance(bars, window=5):
    lows = np.array(bars['low'])
    highs = np.array(bars['high'])

    rolling_support = np.minimum.accumulate(lows)[::-1][:window][::-1]
    rolling_resistance = np.maximum.accumulate(highs)[::-1][:window][::-1]

    return {'rolling_support': rolling_support.tolist(), 'rolling_resistance': rolling_resistance.tolist()}

rolling = calculate_support_resistance(detail.bars, 5)
print(rolling)


# func = "prices[-1] if np.all(prices[-1] > prices[-2:]) else 0"
# #func = "prices[-2] if len(prices) >= 3 and prices[-2] > prices[-3] and prices[-2] > prices[-1] else None"
# for price in price_series:
#     prices.append(price)
#     print(eval(func))
# maxima_indices = argrelextrema(price_series, np.greater)[0]
# minima_indices = argrelextrema(price_series, np.less)[0]
# # Print the indices of local maxima and minima
# print("Local Maxima Indices:", maxima_indices)
# print("Local Minima Indices:", minima_indices)

print("from new function")
maxima_indices = get_local_maxima_numpy(price_series)
minima_indices = get_local_minima_numpy(price_series)
print("Local Maxima Indices:", maxima_indices)
print("Local Minima Indices:", minima_indices)

# Plot the price series with local maxima and minima
plt.figure(figsize=(10, 6))
plt.plot(range(len(price_series)), price_series, label='Price Series')
plt.scatter(maxima_indices, price_series[maxima_indices], color='r', label='Local Maxima', zorder=5)
plt.scatter(minima_indices, price_series[minima_indices], color='g', label='Local Minima', zorder=5)
plt.xlabel('Time')
plt.ylabel('Price')
plt.title('Price Series with Local Maxima and Minima')
plt.legend()
plt.show()


