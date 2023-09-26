import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from keras.models import Sequential
from keras.layers import LSTM, Dense
import matplotlib.pyplot as plt
from v2realbot.controller.services import get_archived_runner_details_byID
from v2realbot.common.model import RunArchiveDetail

# Sample data (replace this with your actual OHLCV data)
bars = {
    'time': [1, 2, 3, 4, 5],
    'high': [10, 11, 12, 13, 14],
    'low': [8, 9, 7, 6, 8],
    'volume': [1000, 1200, 900, 1100, 1300],
    'close': [9, 10, 11, 12, 13],
    'open': [9, 10, 8, 8, 8],
    'resolution': [1, 1, 1, 1, 1]
}

indicators = {
    'time': [1, 2, 3, 4, 5],
    'fastslope': [90, 95, 100, 110, 115],
    'ema': [1000, 1200, 900, 1100, 1300]
}

# Features and target
ohlc_features = ['high', 'low', 'volume', 'open', 'close']
indicator_features = ['fastslope']
target = 'close'

# Prepare the data for bars and indicators
bar_data = np.column_stack([bars[feature] for feature in ohlc_features])
indicator_data = np.column_stack([indicators[feature] for feature in indicator_features])
combined_data = np.column_stack([bar_data, indicator_data])
target_data = np.column_stack([bars[target]])


print(f"{combined_data=}")
print(f"{target_data=}")
# Split the data into training and test sets
X_train, X_test, y_train, y_test = train_test_split(combined_data, target_data, test_size=0.25, random_state=42)

# Standardize the data
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
y_train = scaler.fit_transform(y_train)

# Reshape the input data for LSTM to have an additional dimension for the number of time steps
X_train = X_train.reshape((X_train.shape[0], 1, X_train.shape[1]))

# Define the input shape of the LSTM layer dynamically based on the reshaped X_train value
input_shape = (X_train.shape[1], X_train.shape[2])

# Build the LSTM model
model = Sequential()
model.add(LSTM(128, input_shape=input_shape))
model.add(Dense(1))

# Compile the model
model.compile(loss='mse', optimizer='adam')

# Train the model
model.fit(X_train, y_train, epochs=500)

# Evaluate the model on the test set


# Reshape the test data for same structure as it was trained on
X_test = X_test.reshape((X_test.shape[0], 1, X_test.shape[1]))
y_pred = model.predict(X_test)
y_pred = scaler.inverse_transform(y_pred)
mse = mean_squared_error(y_test, y_pred)
print('Test MSE:', mse)

# Plot the predicted vs. actual close prices
plt.plot(y_test, label='Actual')
plt.plot(y_pred, label='Predicted')
plt.legend()
plt.show()