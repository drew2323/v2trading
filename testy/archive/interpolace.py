import scipy.interpolate as spi
import matplotlib.pyplot as plt
import numpy as np

# x = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
# y = [4, 7, 11, 16, 22, 29, 38, 49, 63, 80]

val = 10
new = np.interp(val, [0, 50, 100], [0, 1, 2])
print(new)
# y_interp = spi.interp1d(x, y)

#find y-value associated with x-value of 13
#print(y_interp(13))


#create plot of x vs. y
#plt.plot(x, y, '-ob')




