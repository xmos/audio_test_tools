# Copyright (c) 2018-2019, XMOS Ltd, All rights reserved
from __future__ import division
from builtins import str
from builtins import range
import os
import os.path
import scipy.signal
import scipy.io.wavfile
import numpy as np

DEFAULT_SAMPLE_RATE = 16000
SYSTEM_DELAY_SAMPLES = 40


def get_magnitude(freq, X, Fs, tolerance_hz, normalise=False):
    X = np.abs(X)
    i = int(2 * freq * len(X) / Fs)
    tol_i = int(2 * tolerance_hz * len(X) / Fs)
    normalisation_factor = 1
    if normalise:
        normalisation_factor = 1.0 / len(X)
    return np.max(X[i - tol_i:i + tol_i]) * normalisation_factor


def get_suppressed_magnitude(frequencies, X, Fs, tolerance_hz,
                             normalise=False, band_min=0, band_max=None):
    if not band_max:
        band_max = Fs // 2
    X = np.abs(X)
    tol_i = int(2 * tolerance_hz * len(X) / Fs)
    min_i = int(2 * band_min * len(X) / Fs)
    max_i = int(2 * band_max * len(X) / Fs)
    X_nulled = np.array(X)
    X_nulled[:min_i] = 0
    X_nulled[max_i:] = 0
    for freq in frequencies:
        i = int(2 * freq * len(X) / Fs)
        X_nulled[i - tol_i:i + tol_i] = 0
    normalisation_factor = 1
    if normalise:
        normalisation_factor = 1.0 / len(X)
    return np.max(X_nulled) * normalisation_factor,\
           int(np.argmax(X_nulled) / (2.0 * len(X) / Fs))


def db(a, b):
    return 20 * np.log10(float(a)/b)


def reverb_filter(duration_ms, amplitude, delay_ms,
                         sample_rate=DEFAULT_SAMPLE_RATE):
    """ Generates the impulse response for a reverberation.
    The amplitude parameter should be < 1. Larger amplitude = longer reverb.
    Duration is in milliseconds."""
    delay = int(sample_rate * delay_ms / 1000)
    signal = np.zeros((int(sample_rate * duration_ms / 1000), ))
    signal[SYSTEM_DELAY_SAMPLES] = 1
    for i in range(SYSTEM_DELAY_SAMPLES, int(sample_rate*duration_ms / 1000), delay):
        delay_i = i + delay
        if delay_i >= (sample_rate * duration_ms / 1000):
            break
        signal[delay_i] = signal[i] * amplitude
    return signal


def get_rt60(duration_ms, delay_ms=12, sample_rate=DEFAULT_SAMPLE_RATE):
    """Generates an RT60 impulse response using reverb_filter()

    Args:
        duration_ms: length in milliseconds of the RT60

    Returns:
        Impulse response of RT60
    """
    target = 1e-3 # -60dB
    delay = int(sample_rate * delay_ms / 1000)
    total_time = int(sample_rate * duration_ms / 1000) - SYSTEM_DELAY_SAMPLES
    n = total_time / delay
    amplitude = np.power(target, 1.0 / n)
    return reverb_filter(int(1.2 * duration_ms), -amplitude, delay_ms,
                         sample_rate)


def echo_filter(duration_ms, amplitude, delay_ms,
                system_delay_samples=SYSTEM_DELAY_SAMPLES,
                sample_rate=DEFAULT_SAMPLE_RATE):
    """ Generates an echo impulse response.
    Duration is in milliseconds."""
    echo_delay_samples = int(sample_rate * delay_ms / 1000)
    signal = np.zeros((int(sample_rate * duration_ms / 1000), ))
    assert(system_delay_samples+echo_delay_samples < int(duration_ms*sample_rate / 1000))
    signal[system_delay_samples] = 1
    signal[system_delay_samples + echo_delay_samples] = amplitude
    return signal


def get_noise(duration=None, samples=None, db=0,
              sample_rate=DEFAULT_SAMPLE_RATE, seed=None):
    """ Generates white noise, useful for generating background noise.
    Set dB to a large negative value (e.g. -150) to generate background
    noise.
    Either specify a duration in seconds, or number of samples."""
    if duration:
        samples = duration*sample_rate
    if seed is None:
        # Seed using inputs
        seed = (hash(str(samples)) + hash(str(db)) + hash(str(sample_rate))) % 2**32
    np.random.seed(seed)
    x = np.random.normal(size=(samples,))
    factor = np.power(10, db / 20.0)
    y = x * factor
    return y


def get_band_limited_noise(min_freq, max_freq, duration=None, samples=None,
                           sample_rate=16000.0, db=0):
    """ Generates white noise band-limited between the min/max frequencies.
    The noise is normally distributed in the time domain."""
    if duration:
        samples = int(duration * sample_rate)
    # Generate random phase
    max_i = int(samples * max_freq / sample_rate)
    min_i = int(samples * min_freq / sample_rate)
    # Generate band-limited noise
    noise = np.array([])
    if duration:
        noise = get_noise(duration=duration)
    elif samples:
        noise = get_noise(samples=samples)
    else:
        print "Error: must provide duration or samples"
        return noise
    Noise = np.fft.rfft(noise)
    Noise[:min_i] = 0
    Noise[max_i:] = 0
    noise = np.fft.irfft(Noise)
    # Normalise to be within [-1, 1] range
    normalised_noise = noise / np.max(np.abs(noise))
    factor = np.power(10, db / 20.0)
    attenuated_noise = normalised_noise * factor
    return attenuated_noise


def get_h(h_type='short', normalise=True):
    """ Generates a transfer function """
    if h_type == 'short':
        h = echo_filter(200, 0.7, 40)
    elif h_type == 'long':
        h = echo_filter(200, 0.7, 170)
    elif h_type == 'excessive':
        h = echo_filter(200, 0.7, 190)
    elif h_type == 'decaying':
        h = reverb_filter(190, -0.9, 12)
    elif h_type == 'delayed':
        h = echo_filter(250, 0.7, 50, system_delay_samples=40+140*16)
    elif h_type == 'random':
        h = np.random.normal(size=(200,))
    else:
        raise Exception("h_type invalid")

    if normalise:
        h = h / np.sum(np.abs(h))
    return h
    raise Exception("H type '%s' not valid" % h_type)


def get_sine(duration, frequencies, amplitudes=None, phases=None,
        sample_rate=DEFAULT_SAMPLE_RATE, rshift=0):
    """ Generates a signal containing one or more sine waves of constant
    frequency.
    Duration is in seconds.
    Frequencies, amplitudes and phases are lists of values. """

    # Do some checks on the input parameters
    assert (type(frequencies) == list), "Error: frequencies not given as a list"
    assert (len(frequencies) != 0), "Error: empty list of frequencies"
    # Set default values for optional parameters
    if not amplitudes:
        amplitudes = np.ones(len(frequencies))
    if not phases:
        phases = np.zeros(len(frequencies))
    assert (len(frequencies) == len(phases)), \
            "Error: Frequencies and phases have different size"
    assert (len(frequencies) == len(amplitudes)), \
            "Error: Frequencies and phases have different size"

    x = np.linspace(0, duration * 2 * np.pi, int(duration * sample_rate))
    signal = np.zeros((int(duration * sample_rate),))
    for idx in range(len(frequencies)):
        signal += amplitudes[idx] * np.sin(frequencies[idx] * x + phases[idx])
    return signal / (1<<rshift)


def get_near_end(duration, frequencies=[700], sample_rate=DEFAULT_SAMPLE_RATE,
                 rshift=4):
    """ Gets a near-end signal (alias for get_sine)
    Duration is in seconds."""
    return get_sine(duration, frequencies, sample_rate=sample_rate,
                    rshift=rshift)


def get_ref_discrete(duration, freq_a=1000, freq_b=2000, period=1,
                     sample_rate=DEFAULT_SAMPLE_RATE, rshift=0):
    """ Gets a reference signal which oscillates between two frequencies

    The signal produced will have magnitude in the frequency domain at only
    those two frequencies.
    Duration is in seconds."""
    x = np.linspace(0, duration * 2 * np.pi, duration * sample_rate)
    y_1 = np.sin(freq_a * x)
    y_2 = np.sin(freq_b * x)
    signal = np.sin(x / (period*2))**2 * y_1 + np.cos(x / (period*2))**2 * y_2
    return signal / (1<<rshift)


def get_ref_continuous(duration, freq_a=500, freq_b=4000, period=0.2,
                       sample_rate=DEFAULT_SAMPLE_RATE, rshift=0):
    """ Gets a reference signal which oscillates smoothly between two
    frequencies

    The signal produced will have magnitude in the frequency domain at all
    frequencies between the two frequencies.
    Duration is in seconds."""
    # Using a cumulative sum to avoid phase error when changing frequency
    x = np.linspace(0, duration * 2 * np.pi, duration * sample_rate)
    f = (np.sin(x / period)*(freq_b-freq_a) / 2) + ((freq_a+freq_b)/2)
    y = np.cumsum(f) / sample_rate * 2 * np.pi
    z = np.sin(y)
    signal = z
    return signal / (1<<rshift)


def get_ref(duration, ref='continuous', sample_rate=DEFAULT_SAMPLE_RATE):
    """ Generates a reference signal
    Duration is in seconds."""
    if ref == "continuous":
        return get_ref_continuous(duration, sample_rate=sample_rate)
    elif ref == "discrete":
        return get_ref_discrete(duration, sample_rate=sample_rate)
    elif ref == "single":
        return get_sine(duration, frequencies=[1000], sample_rate=sample_rate)
    elif ref == "noise":
        return get_noise(duration, sample_rate=sample_rate, db=0)
    elif ref == "bandlimited":
        return get_band_limited_noise(1000, 4000, duration,
                                      sample_rate=sample_rate)
    else:
        raise Exception("ref name \"{}\" invalid.".format(ref))


def get_headroom_divisor(data, headroom):
    """ Get the divisor that gives a number of bits of headroom.

    i.e.
    b = b / get_headroom_divisor(b, 2)
    will give b exactly 2 bits of headroom """
    divisor = (np.abs(data).max() * (1<<headroom))
    return divisor


def write_data(data, filename, sample_rate=DEFAULT_SAMPLE_RATE, dtype=np.int32,
               rshift=0):
    """ Writes array data in the range [-1, 1] to a wav file of arbitrary
    data type."""
    output = np.asarray(data*np.iinfo(dtype).max, dtype=dtype) >> rshift
    scipy.io.wavfile.write(filename, sample_rate, output.T)


def get_filenames(testname, echo_type, ref_type, headroom):
    """ Generates filenames for AEC wavs (without .wav extension)  """
    filename = '%s-%s-%s-hr%d-%s'\
                % (testname, echo_type, ref_type, headroom, "%s")
    audio_in = filename % "AudioIn"
    audio_ref = filename % "AudioRef"
    audio_out = filename % "Error"
    return audio_in, audio_ref, audio_out


def write_audio(test_class, echo_type, ref_type, headroom, AudioIn, AudioRef,
                sample_rate=DEFAULT_SAMPLE_RATE, audio_dir='spec_audio',
                dtype=np.int32, adjust_headroom=True):
    """ Writes test audio to wav files with a specific naming convention. """
    try:
        os.makedirs(audio_dir)
    except os.error:
        pass
    if adjust_headroom:
        divisor = get_headroom_divisor(AudioIn, headroom)
        AudioIn = AudioIn / divisor
        AudioRef = AudioRef / divisor
    in_filename, ref_filename, _ = get_filenames(test_class, echo_type,
                                                 ref_type, headroom)
    write_data(AudioIn, os.path.join(audio_dir, in_filename + ".wav"),
               sample_rate, dtype)
    write_data(AudioRef, os.path.join(audio_dir, ref_filename + ".wav"),
               sample_rate, dtype)
