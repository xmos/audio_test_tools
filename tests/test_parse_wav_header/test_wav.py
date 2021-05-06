# Copyright 2018-2021 XMOS LIMITED.
# This Software is subject to the terms of the XMOS Public Licence: Version 1.

import numpy as np
import scipy.io.wavfile
import sys
import subprocess as sub
import os
import argparse


package_dir = os.path.dirname(os.path.abspath(__file__))
path1 = os.path.join(package_dir,'../../python/')

sys.path.append(path1)

test_wav_exe = os.path.join(package_dir, 'bin/test_wav_parse_header.xe')
test_wav_exe_ai = os.path.join(package_dir, 'bin/AI/test_wav_parse_header.xe')
input_file1 = os.path.join(package_dir, 'test_audio_16b.wav')
input_file2 = os.path.join(package_dir, 'test_audio_32b.wav')
output_file1 = os.path.join(package_dir, 'out1.wav')
output_file2 = os.path.join(package_dir, 'out2.wav')


def test(AI=0):
    #run xcore
    if AI == 0:
        process = sub.call(["axe","--args", test_wav_exe, input_file1, input_file2, output_file1, output_file2])
        assert(process == 0)
    else:
        process = sub.call(["xrun", "--id", "0", "--io", "--args", test_wav_exe_ai, input_file1, input_file2, output_file1, output_file2]) 
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
    parser = argparse.ArgumentParser(description='Run the test.')
    parser.add_argument('--ai', action='store_true', help='run on AI using explorer board')
    args = parser.parse_args()
    test(AI=1 if args.ai else 0)


