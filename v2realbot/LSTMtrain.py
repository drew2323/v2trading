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
# TODO
# podpora pro BINARY TARGET
# podpora hyperpamaetru (activ.funkce sigmoid atp.)
# udelat vsechny config vars do cfg objektu
# vyuzit distribuovane prostredi - nebo aspon vlastni VM
# dopracovat identifikatory typu lastday close, todays open atp.
# random SEARCG a grid search
# udelat nejaka model metadata (napr, trenovano na (runners+obdobi), nastaveni treningovych dat, počet epoch, hyperparametry, config atribu atp.) - mozna persistovat v db
# udelat nejake verzovani
# predelat do GUI a modulu
# prepare data do importovane funkce, aby bylo mozno pouzit v predict casti ve strategii a nemuselo se porad udrzovat 
#s nastavenim modelu. To stejne i s nastavenim upravy features


#TODO NAPADY Na modely
#binary identifikace trendu napr. pokud nasledujici 3 bary rostou (0-1)
#soustredit se na modely s vystupem 0-1 nebo -1 až 1


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


# Zakladni nastaveni
testlist_id = ""
runner_ids = ["838e918e-9be0-4251-a968-c13c83f3f173","c11c5cae-05f8-4b0a-aa4d-525ddac81684"]
features = ["time","high","low","volume","open","close", "trades", "vwap","samebarslope", "fastslope","fsdelta", "fastslope2", "fsdelta2"]
#TODO toto je linearni prediction mod, dodelat podporu BINARY
#u binary bude target bud hotovy indikator a nebo jej vytvorit on the fly

#model muze byt take bez barů, tzn. jen indikatory
use_bars = True
target = 'fastslope2'
#predict how many bars in the future
target_steps = 5
name = "model1"
seq = 10
epochs = 200


#crossday identifier je time (hodnota resolution je pouzita ne odstraneni sekvenci skrz dny)
#predpoklad pouziti je crossday_sequence je time ve features
resolution = 1
crossday_sequence = False 
#zda se model uci i crosseday (skrz runner/day data). Pokud ne, pak se crossday sekvence odstrani
#realizovano pomoci pomocneho identifikatoru (runner)

#zajistime poradi
features.sort()
#cas na prvnim miste
if "time" in features:
   features.remove("time")
   features.insert(0, "time")

def merge_dicts(dict_list):
   # Initialize an empty merged dictionary
    merged_dict = {}

    # Iterate through the dictionaries in the list
    for i,d in enumerate(dict_list):
        for key, value in d.items():
            if key in merged_dict:
                merged_dict[key] += value
            else:
                merged_dict[key] = value
        #vlozime element s idenitfikaci runnera

    return merged_dict

    # # Initialize the merged dictionary with the first dictionary in the list
    # merged_dict = dict_list[0].copy()
    # merged_dict["index"] = []

    # # Iterate through the remaining dictionaries and concatenate their lists
    # for i, d in enumerate(dict_list[1:]):
    #     merged_dict["index"] = 
    #     for key, value in d.items():
    #         if key in merged_dict:
    #             merged_dict[key] += value
    #         else:
    #             merged_dict[key] = value

    # return merged_dict

def load_runner(runner_id):
    res, sada = get_archived_runner_details_byID(runner_id)
    if res == 0:
        print("ok")
    else:
        print("error",res,sada)

    bars = sada["bars"]
    indicators = sada["indicators"][0]
    return bars, indicators

def prepare_data(bars, indicators, features, target) -> tuple[np.array, np.array]:
    #create SOURCE DATA with features
    # bars and indicators dictionary and features as input
    indicator_data = np.column_stack([indicators[feature] for feature in features if feature in indicators])
    if len(bars)>0:
      bar_data = np.column_stack([bars[feature] for feature in features if feature in bars])
      combined_day_data = np.column_stack([bar_data,indicator_data])
    else:
      combined_day_data = indicator_data

    #create TARGET DATA
    try:
        target_base = bars[target]
    except KeyError:
        target_base = indicators[target]
    target_day_data = np.column_stack([target_base])
    return combined_day_data, target_day_data

def load_runners_as_list(runner_ids: list, use_bars: bool):
    """Loads all runners data (bars, indicators) for runner_ids into list of dicts-
    
    Args:
        runner_ids: list of runner_ids.
        use_bars: Whether to use also bars or just indicators

    Returns:
        tuple (barslist, indicatorslist) - lists with dictionaries for each runner
    """
    barslist = []
    indicatorslist = []
    for runner_id in runner_ids:
        bars, indicators = load_runner(runner_id)
        if use_bars:
          barslist.append(bars)
        indicatorslist.append(indicators)

    return barslist, indicatorslist

def create_sequences(combined_data, target_data, seq, target_steps, crossday_sequence = True):
  """Creates sequences of given length seq and target N steps in the future.

  Args:
    combined_data: A list of combined data.
    target_data: A list of target data.
    seq: The sequence length.
    target_steps: The number of steps in the future to target.
    crossday_sequence: Zda vytvaret sekvenci i skrz dny (runnery)

  Returns:
    A list of X sequences and a list of y sequences.
  """
  X_train = []
  y_train = []
  last_delta = None
  for i in range(len(combined_data) - seq - target_steps):
    if last_delta is None:
        last_delta = 2*(combined_data[i + seq + target_steps, 0] - combined_data[i, 0])
    
    curr_delta = combined_data[i + seq + target_steps, 0] - combined_data[i, 0]
    #pokud je cas konce sequence vyrazne vetsi (2x) nez predchozi
    #print(f"standardní zacatek {combined_data[i, 0]} konec {combined_data[i + seq + target_steps, 0]} delta: {curr_delta}")
    if  crossday_sequence is False and curr_delta > last_delta:
      print(f"sekvence vyrazena. Zacatek {combined_data[i, 0]} konec {combined_data[i + seq + target_steps, 0]}")
      continue  
    X_train.append(combined_data[i:i + seq])
    y_train.append(target_data[i + seq + target_steps])
    last_delta = 2*(combined_data[i + seq + target_steps, 0] - combined_data[i, 0])
  return np.array(X_train), np.array(y_train)

barslist, indicatorslist = load_runners_as_list(runner_ids, use_bars)

#zmergujeme vsechny data dohromady 
bars = merge_dicts(barslist)
indicators = merge_dicts(indicatorslist)
print(f"{len(indicators)}")
print(f"{len(bars)}")
source_data, target_data = prepare_data(bars, indicators, features, target)

# Set the printing threshold to print only the first and last 10 rows of the array
np.set_printoptions(threshold=10)
print("source_data", source_data, "shape", np.shape(source_data))

# Standardize the data
scalerX = StandardScaler()
scalerY = StandardScaler()
#FIT SCALER také fixuje počet FEATURES !!
source_data = scalerX.fit_transform(source_data)
target_data = scalerY.fit_transform(target_data)

#print("source_data shape",np.shape(source_data))

# Create a sequence of seq elements and define target prediction horizona
X_train, y_train = create_sequences(source_data, target_data, seq=seq, target_steps=target_steps, crossday_sequence=crossday_sequence)

#X_train (6205, 10, 14)
print("X_train", np.shape(X_train))

X_complete = np.array(X_train.copy())
Y_complete = np.array(y_train.copy())
X_train = np.array(X_train)
y_train = np.array(y_train)

# Split the data into training and test sets
X_train, X_test, y_train, y_test = train_test_split(X_train, y_train, test_size=0.20, shuffle=False) #random_state=42)

#print(np.shape(X_train))
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

#mazeme runner indikator pokud tu je
if "runner" in indicators:
   del indicators["runner"]
   print("runner key deleted from indicators")

if "runner" in features:
   features.remove("runner")
   print("runner removed from features")

lastNbars = slice_dict_lists(bars, seq)
lastNindicators =  slice_dict_lists(indicators, seq)
print("last5bars", lastNbars)
print("last5indicators",lastNindicators)

indicator_data = np.column_stack([lastNindicators[feature] for feature in features if feature in lastNindicators])
if use_bars:
  bar_data = np.column_stack([lastNbars[feature] for feature in features if feature in lastNbars])
  combined_live_data = np.column_stack([bar_data, indicator_data])
else:
   combined_live_data = indicator_data
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
mse = mean_squared_error(Y_complete, X_complete)
print('Test MSE:', mse)

# Plot the predicted vs. actual close prices
plt.plot(Y_complete, label='Actual')
plt.plot(X_complete, label='Predicted')
plt.legend()
plt.show()

# To make a prediction, we can simply feed the model a sequence of 5 elements and it will predict the next element. For example, to predict the close price for the 6th time period, we would feed the model the following sequence:

# sequence = combined_data[0:5]
# prediction = model.predict(sequence)
