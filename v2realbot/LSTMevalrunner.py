import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
import v2realbot.ml.mlutils as mu
from keras.layers import LSTM, Dense
import matplotlib.pyplot as plt
from v2realbot.ml.ml import ModelML
from v2realbot.enums.enums import PredOutput, Source, TargetTRFM
from v2realbot.controller.services import get_archived_runner_details_byID, update_archive_detail
# from collections import defaultdict
# from operator import itemgetter
from joblib import load

#TODO - DO API
# v ml atomicke api pro evaluaci (runneru, batche)
# v services: model.add_vector_prediction_to_archrunner_as_new_indicator (vrátí v podstate obohacený archDetail) - nebo i ukládat do db? uvidime
# v rest api prevolani
# db support: zatim jen ciselnik modelu + jeho zakladni nastaveni, obrabeci api, load modelu zatim z file

cfg: ModelML = mu.load_model("model1", "0.1")


#EVALUATE SPECIFIC RUNNER - VECTOR BASED (toto dat do samostatne API pripadne pak udelat nadstavnu na batch a runners)
#otestuje model na neznamem runnerovi, seznamu runneru nebo batch_id



runner_id = "a38fc269-8df3-4374-9506-f0280d798854"
save_new_ind = True
source_data, target_data, rows_in_day = cfg.load_data(runners_ids=[runner_id])

if len(rows_in_day) > 1:
    #pro vis se cela tato sluzba volat v loopu
    raise Exception("Vytvareni indikatoru dostupne zatim jen pro jeden runner")

#scalujeme X
source_data = cfg.scalerX.fit_transform(source_data)

#tady si vyzkousim i skrz vice runneru
X_eval, y_eval, y_eval_ref = cfg.create_sequences(combined_data=source_data, target_data=target_data,remove_cross_sequences=True, rows_in_day=rows_in_day)

#toto nutne?
X_eval = np.array(X_eval)
y_eval = np.array(y_eval)
y_eval_ref = np.array(y_eval_ref)
#scaluji target - nemusis
#y_eval = cfg.scalerY.fit_transform(y_eval)

X_eval = cfg.model.predict(X_eval)
X_eval = cfg.scalerY.inverse_transform(X_eval)
print("po predikci x_eval shape", X_eval.shape)

#pokud mame dostupnou i target v runneru, pak pridame porovnavaci indikator
difference_mse = None
if len(y_eval) > 0:
    #TODO porad to pliva 1 hodnotu
    difference_mse = mean_squared_error(y_eval, X_eval,multioutput="raw_values")

print("ted mam tedy dva nove sloupce")
print("X_eval", X_eval.shape)
if difference_mse is not None:
    print("difference_mse", difference_mse.shape)
print(f"zplostime je, dopredu pridame {cfg.input_sequences-1} a dozadu nic")
#print(f"a melo by nam to celkem dat {len(bars['time'])}")
#tohle pak nejak doladit, ale vypada to good
#plus do druheho indikatoru pridat ten difference_mse

#TODO jeste je posledni hodnota predikce nejak OFF (2.52... ) - podivat se na to
#TODO na produkci srovnat se skutecnym BT predictem (mozna zde bude treba seq-1) - 
# prvni predikce nejspis uz bude na desítce
ind_pred = list(np.concatenate([np.zeros(cfg.input_sequences-1), X_eval.ravel()]))
print(ind_pred)
print(len(ind_pred))
print("tada")
#ted k nim pridame 

if save_new_ind:
    #novy ind ulozime do archrunnera (na produkci nejspis jen show)
    res, sada = get_archived_runner_details_byID(runner_id)
    if res == 0:
        print("ok")
    else:
        print("error",res,sada)
        raise Exception(f"error loading runner {runner_id} : {res} {sada}")

    sada["indicators"][0]["pred_added"] = ind_pred

    req, res = update_archive_detail(runner_id, sada)
    print(f"indicator pred_added was ADDED to {runner_id}")


# Plot the predicted vs. actual
plt.plot(y_eval, label='Target')
plt.plot(X_eval, label='Predicted')
#TODO zde nejak vymyslet jinou pricelinu - jako lightweight chart
if difference_mse is not None:
    plt.plot(difference_mse, label='diference')
    plt.plot(y_eval_ref, label='reference column - vwap')
plt.plot()
plt.legend()
plt.show()
