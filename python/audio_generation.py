import os
import os.path
import scipy.signal
import scipy.io.wavfile
import numpy as np

DEFAULT_SAMPLE_RATE = 16000
SYSTEM_DELAY_SAMPLES = 40


def reverb_filter(duration_ms, amplitude, delay_ms,
                         sample_rate=DEFAULT_SAMPLE_RATE):
    """ Generates the impulse response for a reverberation.
    The amplitude parameter should be < 1. Larger amplitude = longer reverb.
    Duration is in milliseconds."""
    delay = int(sample_rate * delay_ms / 1000)
    signal = np.zeros((sample_rate * duration_ms / 1000, ))
    signal[SYSTEM_DELAY_SAMPLES] = 1
    for i in range(SYSTEM_DELAY_SAMPLES, sample_rate*duration_ms / 1000, delay):
        delay_i = i + delay
        if delay_i >= sample_rate * duration_ms / 1000:
            break
        signal[delay_i] = signal[i] * amplitude
    return signal


def echo_filter(duration_ms, amplitude, delay_ms,
                sample_rate=DEFAULT_SAMPLE_RATE):
    """ Generates an echo impulse response.
    Duration is in milliseconds."""
    delay = int(sample_rate * delay_ms / 1000)
    signal = np.zeros((sample_rate * duration_ms / 1000, ))
    signal[SYSTEM_DELAY_SAMPLES] = 1
    signal[delay] = amplitude
    return signal


def get_noise(duration=None, samples=None, db=0,
              sample_rate=DEFAULT_SAMPLE_RATE):
    """ Generates white noise, useful for generating background noise.
    Set dB to a large negative value (e.g. -150) to generate background
    noise.
    Either specify a duration in seconds, or number of samples."""
    if duration:
        samples = duration*sample_rate
    x = np.random.normal(size=(samples,))
    factor = np.power(10, db / 20.0)
    y = x * factor
    return y


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
    elif h_type == 'random':
        h = np.random.normal(size=(200,))
    else:
        raise Exception("h_type invalid")

    if normalise:
        h = h / np.sum(np.abs(h))
    return h
    raise Exception("H type '%s' not valid" % h_type)


def get_sine(duration, frequencies, sample_rate=DEFAULT_SAMPLE_RATE, rshift=0):
    """ Generates a signal containing one or more sine waves of constant
    frequency.
    Duration is in seconds.
    Frequencies is a list of frequencies. """
    x = np.linspace(0, duration * 2 * np.pi, duration * sample_rate)
    signal = np.zeros((duration * sample_rate,))
    for freq in frequencies:
        signal += np.sin(freq * x)
    return signal / (1<<rshift)


def get_near_end(duration, frequencies=[700], sample_rate=DEFAULT_SAMPLE_RATE,
                 rshift=4):
    """ Gets a near-end signal (alias for get_sine)
    Duration is in seconds."""
    return get_sine(duration, frequencies, sample_rate, rshift)


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
    f = np.sin(x/period)*(freq_b-freq_a)/2 + (freq_a+freq_b)/2
    y = np.cumsum(f) / sample_rate * 2 * np.pi
    z = np.sin(y)
    signal = z
    return signal / (1<<rshift)


def get_ref(duration, ref='continuous', sample_rate=DEFAULT_SAMPLE_RATE):
    """ Generates a reference signal
    Duration is in seconds."""
    if ref == "continuous":
        return get_ref_continuous(duration, sample_rate=sample_rate)
    if ref == "discrete":
        return get_ref_discrete(duration, sample_rate=sample_rate)
    if ref == "single":
        return get_sine(duration, frequencies=[1000], sample_rate=sample_rate)
    if ref == "noise":
        return get_noise(duration, sample_rate=sample_rate, db=0)


def get_headroom_divisor(data, headroom):
    """ Get the divisor that gives a number of bits of headroom.

    i.e.
    b = b / get_headroom_divisor(b, 2)
    will give b exactly 2 bits of headroom """
    divisor = (np.abs(data).max() * (1<<headroom))
    return divisor


def write_data(data, filename, sample_rate=DEFAULT_SAMPLE_RATE, dtype=np.int16, 
               rshift=0):
    """ Writes array data in the range [-1, 1] to a wav file of arbitrary
    data type."""
    output = np.asarray(data*np.iinfo(np.int16).max, dtype=dtype) >> rshift
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
                dtype=np.int16, adjust_headroom=True):
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

