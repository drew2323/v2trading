

import numpy as np


arr = np.array(values)

# Find the current value and the minimum and maximum values
current_value = arr[-1]
min_value = np.min(arr)
max_value = np.max(arr)

#remapping to -1 and 1


remapped_value = 2 * (current_value - min_value) / (max_value - min_value) - 1


#remap to range 0 and 1
remapped_value = (atr10[-1] - np.min(atr10)) / (np.max(atr10) - np.min(atr10))

    cp.statement = "np.mean(vwap[-(abs(int(50*atr10r[-1]))):])"

