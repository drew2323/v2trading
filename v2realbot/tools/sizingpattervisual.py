import numpy as np
import matplotlib.pyplot as plt

# Sem zadat pattern X a Y pro VIZUALIZACI

#minutes
pattern_x = [0, 30, 90, 200, 300, 390]
pattern_y = [0.1, 0.5, 0.8, 1, 0.6, 0.1]

#bar index - použitelné u time scale barů
pattern_x = [0, 30, 90, 200, 300, 390]
pattern_y = [0.1, 0.5, 0.8, 1, 0.6, 0.1]

#celkový profit

# Generating a range of input values for interpolation
input_values = np.linspace(min(pattern_x), max(pattern_x), 500)
multipliers = np.interp(input_values, pattern_x, pattern_y)

# Plotting
plt.figure(figsize=(10, 6))
plt.plot(pattern_x, pattern_y, 'o', label='Original Points')
plt.plot(input_values, multipliers, label='Interpolated Values')
plt.xlabel('X values')
plt.ylabel('Interpolated Multipliers')
plt.title('Interpolation Chart')
plt.legend()
plt.grid(True)
plt.show()
