import numpy as np
from v2realbot.utils.utils import isfalling
arr = np.array([1, np.nan, 3, 4, 5, 6, 2.3]) 
print(arr)
b = list(arr)
a = b[-1]
print(a)
if str(a) == "nan":
    print(a,"je nan")

rsi = [1,2,3,4,5]
print(isfalling(rsi,1))