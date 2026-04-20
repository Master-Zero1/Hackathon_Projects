#importing all the libraries
import numpy as np
import matplotlib.pyplot as plt
from tkinter import Tk, filedialog
from scipy.signal import butter, filtfilt, iirnotch, savgol_filter
from scipy.signal import find_peaks


#loading the ecg_Dataset
Tk().withdraw()
file_path = filedialog.askopenfilename()
data = np.loadtxt(file_path, skiprows=1, delimiter=',', usecols=1)


#plotting the ecg noised signal
plt.figure(figsize=(12, 4))
plt.plot(data[5000:6000])   # only first 2000 samples
plt.title("ECG (Zoomed)")
plt.xlabel("Samples")
plt.ylabel("Amplitude")
plt.grid(True)
plt.show()


#adding all the denoising filters

    #1. The high pass filter - (removes the wobble caused by breathing) - target noise: baseline wander (targets 0.5Hz)
    #2. The low pass filter - (removes the high frequency noise) - target noise: muscle Noise and high frequency artifacts (targets 40-150Hz)
    #3. The notch filter - (removes the power line interference) - target noise: power line interference (targets 50Hz or 60Hz depending on the region)
    #4. savitzky-golay filter - (smooths the signal while preserving features) - target noise: residual white noise, it keeps the peaks sharp.
    
def apply_highpass(signal_data, fs=360):
    b_high, a_high = butter(2, 0.5, btype='highpass', fs=fs)
    high_passed_signal = filtfilt(b_high, a_high, signal_data)
    return high_passed_signal

def apply_lowpass(signal_data, fs=360):
    b_low, a_low = butter(2, 40, btype='lowpass', fs=fs)
    low_passed_signal = filtfilt(b_low, a_low, signal_data)
    return low_passed_signal

def apply_notch(signal_data, fs=360):
    b_notch, a_notch = iirnotch(50, 30, fs)
    notch_filtered_signal = filtfilt(b_notch, a_notch, signal_data)
    return notch_filtered_signal

def apply_savgol(signal_data):
    savgol_filtered_signal = savgol_filter(signal_data, window_length=11, polyorder=3)
    return savgol_filtered_signal

s1 = apply_highpass(data, fs=360)
s2 = apply_lowpass(s1, fs=360)
s3 = apply_notch(s2, fs=360)
s4 = apply_savgol(s3)

final_signal = s4


#plotting the final denoised signal
plt.figure(figsize=(12, 4))
plt.plot(final_signal[5000:6000], color = 'orange') # only first 2000 samples
plt.title("Denoised ECG (Zoomed)")
plt.xlabel("Samples")
plt.ylabel("Amplitude")
plt.grid(True)
plt.show()


#comparing the original and denoised signal
plt.figure(figsize=(12, 10))
plt.subplot(2, 1, 1)
plt.plot(data[5000:6000], label='Original Noisy ECG')
plt.title("Original Noisy ECG (Zoomed)")
plt.xlabel("Samples")
plt.ylabel("Amplitude")
plt.grid(True)
plt.legend()
plt.subplot(2, 1, 2)
plt.plot(final_signal[5000:6000], label='Denoised ECG', color = 'orange')
plt.title("Denoised ECG (Zoomed)")
plt.xlabel("Samples")
plt.ylabel("Amplitude")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()


#Ecg - quality report
#1. Signal-to-Noise Ratio (SNR): Calculate the SNR before and after denoising to quantify the improvement in signal quality.
#2. Root Mean Square Error (RMSE): Compute the RMSE between the original noisy signal and the denoised signal to assess how closely the denoised signal matches the original.
#3. Heart rate (BPM): Extract the heart rate from both the original and denoised signals to see if the denoising process preserves the physiological information.
#4. Peak amplitude preservation: Compare the amplitude of the R-peaks in the original and denoised signals to ensure that the denoising process does not distort critical features of the ECG.

def calculate_snr(signal_power, noise_power):
    return 10*np.log10(signal_power/noise_power)

def calculate_rmse(original, denoised):
    return np.sqrt(np.mean((original-denoised) ** 2))

def calculate_heart_rate(signal, fs=360):
    peaks, _ = find_peaks(signal, distance=fs*0.35, height = 0.6)  # Assuming a minimum heart rate of 60 BPM
    heart_rate = len(peaks)*(60/(len(signal)/ fs))  # Convert to BPM
    return heart_rate

def calculate_peak_amplitude_preservation(original, denoised):
    original_peaks, _ = find_peaks(original, distance=360*0.35, height = 0.5)
    denoised_peaks, _ = find_peaks(denoised, distance=360*0.35, height = 0.5)
    
    original_peak_amplitudes = original[original_peaks]
    denoised_peak_amplitudes = denoised[denoised_peaks]
    
    # Calculating the average peak amplitude preservation
    if len(original_peak_amplitudes)>0 and len(denoised_peak_amplitudes)>0:
        preservation_ratio = np.mean(denoised_peak_amplitudes)/np.mean(original_peak_amplitudes)
        return preservation_ratio
    else:
        return None
    

# Calculate metrics
noise = data -final_signal
signal_power_clean = np.var(final_signal)
noise_power_removed = np.var(noise)
residual_noise_power = np.var(final_signal-apply_lowpass(final_signal, fs=360))  # Estimate residual noise power after low-pass filtering 
noise_reduction_db = 10*np.log10(noise_power_removed/residual_noise_power) if residual_noise_power > 0 else float('inf')  # Avoid division by zero
snr_before = 10*np.log10(np.var(data)/noise_power_removed)  # SNR before denoising (using original signal as reference)
snr_after = 10*np.log10(signal_power_clean/noise_power_removed)
rmse = calculate_rmse(data, final_signal)
heart_rate_before = calculate_heart_rate(data)
heart_rate_after = calculate_heart_rate(final_signal)
peak_amplitude_preservation = calculate_peak_amplitude_preservation(data, final_signal)


# Print results
print(f"SNR Before Denoising: {snr_before:.2f} dB")
print(f"SNR After Denoising: {snr_after:.2f} dB")
print(f"Total Noise Reduction: {noise_reduction_db:.2f} dB")
print(f"RMSE between Original and Denoised Signal: {rmse:.4f}")
print(f"Heart Rate Before Denoising: {heart_rate_before:.2f} BPM")
print(f"Heart Rate After Denoising: {heart_rate_after:.2f} BPM")
print(f"Peak Amplitude Preservation Ratio: {peak_amplitude_preservation:.4f}")