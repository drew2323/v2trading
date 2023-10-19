import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
import v2realbot.ml.mlutils as mu
from keras.layers import LSTM, Dense
import matplotlib.pyplot as plt
from v2realbot.ml.ml import ModelML
from v2realbot.enums.enums import PredOutput, Source, TargetTRFM
# from collections import defaultdict
# from operator import itemgetter
from joblib import load

# region Notes

#ZAKLAD PRO TRAINING SCRIPT na vytvareni model u
# TODO
# podpora pro BINARY TARGET
# podpora hyperpamaetru (activ.funkce sigmoid atp.)
# vyuzit distribuovane prostredi - nebo aspon vlastni VM
# dopracovat denni identifikatory typu lastday close, todays open atp.
# random SEARCH a grid search
# udelat nejaka model metadata (napr, trenovano na (runners+obdobi), nastaveni treningovych dat, počet epoch, hyperparametry, config atribu atp.) - mozna persistovat v db
# udelat nejake verzovani
# predelat do GUI a modulu
# vyuzit VectorBT na dohledani optimalizovanych parametru napr. pro buy,sell atp. Vyuzit podobne API na pripravu dat jako model.
# EVAL MODEL - umoznit vektorové přidání indikátoru do runneru (např. predikce v modulu, vectorBT, optimalizace atp) - vytvorit si na to API, podobne co mam, nacte runner, transformuje, sekvencuje, provede a pak zpetne transformuje a prida jako dalsi indikator. Lze pak použít i v gui.
# nove tlacitko "Display model prediction" na urovni archrunnera, které
#   - má volbu model + jestli zobrazit jen predictionu jako novy indikator nebo i mse from ytarget  (nutny i target)
# po spusteni pak:
#   - zkonztoluje jestli runner ma indikatory,ktere odpovidaji features modelu (bar_ftrs, ind_ftrs, optional i target)
#   - vektorově doplní predictionu (transformuje data, udela predictionu a Y transformuje zpet)
#    - vysledek (jako nove indikatory) implantuje do runnerdetailu a zobrazi
# podivat se na dalsi parametry kerasu, napr. false positive atp.
# podivat se jeste na rozdil mezi vectorovou predikci a skalarni - proc je nekdy rozdil, odtrasovat - pripadne pogooglit
#      odtrasovat, nekde je sum (zkusit si oboji v jednom skriptu a porovnat)

#TODO NAPADY Na modely
#1.binary identifikace trendu napr. pokud nasledujici 3 bary rostou (0-1) nebo nasledujici bary roste momentum
#2.soustredit se na modely s vystupem 0-1 nebo -1 až 1
#3.Vyzkouset jeden model, ktery by identifikoval trendy v obou smerech - -1 pro klesani a 1 pro stoupání.
#4.vyzkouset zda model vytvoreny z casti dne nebude funkcni na druhe casti (on the fly daily models)
#5.zkusit modely s a bez time (prizpusobit tomu kod v ModelML - zejmena jak na crossday sekvence) - mozna ze zecatku dat aspon pryc z indikatoru? 
# Dat vsechny zbytecne features pryc, nechat tam jen ty podstatne - attention, tak cílím.
#6. zkusit vyuzit tickprice v nejaekm modelu, pripadne pak dalsi CBAR indikatory . vymslet tickbased features
#7. zkusit jako features nevyuzit standardni ceny, ale pouze indikatory reprezentujici chovani (fastslope,samebarslope,volume,tradencnt)
#8. relativni OHLC -  model pouzivajici (jen) bary, ale misto hodnot ohlc udelat features reprezentujici vztahy(pomery) mezi temito velicinami. tzn. relativni ohlc
#9. jiny pristup by byl ucit model na konkretnich  chunkach, ktere chci aby mi identifikoval. Např. určité úseky. Vymyslet. Buď nyni jako test intervaly, ale v budoucnu to treba jen nejak oznacit a poslat k nauceni. Pripadne pak udelat nejaky vycuc.
#10. mozna správným výběrem targetu, můžu taky naučit jen určité věci. Specializace. Stačí když se jednou dvakrát denně aktivuje.
# 11. udelat si go IN model, ktery pomuze strategii generovat vstup - staci jen aby mel trochu lepsi edge nez conditiony, o zbytek se postara logika strategie
# 12. model pro neagregované nebo jen filtroné či velmi lehce agregované trady? - tickprice
# 13. jako featury pouzit Fourierovo transformaci, na sekundovem baru nebo tickprice

#DULEZITE
# soustredit se v modelech na predikci nasledujici hodnoty, ideálně nějaký vektor ukazující směr (např. 0 - 1, kde nula nebude růst, 1 - bude růst strmě)
# pro predikcí nějakého většího trendu, zkusti více modelů na různých rozlišení, každý ukazuje
# hodnotu na svém rozlišení a jeho kombinace mi může určit vstup. Zkusit zda by nešel i jeden model.
# Každopádně se soustředit 
# 1) na další hodnotu (tzn. vstupy musí být bezprostředně ovlivňující tuto (samebasrlope, atp.))
# 2) její výše ukazuje směr na tomto rozlišení
# 3) ideálně se učit z každého baru, tzn. cílová hodnota musí být známá u každého baru 
#      (binary ne, potřebuju linární vektor) -  i když 1 a 0 target v závislosti na stoupání a klesání by mohla být ok, 
#       ale asi příliš restriktivní, spíš bych tam mohl dát jak moc. Tzn. +0.32, -0.04. Učilo by se to míru stoupání.
#       Tu míru tam potřebuju zachovanou.
# pak si muzu rict, když je urcite pravdepodobnost, ze to bude stoupat (tzn. dalsi hodnota) na urovni 1,2,3 - tak jduvstup
# zkusit na nejnižší úrovni i předvídat CBARy, směr dalšího ticku. Vyzkoušet.

##TODO - doma
#bar_features a ind_features do dokumentace SL classic, stejne tak conditional indikator a mathop indikator
#TODO - co je třeba vyvinout
# GENERATOR test intervalu (vstup name, note, od,do,step)
# napsat API, doma pak simple GUI
# vyuziti ATR (jako hranice historickeho rozsahu) - atr-up, atr-down
#    nakreslit v grafu atru = close+atr, atrd = close-atr
#    pripadne si vypocet atr nejak customizovat, prip. ruzne multiplikatory pro high low, pripadne si to vypocist podle sebe
#    vyuziti:
#        pro prekroceni nejake lajny, napr. ema nebo yesterdayclose
#               - k identifikaci ze se pohybuje v jejim rozsahu
#              - proste je to buffer, ktery musi byt prekonan, aby byla urcita akce
#        pro learning pro vypocet conditional parametru (1,0,-1) prekroceni napr. dailyopen, yesterdayclose, gapclose
#             kde 1 prekroceno, 0 v rozsahu (atr), -1 prekroceno dolu - to pomuze uceni
#       vlastni supertrend strateige
#       zaroven moznost vyuzit klouzave či parametrizovane atr, které se na základě
#       určitých parametrů bude samo upravovat a cíleně vybočovat z KONTRA frekvencí, např. randomizovaný multiplier nebo nejak jinak ovlivneny minulým
# v indikatorech vsude kde je odkaz ma source jako hodnotu tak defaultne mit moznost uvest lookback, napr. bude treba porovnavat nejak cenu vs predposledni hodnotu ATRka (nechat az vyvstane pozadavek)
# zacit doma na ATRku si postavit supertrend, viz pinescript na ploše


#TODO - obecne vylepsovaky
# 1. v GUI graf container do n-TABů, mozna i draggable order, zaviratelne na Xko (innerContainer)
# 2. mit mozna specialni mod na pripravu dat (agreg+indikator, tzn. vse jen bez vstupů) - můžu pak zapracovat víc vectorové doplňování dat
#      TOTO:: mozna by postacil vypnout backtester (tzn. no trades) - a projet jen indikatory. mozna by slo i vectorove optimalizovat.
#      indikatory by se mohli predsunout pred next a next by se vubec nemusel volat (jen nekompatibilita s predch.strategiemi)
# 3. kombinace fastslope na fibonacci delkach (1,2,3,5..) jako dobry vstup pro ML
# 4. podivat se na attention based LSTM zda je v kerasu implementace
# do grafu přidat togglovatelné hranice barů určitých rozlišení - což mi jen udělá čáry Xs od sebe (dobré pro navrhování)
# 5. vymyslet optimalizovane vyuziti modelu na produkci (nejak mit zkompilovane, aby to bylo raketově pro skalár) - nyní to backtest zpomalí 4x
# 6. CONVNETS for time series forecasting - small 1D convnets can offer a fast alternative to RNNs for simple tasks such as text classification and timeseries forecasting.
#     zkusit small conv1D pro identifikaci víření před trendem, např. jen 6 barů - identifikovat dobře target, musí jít o tutovku na targetu
#     pro covnet zkusit cbar price, volume a time. Třeba to zachytí víření (ripples)
# Další oblasti k predikci jsou ripples, vlnky - předzvěst nějakého mocnějšího pohybu. A je pravda, že předtím se mohou objevit nějaké indicie. Ty zkus zachytit.
# Do runner_headers pridat bt_from, bt_to - pro razeni order_by, aby se runnery vzdy vraceli vzestupne dle data (pro machine l)

#TODO
# vyvoj modelů workflow s LSTMtrain.py
# 1) POC - pouze zde ve skriptu, nad 1-2 runnery, okamžité zobrazení v plotu,
#           optimalizace zakl. features a hyperparams. Zobrazit i u binary nejak cenu.
# 2) REALITY CHECK - trening modelu na batchi test intervalu, overeni ve strategii v BT, zobrazeni predikce v RT chartu
# 3) FINAL TRAINING
# testovani predikce


#TODO tady
# train model
#     - train data-  batch nebo runners
#     - test data  - batch or runners (s cim porovnavat/validovat)
#     - vyber architektury
#     - soucast skriptu muze byt i porovnavacka pripadne nejaky search optimalnich parametru

#lstmtrain - podporit jednotlive kroky vyse
#modelML - udelat lepsi PODMINKY
#frontend? ma cenu? asi ano - GUI na model - new - train/retrain-change
#  (vymyslet jak v gui chytře vybírat arch modelu a hyperparams, loss, optim - treba nejaka templata?)
#   mozna ciselnik architektur s editačním polem pro kód -jen pár řádků(.add, .compile) přidat v editoru
#    vymyslet jak to udělat pythonově
#testlist generator api

# endregion

#if null,the validation is made on 10% of train data
#runnery pro testovani
validation_runners = ["a38fc269-8df3-4374-9506-f0280d798854"]

#u binary bude target bud hotovy indikator a nebo jej vytvorit on the fly
cfg = ModelML(name="model1",
              version = "0.1",
              note = None,
              pred_output=PredOutput.LINEAR,
              input_sequences = 10,
              use_bars = True,
              bar_features = ["volume","trades"],
              ind_features = ["slope20", "ema20","emaFast","samebarslope","fastslope","fastslope4"],
              target='target', #referencni hodnota pro target - napr pro graf
              target_reference='vwap',
              train_target_steps=3,
              train_target_transformation=TargetTRFM.KEEPVAL,
              train_runner_ids =  ["08b7f96e-79bc-4849-9142-19d5b28775a8"],
              train_batch_id = None,
              train_epochs = 10,
              train_remove_cross_sequences = True,
              )

#TODO toto cele dat do TRAIN metody - vcetne pripadneho loopu a podpory API

test_size = None

#kdyz neplnime vstup, automaticky se loaduje training data z nastaveni classy
source_data, target_data, rows_in_day = cfg.load_data()

if len(target_data) == 0:
    raise Exception("target is empty - required for TRAINING - check target column name")

np.set_printoptions(threshold=10,edgeitems=5)
#print("source_data", source_data)
#print("target_data", target_data)
print("rows_in_day", rows_in_day)
source_data = cfg.scalerX.fit_transform(source_data)

#TODO mozna vyhodit to UNTR
#TODO asi vyhodit i target reference a vymyslet jinak

#vytvořeni sekvenci po vstupních sadách  (např. 10 barů) - výstup 3D např. #X_train (6205, 10, 14)
#doplneni transformace target data
X_train, y_train, y_train_ref = cfg.create_sequences(combined_data=source_data,
                                                     target_data=target_data,
                                                     remove_cross_sequences=cfg.train_remove_cross_sequences,
                                                     rows_in_day=rows_in_day)

#zobrazime si transformovany target a jeho referncni sloupec
#ZHOMOGENIZOVAT OSY
plt.plot(y_train, label='Transf target')
plt.plot(y_train_ref, label='Ref target')
plt.plot()
plt.legend()
plt.show()

print("After sequencing")
print("source:X_train", np.shape(X_train))
print("target:y_train", np.shape(y_train))
print("target:", y_train)
y_train = y_train.reshape(-1, 1)

X_complete = np.array(X_train.copy())
Y_complete = np.array(y_train.copy())
X_train = np.array(X_train)
y_train = np.array(y_train)

#target scaluji az po transformaci v create sequence -narozdil od X je stejny shape
y_train = cfg.scalerY.fit_transform(y_train)


if len(validation_runners) == 0:
    test_size = 0.10
# Split the data into training and test sets - kazdy vstupni pole rozdeli na dve
#nechame si takhle rozdelit i referencni sloupec
X_train, X_test, y_train, y_test, y_train_ref, y_test_ref = train_test_split(X_train, y_train, y_train_ref, test_size=test_size, shuffle=False) #random_state=42)

print("Splittig the data")

print("X_train", np.shape(X_train))
print("X_test", np.shape(X_test))
print("y_train", np.shape(y_train))
print("y_test", np.shape(y_test))
print("y_test_ref", np.shape(y_test_ref))
print("y_train_ref", np.shape(y_train_ref))

#print(np.shape(X_train))
# Define the input shape of the LSTM layer dynamically based on the reshaped X_train value
input_shape = (X_train.shape[1], X_train.shape[2])

# Build the LSTM model
#cfg.model = Sequential()
cfg.model.add(LSTM(128, input_shape=input_shape))
cfg.model.add(Dense(1, activation="relu"))
#activation: Gelu, relu, elu, sigmoid... 
# Compile the model
cfg.model.compile(loss='mse', optimizer='adam')
#loss: mse, binary_crossentropy

# Train the model
cfg.model.fit(X_train, y_train, epochs=cfg.train_epochs)

#save the model
cfg.save()

#TBD db layer
cfg: ModelML = mu.load_model(cfg.name, cfg.version)

# region Live predict
#EVALUATE SIM LIVE - PREDICT SCALAR - based on last X items
barslist, indicatorslist = cfg.load_runners_as_list(runner_id_list=["67b51211-d353-44d7-a58a-5ae298436da7"])
#zmergujeme vsechny data dohromady 
bars = mu.merge_dicts(barslist)
indicators = mu.merge_dicts(indicatorslist)
cfg.validate_available_features(bars, indicators)
#VSTUPEM JE standardni pole v strategii
value = cfg.predict(bars, indicators)
print("prediction for LIVE SIM:", value)
# endregion

#EVALUATE TEST DATA - VECTOR BASED
#pokud mame eval runners pouzijeme ty, jinak bereme cast z testovacich dat
if len(validation_runners) > 0:
    source_data, target_data, rows_in_day = cfg.load_data(runners_ids=validation_runners)
    source_data = cfg.scalerX.fit_transform(source_data)
    X_test, y_test, y_test_ref = cfg.create_sequences(combined_data=source_data, target_data=target_data,remove_cross_sequences=True, rows_in_day=rows_in_day)

#prepnout ZDE pokud testovat cely bundle - jinak testujeme jen neznama
#X_test = X_complete
#y_test = Y_complete

X_test = cfg.model.predict(X_test)
X_test = cfg.scalerY.inverse_transform(X_test)

#target testovacim dat proc tu je reshape? y_test.reshape(-1, 1)
y_test =  cfg.scalerY.inverse_transform(y_test)
#celkovy mean? nebo spis vector pro graf?
mse = mean_squared_error(y_test, X_test)
print('Test MSE:', mse)

# Plot the predicted vs. actual
plt.plot(y_test, label='Actual')
plt.plot(X_test, label='Predicted')
#TODO zde nejak vymyslet jinou pricelinu - jako lightweight chart
plt.plot(y_test_ref, label='reference column - price')
plt.plot()
plt.legend()
plt.show()
