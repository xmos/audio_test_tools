
# -*- coding: utf-8 -*-
# Copyright (c) 2018-2019, XMOS Ltd, All rights reserved
"""
@author: Andrew
"""
import numpy as np
import scipy.io.wavfile
import matplotlib.pyplot as plt
import pandas

speed_of_sound = 342.0

mic_d    = 0.043

circular_mic_array = np.asarray(
        [  [0.0,     0.0,                0.0], 
        [mic_d/2.0,   np.sin(np.pi/3)*mic_d,  0.0], 
        [mic_d,       0.0,                0.0], 
        [mic_d/2.0,  -np.sin(np.pi/3)*mic_d,  0.0], 
        [-mic_d/2.0,  -np.sin(np.pi/3)*mic_d, 0.0], 
        [-mic_d,       0.0,                0.0], 
        [-mic_d/2.0,   np.sin(np.pi/3)*mic_d,  0.0]]
    )

def distance_between_points(a, b):
    return np.sqrt(sum((a-b)**2))

def translate_position(p, x, y, z):
    p_t = p + np.asarray([x, y, z])
    return p_t

def rotate_around_x_axis(p, theta):
    R = np.asarray([[1., 0., 0.],[0., np.cos(theta), -np.sin(theta)],[0., np.sin(theta), np.cos(theta)]])
    p_t = np.dot(p, R)
    return p_t

def rotate_around_y_axis(p, theta):
    R = np.asarray([[np.cos(theta), 0., np.sin(theta)],[0., 1., 0.],[-np.sin(theta), 0., np.cos(theta)]])
    p_t = np.dot(p, R)
    return p_t

def rotate_around_z_axis(p, theta):
    R = np.asarray([[np.cos(theta), -np.sin(theta), 0.],[np.sin(theta), np.cos(theta), 0.],[0., 0., 1.,]])
    p_t = np.dot(p, R)
    return p_t

def print_phi(phi):
    for i in range(len(phi)):
        for j in range(len(phi[i])):
            print('% .4f '%phi[i][j]),
        print ('')
    print ('')
    print ('')
    return

def make_mvdr_matrices(f_bin_count, fft_length, channel_count, rate):
    W = np.zeros((f_bin_count, channel_count, channel_count))
    mu = 0.0000001
    for f_bin in range(f_bin_count):
        freq = 2.0*np.pi*float(f_bin) / float(fft_length)  * float(rate)
        for i in range(channel_count):
            for j in range(channel_count):
                v = np.sinc(freq*d(i, j)/speed_of_sound)
                if i==j:
                    v += mu
                W[f_bin][i][j] = v
        W[f_bin] = np.linalg.pinv(W[f_bin])
    return W

def get_channel_count(wav_file):
    s = np.shape(wav_file)
    if len(s) == 1:
        channel_count = 1
    else:
        channel_count = len(wav_file[0])
    return channel_count
    
# This converts a wav file opened with scipy.io.wavfile
def parse_audio(wav_file):
    channel_count = get_channel_count(wav_file)
    file_length = len(wav_file)

    if len(wav_file.shape ) == 1:
       wav_file = np.reshape(wav_file, (file_length, 1))

    wav_data = wav_file.T

    # assume at least one sample in at least one channel!
    data_type = type(wav_data[0][0])

    if data_type == np.int16:
        max_val = np.iinfo(np.int16).max
        wav_data = wav_data.astype(dtype=np.float64)/float(max_val)
    elif data_type == np.int8:
        max_val = np.iinfo(np.int8).max
        wav_data = wav_data.astype(dtype=np.float64)/float(max_val)
    elif data_type == np.int32:
        max_val = np.iinfo(np.int32).max
        wav_data = wav_data.astype(dtype=np.float64)/float(max_val)
    elif data_type == np.uint8:
        max_val = np.iinfo(np.uint8).max
        min_val = np.iinfo(np.uint8).min
        mid = (max_val - min_val)/2 + 1
        wav_data = (wav_data.astype(dtype=np.float64) - mid)/float(max_val-mid)
    elif data_type == np.float32:
        wav_data = wav_data.astype(dtype=np.float64)
    elif  data_type == np.float64:
        pass
    else:
        print ("Error: unknown data type for parse_audio() " + str(data_type))

    return wav_data, channel_count, file_length



def convert_to_32_bit(wav_data):
    output_32bit = np.asarray(wav_data*np.iinfo(np.int32).max, dtype=np.int32)
    return  output_32bit

#Return the time domain data extracted 
def get_frame(wav_data, frame_start, data_length, delays = None):
    

    channel_count = len(wav_data)

    if delays is None:
        delays = np.zeros(channel_count, dtype= int)

    start_index = frame_start - np.asarray(delays, dtype= int)
    frame = np.zeros((channel_count, data_length), dtype=np.float64)
    for ch in range(channel_count):
        if start_index[ch] < 0 :
            if start_index[ch] + data_length > 0:
                frame[ch][ -start_index[ch]:] =  wav_data[ch][:start_index[ch] + data_length]
        else:
           frame[ch] = wav_data[ch, start_index[ch]:start_index[ch] + data_length]
    return frame
# Apply a sample delay to a frequency domain frame (can be -ve as well)
def steer_channel(Channel, delay):
    fft_length = ((len(Channel)-1) *2)
    w = np.exp(-2.0j*np.pi*np.arange(len(Channel))/float(fft_length) * float(delay))
    return Channel * w

def output_tdoa_graph(gcc_results, filename, max_spread = 2.0):
    plt.clf()
    plt.cla()
    for c in range(len(gcc_results)):
        plt.plot( gcc_results[c], label='ch ' + str(c))
    plt.ylim(-max_spread, max_spread)
    plt.title('TDOA')
    plt.legend()
    plt.xlabel('frame number')
    plt.ylabel('TDOA (samples)')
    plt.savefig(filename, dpi=100)  
    return

def output_multiple_tdoa_graphs(multiple_gcc_results, filename, max_spread = 2.0):
    plt.clf()
    plt.cla()
    for g in range(len(multiple_gcc_results)):
        plt.subplot(len(multiple_gcc_results), 1, g+1)
        for c in range(len(multiple_gcc_results[g])):
            plt.plot( multiple_gcc_results[g][c], label='ch ' + str(c))
        plt.ylim(-max_spread, max_spread)
        plt.title('TDOA')
        plt.legend()
        plt.xlabel('frame number')
        plt.ylabel('TDOA (samples)')
    plt.savefig(filename, dpi=100)
    return

def get_erle(in_filename, out_filename, step_size, ch_number):
    """Returns the ERLE values of the given output/input wav files

    Args:
        in_filename : input wav file
        out_filename : output wav file
        step_size : length in samples of the EWM span
        ch_number : channel of the wav files to analyse

    Returns:
        list of ERLE for each step_size
    """
    in_rate, in_wav_file = scipy.io.wavfile.read(in_filename)
    out_rate, out_wav_file = scipy.io.wavfile.read(out_filename)

    in_wav_data, in_channel_count, in_file_length = parse_audio(in_wav_file)
    out_wav_data, out_channel_count, out_file_length = parse_audio(out_wav_file)

    in_data_trimmed = np.trim_zeros(in_wav_data[ch_number, :], trim='f')
    out_data_trimmed = np.trim_zeros(out_wav_data[ch_number, :], trim='f')

    sample_count = min(len(in_data_trimmed), len(out_data_trimmed))
    erles = []
    for index in range(0, sample_count-step_size, step_size):
        # Calculate EWM of audio power in 1s window
        in_power = np.power(in_data_trimmed[index:index+step_size], 2)
        out_power = np.power(out_data_trimmed[index:index+step_size], 2)
        in_power_ewm = pandas.Series(in_power).ewm(span=step_size).mean()
        out_power_ewm = pandas.Series(out_power).ewm(span=step_size).mean()

        # Get sum of average power
        in_power_sum = 0
        out_power_sum = 0
        for in_val, out_val in zip(in_power_ewm, out_power_ewm):
            in_power_sum += in_val
            out_power_sum += out_val
        next_erle = 10 * np.log10(in_power_sum/out_power_sum) if out_power_sum != 0 else 1000000
        erles.append(next_erle)
    return erles
