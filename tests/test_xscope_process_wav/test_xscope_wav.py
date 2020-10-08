# Copyright (c) 2018-2020, XMOS Ltd, All rights reserved

import numpy as np
import scipy.io.wavfile
import sys
import os
import audio_wav_utils
from io import StringIO
import sh

TEST_LEN_SECONDS=15
INFILE="noise_4ch.wav"
OUTFILE="noise_4ch_processed.wav"
package_dir = os.path.dirname(os.path.abspath(__file__))
test_wav_exe = os.path.join(package_dir, 'bin/test_xscope_process_wav.xe')
host_exe = os.path.join(package_dir, '../../audio_test_tools/host/xscope_host_endpoint')

input_file = os.path.join(package_dir, INFILE)
output_file = os.path.join(package_dir, OUTFILE)


def test_test_wav_xscope():
    #create test noise file
    length_rounded_to_frame = round((float(TEST_LEN_SECONDS) * 16000.0 / 240.0)) * 240 / 16000
    print(f"Generating a {length_rounded_to_frame}s test file")
    filenames = []
    for ch in range(4):
        filename = f"noise_ch{ch}.wav"
        filenames.append(filename)
        sh.sox(f"-n -c 1 -b 32 -r 16000 -e signed-integer {filename} synth {length_rounded_to_frame} whitenoise vol 1.0".split())
    sh.sox(f"-M {' '.join(filenames)} {input_file} remix 1 2 3 4".split())
    for filename in filenames:
        os.remove(filename)

    audio_wav_utils.run_test_wav_xscope(input_file, output_file, test_wav_exe, host_exe, use_xsim=False, target="O[0]")

    in_rate, in_wav_data = scipy.io.wavfile.read(input_file, 'r')
    out_rate, out_wav_data = scipy.io.wavfile.read(output_file, 'r')

    assert(in_rate == out_rate)
    print(in_wav_data.shape, out_wav_data.shape)
    if not np.array_equal(in_wav_data, out_wav_data):
        for idx in range(256):
            print (in_wav_data[idx], out_wav_data[idx]) 
        assert 0

    print("TEST PASSED")
    
if __name__ == "__main__":
    #If running locally, make sure we build fw. This would normally be done by jenkins
    print("Building firmware")
    sh.waf("configure build".split())
    #Build host app
    print("Building host app")
    os.chdir(os.path.join(package_dir,"../../audio_test_tools/host/"))
    sh.make()
    os.chdir(package_dir)

    test_test_wav_xscope()


