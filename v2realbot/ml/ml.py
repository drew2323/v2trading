# from sklearn.preprocessing import StandardScaler
# # from keras.models import Sequential
# from v2realbot.enums.enums import PredOutput, Source, TargetTRFM
# from v2realbot.config import DATA_DIR
# from joblib import dump
# # import v2realbot.ml.mlutils as mu
# from v2realbot.utils.utils import slice_dict_lists
# import numpy as np
# from copy import deepcopy
# import v2realbot.controller.services as cs
# #Basic classes for machine learning
# #drzi model a jeho zakladni nastaveni

# #Sample Data
# sample_bars = {
#     'time': [1, 2, 3, 4, 5,6,7,8,9,10,11,12,13,14,15],
#     'high': [10, 11, 12, 13, 14,10, 11, 12, 13, 14,10, 11, 12, 13, 14],
#     'low': [8, 9, 7, 6, 8,8, 9, 7, 6, 8,8, 9, 7, 6, 8],
#     'volume': [1000, 1200, 900, 1100, 1300,1000, 1200, 900, 1100, 1300,1000, 1200, 900, 1100, 1300],
#     'close': [9, 10, 11, 12, 13,9, 10, 11, 12, 13,9, 10, 11, 12, 13],
#     'open': [9, 10, 8, 8, 8,9, 10, 8, 8, 8,9, 10, 8, 8, 8],
#     'resolution': [1, 1, 1, 1, 1,1, 1, 1, 1, 1,1, 1, 1, 1, 1]
# }

# sample_indicators = {
#     'time': [1, 2, 3, 4, 5,6,7,8,9,10,11,12,13,14,15],
#     'fastslope': [90, 95, 100, 110, 115,90, 95, 100, 110, 115,90, 95, 100, 110, 115],
#     'fsdelta': [90, 95, 100, 110, 115,90, 95, 100, 110, 115,90, 95, 100, 110, 115],
#     'fastslope2': [90, 95, 100, 110, 115,90, 95, 100, 110, 115,90, 95, 100, 110, 115],
#     'ema': [1000, 1200, 900, 1100, 1300,1000, 1200, 900, 1100, 1300,1000, 1200, 900, 1100, 1300]
# }

# #Trida, která drzi instanci ML modelu a jeho konfigurace
# #take se pouziva jako nastroj na pripravu dat pro train a predikci
# #pozor samotna data trida neobsahuje, jen konfiguraci a pak samotny model
# class ModelML:
#     def __init__(self, name: str,
#                 pred_output: PredOutput,
#                 bar_features: list,
#                 ind_features: list,
#                 input_sequences: int,
#                 target: str,
#                 target_reference: str,
#                 train_target_steps: int, #train
#                 train_target_transformation: TargetTRFM, #train
#                 train_epochs: int, #train
#                 train_runner_ids: list = None, #train
#                 train_batch_id: str = None, #train
#                 version: str = "1",
#                 note : str = None,
#                 use_bars: bool = True,
#                 train_remove_cross_sequences: bool = False, #train
#                 #standardne StandardScaler
#                 scalerX: StandardScaler  = StandardScaler(),
#                 scalerY: StandardScaler = StandardScaler(),
#                 model, #Sequential = Sequential()
#                 )-> None:
        
#         self.name = name
#         self.version = version
#         self.note  = note
#         self.pred_output: PredOutput = pred_output
#         #model muze byt take bez barů, tzn. jen indikatory
#         self.use_bars = use_bars
#         #zajistime poradi
#         bar_features.sort()
#         ind_features.sort()
#         self.bar_features = bar_features
#         self.ind_features = ind_features
#         if (train_runner_ids is None or len(train_runner_ids) == 0) and train_batch_id is None:
#             raise Exception("train_runner_ids nebo train_batch_id musi byt vyplnene")
#         self.train_runner_ids = train_runner_ids
#         self.train_batch_id = train_batch_id
#         #target cílový sloupec, který je používám přímo nebo transformován na binary
#         self.target = target
#         self.target_reference = target_reference
#         self.train_target_steps = train_target_steps
#         self.train_target_transformation = train_target_transformation
#         self.input_sequences = input_sequences
#         self.train_epochs = train_epochs
#         #keep cross sequences between runners
#         self.train_remove_cross_sequences = train_remove_cross_sequences
#         self.scalerX = scalerX
#         self.scalerY = scalerY
#         self.model = model

#     def save(self):
#         filename = mu.get_full_filename(self.name,self.version)
#         dump(self, filename)
#         print(f"model {self.name} save")

#     #create X data with features
#     def column_stack_source(self, bars, indicators, verbose = 1) -> np.array:
#         #create SOURCE DATA with features
#         # bars and indicators dictionary and features as input
#         poradi_sloupcu_inds = [feature for feature in self.ind_features if feature in indicators]
#         indicator_data = np.column_stack([indicators[feature] for feature in self.ind_features if feature in indicators])
        
#         if len(bars)>0:
#             bar_data = np.column_stack([bars[feature] for feature in self.bar_features if feature in bars])
#             poradi_sloupcu_bars = [feature for feature in self.bar_features if feature in bars]
#             if verbose == 1:
#                 print("poradi sloupce v source_data", str(poradi_sloupcu_bars + poradi_sloupcu_inds))
#             combined_day_data = np.column_stack([bar_data,indicator_data])
#         else:
#             combined_day_data = indicator_data
#             if verbose == 1:
#                 print("poradi sloupce v source_data", str(poradi_sloupcu_inds))
#         return combined_day_data

#     #create TARGET(Y) data 
#     def column_stack_target(self, bars, indicators) -> np.array:
#         target_base = []
#         target_reference = []
#         try:
#             try:
#                 target_base = bars[self.target]
#             except KeyError:
#                 target_base = indicators[self.target]
#             try:
#                 target_reference = bars[self.target_reference]
#             except KeyError:
#                 target_reference = indicators[self.target_reference]
#         except KeyError:
#             pass
#         target_day_data = np.column_stack([target_base, target_reference])
#         return target_day_data

#     def load_runners_as_list(self, runner_id_list = None, batch_id = None):
#         """Loads all runners data (bars, indicators) for given runners into list of dicts.
        
#         List of runners/train_batch_id may be provided, or self.train_runner_ids/train_batch_id is taken instead.

#         Returns:
#             tuple (barslist, indicatorslist,) - lists with dictionaries for each runner
#         """
#         if runner_id_list is not None:
#             runner_ids = runner_id_list
#             print("loading runners for ",str(runner_id_list))
#         elif batch_id is not None:
#             print("Loading runners for train_batch_id:", batch_id)
#             res, runner_ids = cs.get_archived_runnerslist_byBatchID(batch_id)
#         elif self.train_batch_id is not None:
#             print("Loading runners for TRAINING BATCH self.train_batch_id:", self.train_batch_id)
#             res, runner_ids = cs.get_archived_runnerslist_byBatchID(self.train_batch_id)
#         #pripadne bereme z listu runneru
#         else:
#             runner_ids = self.train_runner_ids
#             print("loading runners for TRAINING runners ",str(self.train_runner_ids))


#         barslist = []
#         indicatorslist = []
#         ind_keys = None
#         for runner_id in runner_ids:
#             bars, indicators = mu.load_runner(runner_id)
#             print(f"runner:{runner_id}")
#             if self.use_bars:
#                 barslist.append(bars)
#                 print(f"bars keys {len(bars)} lng {len(bars[self.bar_features[0]])}")
#             indicatorslist.append(indicators)
#             print(f"indi keys {len(indicators)} lng {len(indicators[self.ind_features[0]])}")
#             if ind_keys is not None and ind_keys != len(indicators):
#                 raise Exception("V runnerech musi byt stejny pocet indikatoru")
#             else:
#                 ind_keys = len(indicators)

#         return barslist, indicatorslist

#     #toto nejspis rozdelit na TRAIN mod (kdy ma smysl si brat nataveni napr. remove cross)
#     def create_sequences(self, combined_data, target_data = None, remove_cross_sequences: bool = False, rows_in_day = None):
#         """Creates sequences of given length seq and optionally target N steps in the future.

#         Returns X(source) a Y(transformed target) - vrací take Y_untransformed - napr. referencni target column pro zobrazeni v grafu (napr. cenu)

#         Volby pro transformaci targetu:
#         - KEEPVAL (keep value as is)
#         - KEEPVAL_MOVE(keep value, move target N steps in the future)

#         další na zámysl (nejspíš ale data budu připravovat ve stratu a využívat jen KEEPy nahoře)
#         - BINARY_prefix - sloupec založený na podmínce, výsledek je 0,1
#         - BINARY_TREND RISING - podmínka založena, že v target columnu stoupají/klesají po target N steps
#          (podvarianty BINARY TREND RISING(0-1), FALLING(0-1), BOTH(-1 - ))
#         - BINARY_READY - předpřipravený sloupec(vytvořený ve strategii jako indikator), stačí jen posunout o target step
#         - BINARY_READY_POSUNUTY - předpřipraveny sloupec (již posunutýo o target M) - stačí brát as is
        
#         Args:
#             combined_data: A list of combined data.
#             target_data: A list of target data (0-target,1-target ref.column)
#             remove_cross_sequences: If to remove crossday sequences
#             rows_in_day: helper dict to remove crossday sequences
#             return_untr: whether to return untransformed reference column

#         Returns:
#             A list of X sequences and a list of y sequences.
#         """

#         if remove_cross_sequences is True and rows_in_day is None:
#             raise Exception("To remove crossday sequences, rows_in_day param required.")

#         if target_data is not None and len(target_data) > 0:
#             target_data_untr = target_data[:,1]
#             target_data = target_data[:,0]
#         else:
#             target_data_untr = []
#             target_data = []

#         X_train = []
#         y_train = []
#         y_untr = []
#         #comb data shape (4073, 13)
#         #target shape (4073, 1)
#         print("Start Sequencing")
#         #range sekvence podle toho jestli je pozadovan MOVE nebo NE
#         if self.train_target_transformation == TargetTRFM.KEEPVAL_MOVE:
#             right_offset = self.input_sequences + self.train_target_steps
#         else:
#             right_offset= self.input_sequences
#         for i in range(len(combined_data) - right_offset):

#             #take neresime cross sekvence kdyz neni vyplneni target nebo neni vyplnena rowsinaday
#             if  remove_cross_sequences is True and not self.is_same_day(i,i + right_offset, rows_in_day):
#                 print(f"sekvence vyrazena. NEW Zacatek {combined_data[i, 0]} konec {combined_data[i + right_offset, 0]}")
#                 continue

#             #pridame sekvenci
#             X_train.append(combined_data[i:i + self.input_sequences])
            
#             #target hodnotu bude ponecha (na radku mame jiz cilovy target)
#             #nebo vezme hodnotu z N(train_target_steps) baru vpredu a da jako target k radku
#             #je rizeno nastavenim right_offset vyse
#             if target_data is not None and len(target_data) > 0:
#                 y_train.append(target_data[i + right_offset])

#             #udela binary transformaci targetu
#             # elif self.target_transformation == TargetTRFM.BINARY_TREND_UP:
#             #     #mini loop od 0 do počtu target steps - zda jsou successively rising
#             #     #radeji budu resit vizualne conditional indikatorem pri priprave dat
#             #     rising = False
#             #     for step in range(0,self.train_target_steps):
#             #         if target_data[i + self.input_sequences + step] < target_data[i + self.input_sequences + step + 1]:
#             #             rising = True
#             #         else:
#             #             rising = False
#             #             break
#             #     y_train.append([1] if rising else [0])
#             #     #tato zakomentovana varianta porovnava jen cenu ted a cenu na target baru
#             #     #y_train.append([1] if target_data[i + self.input_sequences] < target_data[i + self.input_sequences + self.train_target_steps] else [0])
#             if target_data is not None and len(target_data) > 0:
#                 y_untr.append(target_data_untr[i + self.input_sequences])
#         return np.array(X_train), np.array(y_train), np.array(y_untr)

#     def is_same_day(self, idx_start, idx_end, rows_in_day):
#         """Helper for sequencing enables to recognize if the start/end index are from the same day.

#         Used for sequences to remove cross runner(day) sequences.

#         Args:
#             idx_start: Start index
#             idx_end: End index
#             rows_in_day: 1D array containing number of rows(bars,inds) for each day. 
#                          Cumsumed defines edges where each day ends. [10,30,60]

#         Returns:
#             A boolean

#         refactor to vectors if possible
#             i_b, i_e
#             podm_pole = i_b<pole and i_s >= pole
#              [10,30,60]
#         """
#         for i in rows_in_day:
#             #jde o polozku na pomezi - vyhazujeme
#             if idx_start < i and idx_end >= i:
#                 return False
#             if idx_start < i and idx_end < i:
#                 return True
#         return None

#     #vytvori X a Y data z nastaveni self
#     #pro vybrane runnery stahne data, vybere sloupce dle faature a target
#     #a vrátí jako sloupce v numpy poli
#     #zaroven vraci i rows_in_day pro nasledny sekvencing
#     def load_data(self, runners_ids: list = None, batch_id: list = None, source: Source = Source.RUNNERS):
#         """Service to load data for the model. Can be used for training or for vector prediction.

#         If input data are not provided, it will get the value from training model configuration (train_runners_ids, train_batch_id)

#         Args:
#             runner_ids: 
#             batch_id:
#             source: To load sample data.

#         Returns:
#             source_data,target_data,rows_in_day
#         """
#         rows_in_day = []
#         indicatorslist = []
#         #bud natahneme samply
#         if source == Source.SAMPLES:
#             if self.use_bars:
#                 bars = sample_bars
#             else:
#                 bars = {}
#             indicators = sample_indicators
#             indicatorslist.append(indicators)
#         #nebo dotahneme pozadovane runnery
#         else:
#             #nalodujeme vsechny runnery jako listy (bud z runnerids nebo dle batchid)
#             barslist, indicatorslist = self.load_runners_as_list(runner_id_list=runners_ids, batch_id=batch_id)
#             #nerozumim
#             bl  = deepcopy(barslist)
#             il = deepcopy(indicatorslist)
#             #a zmergujeme jejich data dohromady 
#             bars = mu.merge_dicts(bl)
#             indicators = mu.merge_dicts(il)

#         #zaroven vytvarime pomocny list, kde stale drzime pocet radku per day (pro nasledny sekvencing)
#         #zatim nad indikatory - v budoucnu zvazit, kdyby jelo neco jen nad barama
#         for i, val in enumerate(indicatorslist):
#             #pro prvni klic z indikatoru pocteme cnt
#             pocet = len(indicatorslist[i][self.ind_features[0]])
#             print("pro runner vkladame pocet", pocet)
#             rows_in_day.append(pocet)

#         rows_in_day = np.array(rows_in_day)
#         rows_in_day = np.cumsum(rows_in_day)
#         print("celkove pole rows_in_day(cumsum):", rows_in_day)

#         print("Data LOADED.")
#         print(f"number of indicators {len(indicators)}")
#         print(f"number of bar elements{len(bars)}")
#         print(f"ind list length {len(indicators['time'])}")
#         print(f"bar list length {len(bars['time'])}")

#         self.validate_available_features(bars, indicators)    

#         print("Preparing FEATURES")
#         source_data, target_data = self.stack_bars_indicators(bars, indicators)
#         return source_data, target_data, rows_in_day
    
#     def validate_available_features(self, bars, indicators):
#         for k in self.bar_features:
#             if not k in bars.keys():
#                 raise Exception(f"Missing bar feature {k}")

#         for k in self.ind_features:
#             if not k in indicators.keys():
#                 raise Exception(f"Missing ind feature {k}")    

#     def stack_bars_indicators(self, bars, indicators):
#         print("Stacking dicts to numpy")
#         print("Source - X")
#         source_data = self.column_stack_source(bars, indicators)
#         print("shape", np.shape(source_data))
#         print("Target - Y", self.target)
#         target_data = self.column_stack_target(bars, indicators)
#         print("shape", np.shape(target_data))

#         return source_data, target_data

#     #pomocna sluzba, ktera provede vsechny transformace a inverzni scaling  a vyleze z nej predikce
#     #vstupem je standardni format ve strategii (state.bars, state.indicators)
#     #vystupem je jedna hodnota
#     def predict(self, bars, indicators) -> float:
#         #oriznuti podle seqence - pokud je nastaveno v modelu 
#         lastNbars = slice_dict_lists(bars, self.input_sequences)
#         lastNindicators =  slice_dict_lists(indicators, self.input_sequences)
#         # print("last5bars", lastNbars)
#         # print("last5indicators",lastNindicators)

#         combined_live_data = self.column_stack_source(lastNbars, lastNindicators, verbose=0)
#         #print("combined_live_data",combined_live_data)
#         combined_live_data = self.scalerX.transform(combined_live_data)
#         combined_live_data = np.array(combined_live_data)
#         #print("last 5 values combined data shape", np.shape(combined_live_data))

#         #converts to 3D array 
#         # 1 number of samples in the array.
#         # 2 represents the sequence length.
#         # 3 represents the number of features in the data.
#         combined_live_data = combined_live_data.reshape((1, self.input_sequences, combined_live_data.shape[1]))

#         # Make a prediction
#         prediction = self.model(combined_live_data, training=False)
#         #prediction = prediction.reshape((1, 1))
#         # Convert the prediction back to the original scale
#         prediction = self.scalerY.inverse_transform(prediction)
#         return float(prediction)
