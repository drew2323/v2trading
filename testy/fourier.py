import numpy as np
import scipy.fft as fft


time_series = np.array(prices)
n = len(time_series)

# Compute the Fourier transform
yf = fft(time_series)
xf = np.linspace(0.0, 1.0/(2.0), n//2)
# Compute the Fourier transform
yf = np.abs(fft(time_series))

# Find the corresponding frequencies
frequencies = xf

# Find the corresponding amplitudes
amplitudes = 2.0/n * np.abs(yf[:n//2])

# Interpret the amplitudes and frequencies
for freq, ampl in zip(frequencies, amplitudes):
    print(f"Frequency: {freq}, Amplitude: {ampl}")