# Copyright (c) 2020, XMOS Ltd, All rights reserved
import numpy as np
import scipy.io.wavfile
import sys
import os
import audio_wav_utils

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
    audio_wav_utils.run(f"sox -n -c 4 -b 32 -r 16000 -e signed-integer {input_file} synth {length_rounded_to_frame} whitenoise vol 1.0")

    audio_wav_utils.run_test_wav_xscope(input_file, output_file, test_wav_exe, host_exe, use_xsim=False, target="O[0]")

    in_rate, in_wav_data = scipy.io.wavfile.read(input_file, 'r')
    out_rate, out_wav_data = scipy.io.wavfile.read(output_file, 'r')

    assert(in_rate == out_rate)
    assert(np.array_equal(in_wav_data, out_wav_data) == True)

    print("TEST PASSED")
    
if __name__ == "__main__":
    #If running locally, make sure we build fw. This would normally be done by jenkins
    print("Building firmware")
    audio_wav_utils.run("waf configure build")
    #Build host app
    print("Building host app")
    os.chdir(os.path.join(package_dir,"../../audio_test_tools/host/"))
    audio_wav_utils.run("make")
    os.chdir(package_dir)

    test_test_wav_xscope()


