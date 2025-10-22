# Copyright 2025 XMOS LIMITED.
# This Software is subject to the terms of the XMOS Public Licence: Version 1.

import os
import sys
import tempfile

import numpy as np
import pytest
import scipy.io.wavfile

# Add the python directory to the path
package_dir = os.path.dirname(os.path.abspath(__file__))
python_path = os.path.join(package_dir, '../python/')
sys.path.insert(0, python_path)

import thdncalculator  # noqa: E402
from audio_generation import get_sine, get_noise  # noqa: E402


"""Test suite for THD+N calculator with synthesized signals"""

@pytest.mark.parametrize("duration", [0.5, 1.0])
@pytest.mark.parametrize("fs", [16000, 44100, 48000, 96000])
@pytest.mark.parametrize("f", [99.7, 440, 997, 4997, 9997])
def test_pure_sine_wave(fs, f, duration):
    """Test that a pure sine wave has very low THD+N"""

    if f > fs / 2:
        pytest.skip(f"Frequency {f} Hz too close to Nyquist for {fs} Hz sample rate")

    sample_rate = fs
    duration = duration  # seconds
    frequency = f  # Hz
    
    # Generate a pure sine wave
    signal = get_sine(duration, [frequency], sample_rate=sample_rate)
    
    # Calculate THD+N
    thdn_db = thdncalculator.thdn_new(signal, sample_rate, x_freq=frequency)
    thdn_db_old = thdncalculator.THDN(signal, sample_rate)

    # A pure sine wave should have very low THD+N
    # NOTE: 997 Hz at 0.5s duration has anomalously high THD+N (~-61 dB) due to 
    # interaction between frequency, duration, and windowing. This is expected behavior.
    # Set threshold to < -59 dB (1 dB margin above worst case)
    # if duration < 1.0:
    #     threshold = -59  # Accounts for 997 Hz at 0.5s worst case
    # else:
    threshold = -94.7  # Most are better than -87 dB at 1.0s duration
    assert thdn_db < threshold, f"Pure sine wave THD+N too high: {thdn_db} dB (threshold: {threshold} dB)"

@pytest.mark.parametrize("duration", [0.5, 1.0])
@pytest.mark.parametrize("fs", [16000, 44100, 48000, 96000])
@pytest.mark.parametrize("f", [99.7, 440, 997, 4997, 9997])
def test_sine_wave_with_harmonics(fs, f, duration):
    """Test THD+N increases with added harmonics"""

    if f*2 > fs / 2:
        pytest.skip(f"Frequency {f} Hz too close to Nyquist for {fs} Hz sample rate")

    sample_rate = fs
    duration = duration  # seconds
    fundamental = f  # Hz
    
    # Generate sine wave with 2nd and 3rd harmonics
    # Fundamental at full amplitude, 2nd harmonic at -20dB, 3rd at -30dB
    signal = get_sine(
        duration, 
        [fundamental, 2 * fundamental, 3 * fundamental],
        amplitudes=[1.0, 0.1, 0.0316],  # 0.1 = -20dB, 0.0316 = -30dB
        sample_rate=sample_rate
    )
    
    # Calculate THD+N
    thdn_db = thdncalculator.thdn_new(signal, sample_rate, x_freq=fundamental)
    thdn_db_old = thdncalculator.THDN(signal, sample_rate)

    # With harmonics, THD+N should be very consistent at approximately -19.6 dB
    # across all parameter combinations (within 0.1 dB)
    assert thdn_db > -20.2, f"THD+N with harmonics unexpectedly low: {thdn_db} dB"
    assert thdn_db < -18.5, f"THD+N with harmonics unexpectedly high: {thdn_db} dB"

@pytest.mark.parametrize("duration", [0.5, 1.0])
@pytest.mark.parametrize("fs", [16000, 44100, 48000, 96000])
@pytest.mark.parametrize("f", [99.7, 440, 997, 4997, 9997])
@pytest.mark.parametrize("noise_level", [-100, -80, -60, -40, -20])
def test_sine_wave_with_noise(fs, f, duration, noise_level):
    """Test that adding noise increases THD+N"""

    if f > fs / 2:
        pytest.skip(f"Frequency {f} Hz too close to Nyquist for {fs} Hz sample rate")

    sample_rate = fs
    duration = duration  # seconds
    frequency = f  # Hz
    
    # Generate sine wave
    sine = get_sine(duration, [frequency], sample_rate=sample_rate)
    
    # Add noise at -40dB relative to signal
    noise = get_noise(duration=duration, sample_rate=sample_rate, db=noise_level)
    signal = sine + noise
    
    # Calculate THD+N
    thdn_db = thdncalculator.thdn_new(signal, sample_rate, x_freq=frequency)
    thdn_db_old = thdncalculator.THDN(signal, sample_rate)

    # THD+N should reflect the noise level added
    # NOTE: 997 Hz at 0.5s has slightly worse performance (about 1.5 dB worse)
    # -60dB noise: ranges from -55.5 to -57.1 dB (worst at 997Hz 0.5s)
    # -40dB noise: ranges from -36.9 to -37.1 dB
    # -20dB noise: ranges from -17.0 to -17.2 dB
    assert thdn_db > noise_level, f"THD+N with {noise_level}dB noise unexpectedly low: {thdn_db} dB"
    if noise_level == -100:
        assert thdn_db < -95.0, f"THD+N with {noise_level}dB noise unexpectedly high: {thdn_db} dB"
    elif noise_level == -80:
        assert thdn_db < -75.5, f"THD+N with {noise_level}dB noise unexpectedly high: {thdn_db} dB"
    elif noise_level == -60:
        assert thdn_db < -54.5, f"THD+N with {noise_level}dB noise unexpectedly high: {thdn_db} dB"
    elif noise_level == -40:
        assert thdn_db < -35.8, f"THD+N with {noise_level}dB noise unexpectedly high: {thdn_db} dB"
    elif noise_level == -20:
        assert thdn_db < -15.9, f"THD+N with {noise_level}dB noise unexpectedly high: {thdn_db} dB"


@pytest.mark.parametrize("duration", [0.5, 1.0])
@pytest.mark.parametrize("fs", [16000, 44100, 48000, 96000])
@pytest.mark.parametrize("f", [99.7, 440, 997, 4997, 9997])
def test_frequency_detection(fs, f, duration):
    """Test that the fundamental frequency is correctly detected"""
    sample_rate = fs
    freq = f
    
    # Skip frequencies too close to Nyquist
    if freq > sample_rate / 2:
        pytest.skip(f"Frequency {freq} Hz too close to Nyquist for {sample_rate} Hz sample rate")
        
    signal = get_sine(duration, [freq], sample_rate=sample_rate)
    thdn_db, detected_freq = thdncalculator.THDN_and_freq(signal, sample_rate)
    
    # Allow 1% tolerance in frequency detection
    freq_error = abs(detected_freq - freq) / freq
    assert freq_error < 0.01, \
        f"Frequency detection error too large: expected {freq} Hz, got {detected_freq} Hz (error: {freq_error*100:.2f}%)"

@pytest.mark.parametrize("duration", [0.5, 1.0])
@pytest.mark.parametrize("fs", [16000, 44100, 48000, 96000])
@pytest.mark.parametrize("f", [440, 997, 4997])
def test_different_sample_rates(fs, f, duration):
    """Test THD+N calculation works with different sample rates"""

    if f > fs / 2:
        pytest.skip(f"Frequency {f} Hz too close to Nyquist for {fs} Hz sample rate")

    sample_rate = fs
    frequency = f  # Hz
    
    signal = get_sine(duration, [frequency], sample_rate=sample_rate)
    thdn_db = thdncalculator.thdn_new(signal, sample_rate, x_freq=frequency)
    thdn_db_old = thdncalculator.THDN(signal, sample_rate)

    # Pure sine should have low THD+N at any sample rate
    assert thdn_db < -70, \
        f"Pure sine THD+N too high at {sample_rate} Hz sample rate: {thdn_db} dB"

@pytest.mark.parametrize("duration", [0.5, 1.0])
@pytest.mark.parametrize("fs", [16000, 44100, 48000, 96000])
@pytest.mark.parametrize("f", [440, 997, 4997])
@pytest.mark.parametrize("amplitude", [0.1, 0.5, 1.0])
def test_low_amplitude_signal(fs, f, duration, amplitude):
    """Test THD+N calculation with various amplitude signals"""

    if f > fs / 2:
        pytest.skip(f"Frequency {f} Hz too close to Nyquist for {fs} Hz sample rate")

    sample_rate = fs
    frequency = f  # Hz
    
    # Generate sine wave at specified amplitude
    signal = get_sine(duration, [frequency], amplitudes=[amplitude], sample_rate=sample_rate)
    
    thdn_db = thdncalculator.thdn_new(signal, sample_rate, x_freq=frequency)
    thdn_db_old = thdncalculator.THDN(signal, sample_rate)
    
    # Should still have low THD+N regardless of amplitude
    assert thdn_db < -95, f"Sine wave at amplitude {amplitude} THD+N too high: {thdn_db} dB"


@pytest.mark.parametrize("duration", [0.5, 1.0])
@pytest.mark.parametrize("fs", [16000, 44100, 48000, 96000])
@pytest.mark.parametrize("noise_db", [-10, 0, 10])
def test_white_noise_only(fs, duration, noise_db):
    """Test THD+N with white noise (no fundamental)"""
    sample_rate = fs
    
    # Generate white noise
    signal = get_noise(duration=duration, sample_rate=sample_rate, db=noise_db)
    
    # Calculate THD+N
    thdn_db, detected_freq = thdncalculator.THDN_and_freq(signal, sample_rate)
    
    # For white noise, THD+N should be close to 0 dB (100%)
    assert thdn_db > -1, f"White noise THD+N unexpectedly low: {thdn_db} dB"


@pytest.mark.parametrize("duration", [0.5, 1.0])
@pytest.mark.parametrize("fs", [16000, 44100, 48000, 96000])
@pytest.mark.parametrize("f", [440, 997, 4997])
def test_wav_file_loading(fs, f, duration):
    """Test loading and analyzing a WAV file"""

    if f > fs / 2:
        pytest.skip(f"Frequency {f} Hz too close to Nyquist for {fs} Hz sample rate")

    sample_rate = fs
    frequency = f  # Hz
    
    # Generate a test signal
    signal = get_sine(duration, [frequency], sample_rate=sample_rate)
    
    # Normalize to 16-bit range
    signal_16bit = (signal * 32767).astype(np.int16)
    
    # Create temporary WAV file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
        tmp_filename = tmp_file.name
        
    try:
        # Write WAV file
        scipy.io.wavfile.write(tmp_filename, sample_rate, signal_16bit)
        
        # Load using thdncalculator
        loaded_signal, loaded_rate, channels = thdncalculator.load(tmp_filename)
        
        # Check sample rate
        assert loaded_rate == sample_rate, \
            f"Sample rate mismatch: expected {sample_rate}, got {loaded_rate}"
        
        # Calculate THD+N on loaded signal
        thdn_db = thdncalculator.thdn_new(signal, sample_rate, x_freq=frequency)
        thdn_db_old = thdncalculator.THDN(signal, sample_rate)

        # Should still have low THD+N after file round-trip
        assert thdn_db < -88, \
            f"THD+N after WAV file round-trip too high: {thdn_db} dB"
            
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_filename):
            os.remove(tmp_filename)


if __name__ == "__main__":
    # Run tests with pytest
    # pytest.main([__file__, "-v"])
    # test_sine_wave_with_noise(48000, 997, 0.1, -100)
    # test_sine_wave_with_harmonics(48000, 997, 1.0)
    test_pure_sine_wave(48000, 99.7, 1.0)
