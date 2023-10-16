import numpy as np

indicators = dict(time=[1,2,3], rsi=[15,16,17], vwap=[5,6,7])
bars = dict(time=[1,2,3], open=[15,16,17], close=[5,6,7])

#last values
operation = "rsi[-1] * (vwap[-1] + 1) + var1 + np.mean(rsi[-2:])"

#nejdriv naharadit indikatory skutečnými hodnotami

#muzu iterovat nad indikatory
# for key in indicators.keys():
#     if key != 'time':
#         operation = operation.replace(key, f"indicators['{key}'][-1]")

var1 = 13

#a nebo si jednou pri initiu vytvorim mapovaci dictionary indikatorů a barů
local_dict_inds = {key: indicators[key] for key in indicators.keys() if key != "time"}
local_dict_bars = {key: bars[key] for key in bars.keys() if key != "time"}

local_dict = {**local_dict_inds, **local_dict_bars}

print(local_dict)


print(operation)
print(eval(operation, None, local_dict))