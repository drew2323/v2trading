import numpy as np
# import v2realbot.controller.services as cs
from joblib import load
from v2realbot.config import DATA_DIR

def get_full_filename(name, version = "1"):
  return DATA_DIR+'/models/'+name+'_v'+version+'.pkl'

def load_model(name, version = "1"):
   filename = get_full_filename(name, version)
   return load(filename)
   
#pomocne funkce na manipulaci s daty

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
    res, sada = cs.get_archived_runner_details_byID(runner_id)
    if res == 0:
        print("ok")
    else:
        print("error",res,sada)
        raise Exception(f"error loading runner {runner_id} : {res} {sada}")

    bars = sada["bars"]
    indicators = sada["indicators"][0]
    return bars, indicators
