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
import warnings

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


def get_notch_Q(f0, fs, nperseg, safety=1.25):
    """
    Choose Q so notch bandwidth >= window mainlobe (~8 bins for Blackman-Harris).
    mainlobe width (Hz) ≈ mainlobe_bins * fs / nperseg.
    Q = f0 / BW.
    """

    win = spsig.windows.blackmanharris(nperseg)
    win_spect = np.fft.rfft(win)
    lobe_width = (argmax(np.diff(np.abs(win_spect))) - 1) * 2 + 1

    bw_mainlobe_hz = lobe_width * fs / nperseg
    Q_target = (f0 / (bw_mainlobe_hz * safety))

    # limit upper Q to AES17 recommended range
    Q_target = min(3.0, Q_target)

    if Q_target < 1.2 or Q_target > 3.0:
        warnings.warn(f"Desired Q {Q_target:.2f} for THD+N notch out of AES17 range ({f0} Hz, {fs} Hz sample rate)")

    return Q_target


def AES_THDN_and_freq(signal, sample_rate, fund_freq=None):
    """
    THD+N calculation method after AES17, using a time domain notch filter. It is highly
    recommended to provide the fundamental frequency as fund_freq for accurate notching.

    Note the low pass filter specified in AES17 is not implemented here.
    """

    nperseg = 1024*8 * max(1, sample_rate//48000)

    if len(signal) < 8000:
        raise ValueError("Signal too short for THD+N calculation")

    # do a PSD and find the fundamental frequency
    freqs, psd = spsig.welch(signal, sample_rate, nperseg=nperseg, window='blackmanharris', noverlap=nperseg*0.5, scaling='density', detrend=False)
    if fund_freq is None:
        fund_freq = peak_locator(freqs, psd)
    else:
        max_idx = argmax(psd)
        # check provided fund_freq is close to peak
        if abs(freqs[max_idx] - fund_freq) > (sample_rate / nperseg):
            raise ValueError(f"Provided fundamental frequency {fund_freq} Hz differs from peak frequency {freqs[max_idx]} Hz by more than one bin ({sample_rate / nperseg} Hz)")

    # calculate required notch Q and filter the signal
    Q = get_notch_Q(fund_freq, sample_rate, nperseg=nperseg)
    notch_b, notch_a = spsig.iirnotch(fund_freq, Q=Q, fs=sample_rate)
    filtered_signal = spsig.lfilter(notch_b, notch_a, signal)

    # avoid the notch transient by ignoring the start of the signal
    thdn = sqrt(np.mean((filtered_signal[6500:])**2)) / sqrt(np.mean((signal[6500:])**2))

    result = "new THD+N: %.4f%% or %.1f dB" % (thdn * 100, 20 * log10(thdn))
    # print(result)

    return 20*log10(thdn), fund_freq

def thdn_new(signal, sample_rate, fund_freq=None):
    thdn, freq = AES_THDN_and_freq(signal, sample_rate, fund_freq=fund_freq)
    return thdn

def old_THDN_and_freq(signal, sample_rate):
    """
    Measure the THD+N for a signal and print the results. This uses
    frequency domain methods which are less accurate than time-domain,
    but can be used for short signals.

    Prints the estimated fundamental frequency and the measured THD+N. 
    This is calculated from the ratio of the entire signal before and after
    notch-filtering in the frequency domain.

    Currently this tries to find the "skirt" around the fundamental and notch
    out the entire thing.  However, depending on the signal length, windowing
    and expected THD, this can be very inaccurate for low THD signals
    (>100dB error).
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
    # print(result)

    return 20 * log10(THDN) , freq


def THDN(signal, sample_rate, fund_freq=None):
    THDN, _ = THDN_and_freq(signal, sample_rate, fund_freq=fund_freq)
    return THDN


def THDN_and_freq(signal, sample_rate, fund_freq=None):
    if len(signal) < 8000:
        warnings.warn("Signal too short for AES THD+N calculation, using old method")
        THDN, freq = old_THDN_and_freq(signal, sample_rate)
    else:
        THDN, freq = AES_THDN_and_freq(signal, sample_rate, fund_freq=fund_freq)
    return THDN, freq


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
