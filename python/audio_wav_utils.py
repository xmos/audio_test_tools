# Copyright (c) 2018-2019, XMOS Ltd, All rights reserved
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from builtins import str
from builtins import range
import numpy as np
import scipy.io.wavfile
import pandas

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
        mid = ((max_val - min_val) // 2) + 1
        wav_data = (wav_data.astype(dtype=np.float64) - mid)/float(max_val-mid)
    elif data_type == np.float32:
        wav_data = wav_data.astype(dtype=np.float64)
    elif  data_type == np.float64:
        pass
    else:
        print ("Error: unknown data type for parse_audio() " + str(data_type))

    return wav_data, channel_count, file_length



def convert_to_32_bit(wav_data):
    if wav_data.dtype == np.int32:
        return wav_data
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


def get_erle(in_filename, out_filename, step_size, ch_number):
    in_rate, in_wav_file = scipy.io.wavfile.read(in_filename)
    out_rate, out_wav_file = scipy.io.wavfile.read(out_filename)

    in_wav_data, in_channel_count, in_file_length = parse_audio(in_wav_file)
    out_wav_data, out_channel_count, out_file_length = parse_audio(out_wav_file)

    in_data_trimmed = np.trim_zeros(in_wav_data[ch_number,:], trim='f')
    out_data_trimmed = np.trim_zeros(out_wav_data[ch_number,:], trim='f')

    sample_count = min(len(in_data_trimmed), len(out_data_trimmed))
    erle = []
    for index in range(0, sample_count-step_size, step_size):
        # Calculate EWM of audio power in 1s window
        in_power = np.power(in_data_trimmed[index:index+step_size], 2)
        out_power = np.power(out_data_trimmed[index:index+step_size], 2)
        in_power_ewm = pandas.Series(in_power).ewm(span=step_size).mean()
        out_power_ewm = pandas.Series(out_power).ewm(span=step_size).mean()

        # Get sum of average power
        in_power_sum = 0
        out_power_sum = 0
        for i in range(len(out_power_ewm)):
            in_power_sum += in_power_ewm[i]
            out_power_sum += out_power_ewm[i]
        next_erle = 10 * np.log10(in_power_sum/out_power_sum) if out_power_sum != 0 else 1000000
        erle.append(next_erle)

    return erle
