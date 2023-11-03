import numpy as np
import matplotlib.pyplot as plt
from v2realbot.controller.services import get_archived_runner_details_byID
from v2realbot.common.model import RunArchiveDetail
# Generate sample price data
timestamps = np.arange('2023-10-27', '2023-10-28', dtype='datetime64[s]')
price = 100 + np.arange(100) * 0.5

id = "e74b5d35-6552-4dfc-ba59-2eda215af292"

res, val = get_archived_runner_details_byID(id)
if res < 0:
    print(res)

detail = RunArchiveDetail(**val)
# detail.indicators[0]
price = detail.bars["vwap"]
timestamps = detail.bars["time"]

# Calculate the standard deviation of price changes over a specified time interval
def calculate_volatility(price, window):
    volatility = np.zeros_like(price)
    for i in range(window, len(price)):
        volatility[i] = np.std(price[i - window: i])
    return volatility

# Set a threshold for the indicator
threshold = 0.4

# Identify breakout points based on the threshold
def identify_breakouts(volatility, threshold):
    return volatility > threshold

# Plot the price data and the volatility breakout points
def plot_data(timestamps, price, breakout_points):
    plt.figure(figsize=(12, 6))
    plt.plot(timestamps, price, label='Price')
    breakout_timestamps = timestamps[np.where(breakout_points)[0]]
    breakout_prices = price[np.where(breakout_points)[0]]
    plt.scatter(breakout_timestamps, breakout_prices, color='r', label='Volatility Breakout')
    plt.xlabel('Time')
    plt.ylabel('Price')
    plt.title('Intraday Volatility Breakout Indicator')
    plt.legend()
    plt.show()

# Applying the functions
window = 30
volatility = calculate_volatility(price, window)
breakout_points = identify_breakouts(volatility, threshold)
plot_data(timestamps, price, breakout_points)