import os
import os.path
import scipy.signal
import scipy.io.wavfile
import numpy as np

DEFAULT_SAMPLE_RATE=16000

def decaying_echo_filter(length_ms, amplitude, delay_ms,
                         sample_rate=DEFAULT_SAMPLE_RATE):
    delay = int(sample_rate * delay_ms / 1000)
    signal = np.zeros((sample_rate * length_ms / 1000, ))
    signal[40] = 1
    for i in range(40, sample_rate * length_ms / 1000, delay):
        delay_i = i + delay
        if delay_i >= sample_rate * length_ms / 1000:
            break
        signal[delay_i] = signal[i] * amplitude
    return signal


def echo_filter(length_ms, amplitude, delay_ms,
                sample_rate=DEFAULT_SAMPLE_RATE):
    delay = int(sample_rate * delay_ms / 1000)
    signal = np.zeros((sample_rate * length_ms / 1000, ))
    signal[40] = 1
    signal[delay] = amplitude
    return signal


def get_silence(length=None, samples=None, db=-150,
            sample_rate=DEFAULT_SAMPLE_RATE):
    if length:
        samples = length*sample_rate
    x = np.random.normal(size=(samples,))
    factor = np.power(10, db / 20.0)
    y = x * factor
    return y


def get_h(h_type, normalise=True):
    if h_type == 'short':
        h = echo_filter(200, 0.7, 40)
    if h_type == 'long':
        h = echo_filter(200, 0.7, 170)
    if h_type == 'excessive':
        h = echo_filter(200, 0.7, 190)
    if h_type == 'decaying':
        h = decaying_echo_filter(500, -0.9, 12)
    if normalise:
        h = h / np.sum(np.abs(h))
    return h
    raise Exception("H type '%s' not valid" % h_type)


def get_sine(length, frequencies, sample_rate=DEFAULT_SAMPLE_RATE, rshift=0):
    x = np.linspace(0, length * 2 * np.pi, length * sample_rate)
    signal = np.zeros((length * sample_rate,))
    for freq in frequencies:
        signal += np.sin(freq * x)
    return signal / (1<<rshift)


def get_near_end(length, frequencies=[700], sample_rate=DEFAULT_SAMPLE_RATE,
                 rshift=4):
    return get_sine(length, frequencies, sample_rate, rshift)


def get_ref_discrete(length, freq_a=1000, freq_b=2000, period=1,
                     sample_rate=DEFAULT_SAMPLE_RATE, rshift=0):
    x = np.linspace(0, length * 2 * np.pi, length * sample_rate)
    y_1 = np.sin(freq_a * x)
    y_2 = np.sin(freq_b * x)
    signal = np.sin(x / (period*2))**2 * y_1 + np.cos(x / (period*2))**2 * y_2
    return signal / (1<<rshift)


def get_ref_continuous(length, freq_a=500, freq_b=4000, period=0.2,
                       sample_rate=DEFAULT_SAMPLE_RATE, rshift=0):
    x = np.linspace(0, length * 2 * np.pi, length * sample_rate)
    f = np.sin(x/period)*(freq_b-freq_a)/2 + (freq_a+freq_b)/2
    y = np.cumsum(f) / sample_rate * 2 * np.pi
    z = np.sin(y)
    signal = z
    return signal / (1<<rshift)


def get_ref(length, ref='continuous', sample_rate=DEFAULT_SAMPLE_RATE):
    if ref == "continuous":
        return get_ref_continuous(length, sample_rate=sample_rate)
    if ref == "discrete":
        return get_ref_discrete(length, sample_rate=sample_rate)
    if ref == "single":
        return get_sine(length, frequencies=[1000], sample_rate=sample_rate)
    if ref == "noise":
        return np.random.normal(size=(length*sample_rate))


def get_headroom_divisor(data, headroom):
    divisor = (np.abs(data).max() * (1<<headroom))
    return divisor


def write_data(data, filename, sample_rate=DEFAULT_SAMPLE_RATE, dtype=np.int16, 
               rshift=0):
    output = np.asarray(data*np.iinfo(np.int16).max, dtype=dtype) >> rshift
    scipy.io.wavfile.write(filename, sample_rate, output.T)


def write_audio(test_class, echo_type, ref_type, headroom, AudioIn, AudioRef,
                sample_rate=DEFAULT_SAMPLE_RATE, audio_dir='spec_audio',
                dtype=np.int16):
    filename = '%s-%s-%s-hr%d-%s' % (test_class, echo_type, ref_type, headroom, "%s")
    try:
        os.makedirs(audio_dir)
    except os.error:
        pass
    divisor = get_headroom_divisor(AudioIn, headroom)
    AudioIn = AudioIn / divisor
    AudioRef = AudioRef / divisor
    write_data(AudioIn, os.path.join(audio_dir, filename % "AudioIn.wav"),
               sample_rate, dtype)
    write_data(AudioRef, os.path.join(audio_dir, filename % "AudioRef.wav"),
               sample_rate, dtype)

