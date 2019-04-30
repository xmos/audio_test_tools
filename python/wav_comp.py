# Copyright (c) 2018-2019, XMOS Ltd, All rights reserved
from __future__ import division
from builtins import str
from builtins import range
from past.utils import old_div
import numpy as np
import scipy.io.wavfile
import matplotlib.pyplot as plt
import audio_utils as au
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("a", help="a wav file")
    parser.add_argument("b", help="b wav file")
    parser.parse_args()
    args = parser.parse_args()
    return args

if __name__ == "__main__":

    args = parse_arguments()

    #The number of samples of data in the frame
    proc_frame_length = 2**12

    a_rate, a_wav_file = scipy.io.wavfile.read(args.a, 'r')
    b_rate, b_wav_file = scipy.io.wavfile.read(args.b, 'r')
   
    if a_rate != b_rate:
        print "Error files are different rates"

    a_wav_data, a_channel_count, a_file_length = au.parse_audio(a_wav_file)
    b_wav_data, b_channel_count, b_file_length = au.parse_audio(b_wav_file)
    
    if a_channel_count != b_channel_count:
        print "Error files are different channel counts"

    if a_file_length != b_file_length:
        print "Error files are different file lengths " + str(abs(a_file_length - b_file_length))

    channel_count = min(a_channel_count, b_channel_count)
    file_length = min(a_file_length, b_file_length)

    for ch in range(channel_count):
        xcorr = np.zeros(proc_frame_length*2 - 1)

        for frame_start in range(0, file_length, old_div(proc_frame_length,2)):
            if frame_start+proc_frame_length < file_length:

                a_frame = a_wav_data[ch, frame_start:frame_start+proc_frame_length]
                b_frame = b_wav_data[ch, frame_start:frame_start+proc_frame_length]

                r = np.correlate(a_frame, b_frame, mode='full')
                xcorr += r

        if sum(xcorr) == 0:
            ch_a_ahead_of_ch_b = 0
        else:
            ch_a_ahead_of_ch_b =  proc_frame_length - 1 - np.argmax(xcorr)

        if ch_a_ahead_of_ch_b > 0:
            print "Channel a is ahead of b by " + str(ch_a_ahead_of_ch_b) + ' samples'
            a_start = 0
            b_start = abs(ch_a_ahead_of_ch_b)
            a_end = file_length - abs(ch_a_ahead_of_ch_b)
            b_end = file_length
        else :
            print "Channel b is ahead of a by " + str(abs(ch_a_ahead_of_ch_b)) + ' samples'
            a_start = abs(ch_a_ahead_of_ch_b)
            b_start = 0
            a_end = file_length 
            b_end = file_length - abs(ch_a_ahead_of_ch_b)

        rms_channel_diff = np.sqrt(old_div(np.sum((a_wav_data[ch, a_start:a_end] - b_wav_data[ch, b_start:b_end])**2),(file_length - abs(ch_a_ahead_of_ch_b))))

        if rms_channel_diff != 0 :
            print "Ch: " + str(ch) + ' Difference: ' + str(20.*np.log10(rms_channel_diff)) + ' dB'
        else:
            print "Ch: " + str(ch) + ' Exactly the same'


