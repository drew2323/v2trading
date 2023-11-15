import numpy as np
from array import array

# Original list
puvodni = array('i', [1, 2, 3, 4])

# Create a NumPy array using the original list
numpied = np.array(puvodni)

# Now, if puvodni changes, numpied will be updated as well
puvodni.append(5)

# Check the updated numpied array
print(numpied)