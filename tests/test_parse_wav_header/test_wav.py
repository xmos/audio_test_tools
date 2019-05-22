# Copyright (c) 2018-2019, XMOS Ltd, All rights reserved

import numpy as np
import scipy.io.wavfile
import sys
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import subprocess as sub
import os

package_dir = os.path.dirname(os.path.abspath(__file__))
path1 = os.path.join(package_dir,'../../python/')

sys.path.append(path1)

import audio_utils as au

test_wav_exe = os.path.join(package_dir, 'bin/test_wav.xe')
input_file1 = os.path.join(package_dir, 'test_audio_16b.wav')
input_file2 = os.path.join(package_dir, 'test_audio_32b.wav')
output_file1 = os.path.join(package_dir, 'out1.wav')
output_file2 = os.path.join(package_dir, 'out2.wav')


def test():
    #run xcore
    process = sub.call(["axe","--args", test_wav_exe, input_file1, input_file2, output_file1, output_file2])
    assert(process == 0)

    in_rate1, in_wav_data1 = scipy.io.wavfile.read(input_file1, 'r')
    in_rate2, in_wav_data2 = scipy.io.wavfile.read(input_file2, 'r')

    out_rate1, out_wav_data1 = scipy.io.wavfile.read(output_file1, 'r')
    out_rate2, out_wav_data2 = scipy.io.wavfile.read(output_file2, 'r')
    assert(in_rate1 == out_rate1)
    assert(in_rate2 == out_rate2)

    assert(np.array_equal(in_wav_data1, out_wav_data1) == True)
    assert(np.array_equal(in_wav_data2, out_wav_data2) == True)
 
if __name__ == "__main__":
    test()


