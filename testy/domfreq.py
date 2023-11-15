import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft

# Define the sampling frequency and time vector
fs = 500  # Sampling frequency
t = np.arange(0, 1, 1/fs)  # Time vector

# Define the frequencies
f1 = 5    # Frequency that occurs most often but with lower amplitude
f2 = 20   # Frequency with the highest amplitude

# Creating the individual signals
signal_f1 = 0.5 * np.sin(2 * np.pi * f1 * t)  # Signal with frequency f1
signal_f2 = 2 * np.sin(2 * np.pi * f2 * t)    # Signal with frequency f2

# Composite signal
signal = signal_f1 + signal_f2

# Performing a Fourier Transform
freq = np.fft.fftfreq(len(t), 1/fs)
fft_values = fft(signal)

# Plotting all the signals and the frequency spectrum
plt.figure(figsize=(14, 10))

# Plot 1: Composite Signal
plt.subplot(4, 1, 1)
plt.plot(t, signal)
plt.title('Composite Signal (f1 + f2)')
plt.xlabel('Time [s]')
plt.ylabel('Amplitude')

# Plot 2: Frequency f1 Signal
plt.subplot(4, 1, 2)
plt.plot(t, signal_f1)
plt.title('Individual Frequency f1 Signal')
plt.xlabel('Time [s]')
plt.ylabel('Amplitude')

# Plot 3: Frequency f2 Signal
plt.subplot(4, 1, 3)
plt.plot(t, signal_f2)
plt.title('Individual Frequency f2 Signal')
plt.xlabel('Time [s]')
plt.ylabel('Amplitude')

# Plot 4: Frequency Spectrum
plt.subplot(4, 1, 4)
plt.plot(freq, np.abs(fft_values))
plt.title('Frequency Spectrum of Composite Signal')
plt.xlabel('Frequency [Hz]')
plt.ylabel('Amplitude')
plt.xlim([0, 30])

# Highlighting the dominant frequencies in the spectrum
plt.axvline(x=f1, color='green', linestyle='--', label='Frequency f1')
plt.axvline(x=f2, color='red', linestyle='--', label='Frequency f2')

plt.legend()
plt.tight_layout()
plt.show()
