import numpy as np
from sklearn.preprocessing import StandardScaler
from keras.models import Sequential
from keras.layers import LSTM, Dense
from v2realbot.controller.services import get_archived_runner_details_byID
from v2realbot.common.model import RunArchiveDetail
import orjson

runner_id = "838e918e-9be0-4251-a968-c13c83f3f173"
result = None
res, set = get_archived_runner_details_byID(runner_id)
if res == 0:
    print("ok")
else:
    print("error",res,set)

bars = set["bars"]
indicators = set["indicators"]
#print("bars",bars)
#print("indicators",indicators)

def scale_and_transform_data(bars, indicators):
  """Scales and transforms the `bars` and `indicators` dictionaries to use in an RNN time series prediction model.

  Args:
    bars: A dictionary containing OHLCV values and a timestamp.
    indicators: A dictionary containing additional indicators and a timestamp.

  Returns:
    A tuple containing the scaled and transformed training data, validation data, and test data.
  """

  # Combine the two dictionaries
  #combined_data = {**bars, **indicators}
  bar_data = np.column_stack((bars["time"], bars['high'], bars['low'], bars['volume'], bars['close'], bars['open']))

  # Scale the data
  scaler = StandardScaler()
  scaled_data = scaler.fit_transform(bar_data)

  # Create sequences of data
  sequences = []
  for i in range(len(scaled_data) - 100):
    sequence = scaled_data[i:i + 100]
    sequences.append(sequence)

  # Split the data into training, validation, and test sets
  train_sequences = sequences[:int(len(sequences) * 0.8)]
  val_sequences = sequences[int(len(sequences) * 0.8):int(len(sequences) * 0.9)]
  test_sequences = sequences[int(len(sequences) * 0.9):]

  return train_sequences, val_sequences, test_sequences

#Scale and transform the data
train_sequences, val_sequences, test_sequences = scale_and_transform_data(bars, indicators)
# Convert the training sequences to a NumPy array

# Convert the training sequences array to a NumPy array
train_sequences_array = np.asarray(train_sequences)

# Reshape the training sequences to the correct format
train_sequences_array = np.reshape(train_sequences_array, (train_sequences_array.shape[0], train_sequences_array.shape[1], 1))

# Define the RNN model
model = Sequential()
model.add(LSTM(128, input_shape=(train_sequences_array.shape[1], train_sequences_array.shape[2])))
model.add(Dense(1))

# Compile the model
model.compile(loss='mse', optimizer='adam')

# Train the model on the sequence data
model.fit(train_sequences, train_sequences, epochs=100)

# Make a prediction for the next data point
prediction = model.predict(test_sequences[-1:])

# Print the prediction
print(prediction)
