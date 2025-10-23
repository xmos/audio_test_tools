# Copyright 2019-2021 XMOS LIMITED.
# This Software is subject to the terms of the XMOS Public Licence: Version 1.
import sys, os
try:
    from scipy.signal import blackmanharris
except ImportError:
    from scipy.signal.windows import blackmanharris
import scipy.signal as spsig
from numpy.fft import rfft, irfft
from numpy import argmax, sqrt, mean, absolute, arange, log10
import numpy as np

use_soundfile = False


try:
    import soundfile as sf
    print("using soundfile")
    use_soundfile = True
except ImportError:
    from scikits.audiolab import Sndfile
    print("using scikits.audiolab")


def rms_flat(a, sample_rate):
    """
    Return the root mean square of all the elements of *a*, flattened out.
    """
    return sqrt(mean(absolute(a)**2))


def find_range(f, x):
    """
    Find range between nearest local minima from peak at index x
    """
    uppermin = lowermin = x
    for i in arange(x+1, len(f)):
        if f[i+1] >= f[i]:
            uppermin = i
            break
    for i in arange(x-1, 0, -1):
        if f[i] <= f[i-1]:
            lowermin = i + 1
            break
    return (lowermin, uppermin)

def peak_locator(f, psd):
    """
    Locate peaks in the PSD
    """
    max_idx = argmax(psd)

    # equation 13.75 in "Understanding Digital Signal Processing" 3rd Ed. by Lyons
    # note 1.72 assumes Blackman Harris window
    C = 1.72*(psd[max_idx+1] - psd[max_idx - 1])/(psd[max_idx] + psd[max_idx-1] + psd[max_idx + 1])

    # assuming f[0] is 0, f[1] should be our frequency spacing
    assert f[0] == 0
    true_peak = f[max_idx] + C*f[1]
    return true_peak

def _adaptive_notch_Q(f0, fs, nperseg, mainlobe_bins=8, safety=1.25, use_filtfilt=False):
    """
    Choose Q so notch bandwidth >= window mainlobe (~8 bins for Blackman-Harris).
    mainlobe width (Hz) ≈ mainlobe_bins * fs / nperseg.
    Q = f0 / BW. Reduce Q further if filtfilt is used (since magnitude squared narrows BW).
    """

    win = spsig.windows.blackmanharris(nperseg)
    win_spect = np.fft.rfft(win)
    lobe_width = (argmax(np.diff(np.abs(win_spect))) - 1) * 2 + 1

    bw_mainlobe_hz = lobe_width * fs / nperseg
    Q_target = (f0 / (bw_mainlobe_hz * safety))

    if Q_target < 1.2 or Q_target > 3.0:
        print(f"Warning: Calculated Q {Q_target:.2f} out of AES17 range")
        # Q_target = min(3.0, max(1.2, Q_target))

    if use_filtfilt:
        Q_target *= 0.85  # compensate for filtfilt narrowing

    return Q_target


def thdn_new(signal, fs,x_freq=None):
    """
    New THD+N calculation method
    """

    nperseg = 1024*8

    if len(signal) < 8000:
        raise ValueError("Signal too short for THD+N calculation")

    # do a PSD and find the fundamental frequency
    freqs, psd = spsig.welch(signal, fs, nperseg=nperseg, window='blackmanharris', noverlap=0, scaling='density', detrend=False)
    if x_freq is None:
        x_freq = peak_locator(freqs, psd)

    Q = _adaptive_notch_Q(x_freq, fs, nperseg=nperseg, mainlobe_bins=8, safety=1.25, use_filtfilt=True)
    notch_b, notch_a = spsig.iirnotch(x_freq, Q=Q, fs=fs)
    filtered_signal = spsig.lfilter(notch_b, notch_a, signal)
    # freqs, psd2 = spsig.welch(filtered_signal[6500:], fs, nperseg=nperseg, window='blackmanharris', noverlap=0, scaling='density', detrend=False)
    # freqs, psd = spsig.welch(signal[6500:], fs, nperseg=nperseg, window='blackmanharris', noverlap=0, scaling='density', detrend=False)

    # thdn = (np.sqrt(np.sum(psd2)/np.sum(psd)))

    # win = spsig.windows.hann(len(filtered_signal))
    # thdn = (np.sum(np.abs(filtered_signal*win))) / (np.sum(np.abs(signal*win)))
    thdn = sqrt(np.mean((filtered_signal[6500:])**2)) / sqrt(np.mean((signal[6500:])**2))

    result = "new THD+N: %.4f%% or %.1f dB" % (thdn * 100, 20 * log10(thdn))
    print(result)

    # thdn = sqrt(np.sum((filtered_signal)**2)) / sqrt(np.sum(signal**2))
    # import matplotlib.pyplot as plt
    # plt.plot(freqs, 10 * np.log10(psd))
    # plt.plot(freqs, 10 * np.log10(psd2))
    # plt.show()

    return 20*log10(thdn)



def THDN_and_freq(signal, sample_rate):
    """
    Measure the THD+N for a signal and print the results

    Prints the estimated fundamental frequency and the measured THD+N.  This is
    calculated from the ratio of the entire signal before and after
    notch-filtering.

    Currently this tries to find the "skirt" around the fundamental and notch
    out the entire thing.  A fixed-width filter would probably be just as good,
    if not better.
    """
    # Get rid of DC and window the signal
    signal -= mean(signal) # TODO: Do this in the frequency domain, and take any skirts with it?
    windowed = signal * blackmanharris(len(signal))  # TODO Kaiser?

    # Measure the total signal before filtering but after windowing
    total_rms = rms_flat(windowed, sample_rate)

    # Find the peak of the frequency spectrum (fundamental frequency), and
    # filter the signal by throwing away values between the nearest local
    # minima
    f = rfft(windowed)
    i = argmax(abs(f))
    freq = (sample_rate * (i / len(windowed)))  # Not exact
    # print('Frequency: %f Hz' % freq) 
    lowermin, uppermin = find_range(abs(f), i)
    f[lowermin: uppermin] = 0

    # Transform noise back into the signal domain and measure it
    # TODO: Could probably calculate the RMS directly in the frequency domain instead
    noise = irfft(f)
    THDN = rms_flat(noise, sample_rate) / total_rms

    result = "THD+N:     %.4f%% or %.1f dB" % (THDN * 100, 20 * log10(THDN))
    print(result)

    return 20 * log10(THDN) , freq


def THDN(signal, sample_rate):
    THDN, freq = THDN_and_freq(signal, sample_rate)
    return THDN


def load(filename):
    """
    Load a wave file and return the signal, sample rate and number of channels.

    Can be any format that libsndfile supports, like .wav, .flac, etc.
    """
    if use_soundfile:
        wave_file = sf.SoundFile(filename)
        signal = wave_file.read()
    else:
        wave_file = Sndfile(filename, 'r')
        signal = wave_file.read_frames(wave_file.nframes)

    channels = wave_file.channels
    sample_rate = wave_file.samplerate

    return signal, sample_rate, channels


def analyze_channels(filename, function):
    """
    Given a filename, run the given analyzer function on each channel of the
    file
    """
    signal, sample_rate, channels = load(filename)
    print('Analyzing "' + filename + '" SR: ' + str(sample_rate) + 'Hz...')
    result = None

    if channels == 2:
        # Stereo
        if np.array_equal(signal[:, 0], signal[:, 1]):
            print('-- Left and Right channels are identical --')
            print(function(signal[:, 0], sample_rate))
        else:
            print('-- Left channel --')
            print(function(signal[:, 0], sample_rate))
            print('-- Right channel --')
            print(function(signal[:, 1], sample_rate))
    else:
        # Multi-channel
        for ch_no, channel in enumerate(signal.transpose()):
            print('-- Channel %d --' % (ch_no + 1))
            print(function(channel, sample_rate))

    if(result):
        return result

if __name__ == "__main__":
    if len(sys.argv) == 2:
        input_file_name = sys.argv[1]
    else:
        print(f"Usage: {sys.argv[0]} <wavfile>")
        sys.exit(-1)
    analyze_channels(input_file_name, THDN_and_freq)
    sys.exit(0)
