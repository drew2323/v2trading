import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from keras.models import Sequential, load_model
from keras.layers import LSTM, Dense
import matplotlib.pyplot as plt
from v2realbot.controller.services import get_archived_runner_details_byID
from v2realbot.common.model import RunArchiveDetail
from v2realbot.config import DATA_DIR
from v2realbot.utils.utils import slice_dict_lists
from collections import defaultdict
from operator import itemgetter
from joblib import dump, load


#ZAKLAD PRO TRAINING SCRIPT na vytvareni model 
# TODO (v budoucnu predelat do GUI)
#jednotlive funkcni bloky dat do modulů
#pridat natrenovani z listu runnerů (případně dodělat do RUNu a ty runnery si spustit nejdřív)
#TODO
#binary target
#random search a grid search

#TODO
#udelat to same jen na trend, pres binary target, sigmoid a crossentropy
#napr. pokud nasledujici 3 bary rostou (0-1)

def create_sequences(combined_data, target_data, seq, target_steps):
  """Creates sequences of given length seq and target N steps in the future.

  Args:
    combined_data: A list of combined data.
    target_data: A list of target data.
    seq: The sequence length.
    target_steps: The number of steps in the future to target.

  Returns:
    A list of X sequences and a list of y sequences.
  """

  X_train = []
  y_train = []
  for i in range(len(combined_data) - seq - target_steps):
    X_train.append(combined_data[i:i + seq])
    y_train.append(target_data[i + seq + target_steps])

  return X_train, y_train

# Sample data (replace this with your actual OHLCV data)
bars = {
    'time': [1, 2, 3, 4, 5,6,7,8,9,10,11,12,13,14,15],
    'high': [10, 11, 12, 13, 14,10, 11, 12, 13, 14,10, 11, 12, 13, 14],
    'low': [8, 9, 7, 6, 8,8, 9, 7, 6, 8,8, 9, 7, 6, 8],
    'volume': [1000, 1200, 900, 1100, 1300,1000, 1200, 900, 1100, 1300,1000, 1200, 900, 1100, 1300],
    'close': [9, 10, 11, 12, 13,9, 10, 11, 12, 13,9, 10, 11, 12, 13],
    'open': [9, 10, 8, 8, 8,9, 10, 8, 8, 8,9, 10, 8, 8, 8],
    'resolution': [1, 1, 1, 1, 1,1, 1, 1, 1, 1,1, 1, 1, 1, 1]
}

indicators = {
    'time': [1, 2, 3, 4, 5,6,7,8,9,10,11,12,13,14,15],
    'fastslope': [90, 95, 100, 110, 115,90, 95, 100, 110, 115,90, 95, 100, 110, 115],
    'fsdelta': [90, 95, 100, 110, 115,90, 95, 100, 110, 115,90, 95, 100, 110, 115],
    'fastslope2': [90, 95, 100, 110, 115,90, 95, 100, 110, 115,90, 95, 100, 110, 115],
    'ema': [1000, 1200, 900, 1100, 1300,1000, 1200, 900, 1100, 1300,1000, 1200, 900, 1100, 1300]
}

#LOADING
runner_id = "838e918e-9be0-4251-a968-c13c83f3f173"
result = None
res, sada = get_archived_runner_details_byID(runner_id)
if res == 0:
    print("ok")
else:
    print("error",res,sada)

# bars = sada["bars"]
# indicators = sada["indicators"][0]

# Zakladni nastaveni
testlist_id = ""
ohlc_features = ['time','high', 'low', 'volume', 'open', 'close', 'trades', 'vwap']
indicator_features = ['samebarslope', 'fastslope','fsdelta', 'fastslope2', 'fsdelta2']

features = ["time","high","low","volume","open","close", "trades", "vwap","samebarslope", "fastslope","fsdelta", "fastslope2", "fsdelta2"]
#TODO toto je linearni prediction mod, dodelat podporu BINARY
#u binary bude target bud hotovy indikator a nebo jej vytvorit on the fly
target = 'close'
#predict how many bars in the future
target_steps = 5
name = "model1"
seq = 2
epochs = 500

features.sort()
# Prepare the data for bars and indicators
bar_data = np.column_stack([bars[feature] for feature in features if feature in bars])
indicator_data = np.column_stack([indicators[feature] for feature in features if feature in indicators])
combined_data = np.column_stack([bar_data, indicator_data])
###print(combined_data)
target_data = np.column_stack([bars[target]])
#print(target_data)
#for LSTM scaling before sequencing
# Standardize the data
scalerX = StandardScaler()
scalerY = StandardScaler()
combined_data = scalerX.fit_transform(combined_data)
target_data = scalerY.fit_transform(target_data)

# Create a sequence of seq elements and define target prediction horizona
X_train, y_train = create_sequences(combined_data, target_data, seq=seq, target_steps=target_steps)

#print("X_train", X_train)
#print("y_train", y_train)
X_complete = np.array(X_train.copy())
Y_complete = np.array(y_train.copy())
X_train = np.array(X_train)
y_train = np.array(y_train)

# Split the data into training and test sets
X_train, X_test, y_train, y_test = train_test_split(X_train, y_train, test_size=0.20, shuffle=False) #random_state=42)

# Define the input shape of the LSTM layer dynamically based on the reshaped X_train value
input_shape = (X_train.shape[1], X_train.shape[2])

# Build the LSTM model
model = Sequential()
model.add(LSTM(128, input_shape=input_shape))
model.add(Dense(1))

# Compile the model
model.compile(loss='mse', optimizer='adam')

# Train the model
model.fit(X_train, y_train, epochs=epochs)

#save the model
#model.save(DATA_DIR+'/my_model.keras')
#model = load_model(DATA_DIR+'/my_model.keras')
dump(scalerX, DATA_DIR+'/'+name+'scalerX.pkl')
dump(scalerY, DATA_DIR+'/'+name+'scalerY.pkl')
dump(model, DATA_DIR+'/'+name+'.pkl')

model = load(DATA_DIR+'/'+ name +'.pkl')
scalerX: StandardScaler = load(DATA_DIR+'/'+ name +'scalerX.pkl')
scalerY: StandardScaler = load(DATA_DIR+'/'+ name +'scalerY.pkl')

#LIVE PREDICTION - IMAGINE THIS HAPPENS LIVE
# Get the live data
# Prepare the data for bars and indicators

#asume ohlc_features and indicator_features remain the same


#get last 5 items of respective indicators
lastNbars = slice_dict_lists(bars, seq)
lastNindicators =  slice_dict_lists(indicators, seq)
print("last5bars", lastNbars)
print("last5indicators",lastNindicators)

bar_data = np.column_stack([lastNbars[feature] for feature in features if feature in lastNbars])
indicator_data = np.column_stack([lastNindicators[feature] for feature in features if feature in lastNindicators])
combined_live_data = np.column_stack([bar_data, indicator_data])
print("combined_live_data",combined_live_data)
combined_live_data = scalerX.transform(combined_live_data)
#scaler = StandardScaler()

combined_live_data = np.array(combined_live_data)

#converts to 3D array 
# 1 number of samples in the array.
# 2 represents the sequence length.
# 3 represents the number of features in the data.
combined_live_data = combined_live_data.reshape((1, seq, combined_live_data.shape[1]))


# Make a prediction
prediction = model(combined_live_data, training=False)
#prediction = prediction.reshape((1, 1))
# Convert the prediction back to the original scale
prediction = scalerY.inverse_transform(prediction)

print("prediction for last value", float(prediction))

#TEST PREDICATIONS
# Evaluate the model on the test set
#pozor testovaci sadu na produkc scalovat samostatne
#X_test = scalerX.transform(X_test)
#predikce nad testovacimi daty
X_complete = model.predict(X_complete)
X_complete = scalerY.inverse_transform(X_complete)

#target testovacim dat
Y_complete =  scalerY.inverse_transform(Y_complete)
#mse = mean_squared_error(y_test, y_pred)
#print('Test MSE:', mse)

# Plot the predicted vs. actual close prices
plt.plot(Y_complete, label='Actual')
plt.plot(X_complete, label='Predicted')
plt.legend()
plt.show()

# To make a prediction, we can simply feed the model a sequence of 5 elements and it will predict the next element. For example, to predict the close price for the 6th time period, we would feed the model the following sequence:

# sequence = combined_data[0:5]
# prediction = model.predict(sequence)
