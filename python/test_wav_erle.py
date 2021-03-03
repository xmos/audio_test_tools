# Copyright (c) 2018-2021, XMOS Ltd, All rights reserved
# This software is available under the terms provided in LICENSE.txt.
import numpy as np
import scipy.io.wavfile
import audio_utils as au
import argparse
import matplotlib.pyplot as plt
import audio_wav_utils

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs='?', help="near end(y) and  far end (x) wav file", default='input.wav')
    parser.add_argument("input_channel_count", nargs='?', help="near end(y) channel count")

    parser.add_argument("output", nargs='?', help="error (e) and passthrough(x) wav file", default='output.pdf')
    parser.add_argument("--verbose", action='store_true', help="Turn verbose mode on", default=False)
    parser.add_argument("--process_until_frame", help="Process until this frame", type=int, default=-1)
    parser.parse_args()
    args = parser.parse_args()
    return args

def test_data(input_wav_data, input_rate, file_length, input_channel_count, verbose = False, process_until_frame = -1, alpha = 0.995):

    frame_len = 240

    total_channel_count = input_wav_data.shape[0]

    output_frames = int(np.ceil(float(file_length) / frame_len))
    padding =  np.zeros((total_channel_count, output_frames * frame_len - file_length))

    framed_input_wav_data = np.hstack((input_wav_data, padding))

    framed_input_wav_data = np.reshape(framed_input_wav_data, (total_channel_count, output_frames, frame_len))
    
    frames_power = np.sum(framed_input_wav_data**2, axis = -1)
    
    frames_power_ewm = np.zeros((total_channel_count, output_frames))
    for f in range(1, output_frames):
        frames_power_ewm[:, f] = frames_power_ewm[:, f-1]*alpha + (1.0-alpha) * frames_power[:, f]

    input_energy = frames_power_ewm[:input_channel_count]
    output_energy = frames_power_ewm[input_channel_count: 2*input_channel_count]


    eps = np.finfo(float).eps
    # erle =  -np.where(output_energy>0.0, np.where(input_energy>0.0,10*np.log10((input_energy+eps) / (output_energy+eps)), np.Inf), np.Inf)
    erle =  np.where(input_energy>0.0, np.where(output_energy>0.0,10*np.log10((output_energy+eps) / (input_energy+eps)), np.Inf), 0)

    return erle


def test_file(input_file, output_file, input_channel_count, verbose = False, process_until_frame = -1):

    input_rate, input_wav_file = scipy.io.wavfile.read(input_file, 'r')
    input_wav_data, total_channel_count, file_length = audio_wav_utils.parse_audio(input_wav_file)

    elre = test_data(input_wav_data, input_rate, file_length, input_channel_count, verbose, process_until_frame)

    plt.clf()
    for input_ch in range(input_channel_count):
        plt.plot(elre[input_ch])
    plt.savefig(output_file)

if __name__ == "__main__":
    args = parse_arguments()

    test_file(args.input, args.output, int(args.input_channel_count), args.verbose, int(args.process_until_frame))




