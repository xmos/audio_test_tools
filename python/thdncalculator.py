# Copyright (c) 2019-2020, XMOS Ltd, All rights reserved
import sys, os
from scipy.signal import blackmanharris
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
    # print(result)

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
