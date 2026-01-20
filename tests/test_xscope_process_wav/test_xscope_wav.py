# Copyright 2018-2022 XMOS LIMITED.
# This Software is subject to the terms of the XMOS Public Licence: Version 1.

import numpy as np
import scipy.io.wavfile
import sys
import os
# import audio_wav_utils

import xscope_fileio
import xtagctl
from io import StringIO
import subprocess

TEST_LEN_SECONDS=15
INFILE="input.wav"
OUTFILE="output.wav"
package_dir = os.path.dirname(os.path.abspath(__file__))
test_wav_exe = os.path.join(package_dir, 'bin/test_xscope_process_wav.xe')

input_file = os.path.join(package_dir, INFILE)
output_file = os.path.join(package_dir, OUTFILE)


def test_test_wav_xscope():
    #create test noise file. Note we round to a frame because test_wav_xscope can only handle full frames
    length_rounded_to_frame = round((float(TEST_LEN_SECONDS) * 16000.0 / 240.0)) * 240 / 16000
    print(f"Generating a {length_rounded_to_frame}s test file")
    filenames = []
    for ch in range(4):
        filename = f"noise_ch{ch}.wav"
        filenames.append(filename)
        cmd_opts = f"-n -c 1 -b 32 -r 16000 -e signed-integer {filename} synth {length_rounded_to_frame} whitenoise vol 1.0"
        subprocess.run(["sox", *cmd_opts.split()])
    cmd_opts = f"-M {' '.join(filenames)} {input_file} remix 1 2 3 4"
    subprocess.run(["sox", *cmd_opts.split()])
    for filename in filenames:
        os.remove(filename)

    print(f"acquire")
    with xtagctl.acquire("XCORE-AI-EXPLORER") as adapter_id:
        print(f"Running on {adapter_id}")
        xscope_fileio.run_on_target(adapter_id, test_wav_exe)
   
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
    subprocess.run(["waf", "configure", "build"])
    #Build host app
    print("Building host app")
    os.chdir(os.path.join(package_dir,"../../../xscope_fileio/host"))
    subprocess.run(["make"])
    os.chdir(package_dir)

    test_test_wav_xscope()


