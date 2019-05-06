#!/usr/bin/env python
# Copyright (c) 2019, XMOS Ltd, All rights reserved

import argparse
from itertools import combinations

import numpy as np
import scipy.io.wavfile
import audio_utils as au

EPSILON = 1e-99

def wav_width(input_file, start_channel, end_channel):
    rate, wav_file = scipy.io.wavfile.read(input_file, 'r')
    wav_data, channel_count, file_length = au.parse_audio(wav_file)

    start_channel = start_channel - 1
    end_channel = end_channel or (channel_count - 1)

    for channels in combinations(range(start_channel, end_channel), 2):
        mid = np.sum([wav_data[channels[0]], wav_data[channels[1]]], axis=0) / 2.0
        side = np.diff([wav_data[channels[0]], wav_data[channels[1]]], axis=0) / 2.0

        # the mid-signal represents those parts of the stereo-signal which are equal on both channels,
        # the side-signal represents the differences between both channels
        width = np.around(10 * np.log10(np.mean(mid**2.0) / (np.mean(side**2.0) + EPSILON)))

        print(f'Channels ({channels[0] + 1}, {channels[1] + 1})    Width = {width}')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('wav', help='Input wav file')
    parser.add_argument('-s', '--start-channel', type=int, default=0, help="Start channel")
    parser.add_argument('-e', '--end-channel', type=int, default=None, help="End channel")
    args = parser.parse_args()

    wav_width(args.wav, args.start_channel, args.end_channel)
