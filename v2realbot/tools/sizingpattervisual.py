import numpy as np
from scipy.interpolate import interp1d
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
input_values = np.linspace(min(pattern_x), max(pattern_x), 1000)  # Increase the number of points

# Bezier interpolation
interp_func = interp1d(pattern_x, pattern_y, kind='cubic')
multipliers_cubic = interp_func(input_values)

multipliers_linear = np.interp(input_values, pattern_x, pattern_y)


# Plotting multipliers_linear and multipliers_cubic on the same canvas
plt.figure(figsize=(10, 6))
plt.plot(pattern_x, pattern_y, 'o', label='Original Points')
plt.plot(input_values, multipliers_linear, label='Linear Interpolation')
plt.plot(input_values, multipliers_cubic, label='Cubic Interpolation')
plt.xlabel('X values')
plt.ylabel('Interpolated Multipliers')
plt.title('Interpolation Comparison')
plt.legend()
plt.grid(True)
plt.show()

# # Plotting multipliers_cubic
# plt.figure(figsize=(10, 6))
# plt.plot(pattern_x, pattern_y, 'o', label='Original Points')
# plt.plot(input_values, multipliers_cubic, label='Cubic Interpolation')
# plt.xlabel('X values')
# plt.ylabel('Interpolated Multipliers')
# plt.title('Cubic Interpolation Chart')
# plt.legend()
# plt.grid(True)
# plt.show()
