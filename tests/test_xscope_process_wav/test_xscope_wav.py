# Copyright (c) 2020, XMOS Ltd, All rights reserved
import numpy as np
import scipy.io.wavfile
import sys
import subprocess
import os
import re
import socket
import time


TEST_LEN_SECONDS=0.05
INFILE="noise_4ch.wav"
OUTFILE="noise_4ch_processed.wav"
USE_XSIM=True #For testing locally without HW only. VERY slow
package_dir = os.path.dirname(os.path.abspath(__file__))
test_wav_exe = os.path.join(package_dir, 'bin/test_test_wav_xscope.xe')
host_exe = os.path.join(package_dir, '../../audio_test_tools/host/xscope_host_endpoint')

input_file = os.path.join(package_dir, INFILE)
output_file = os.path.join(package_dir, OUTFILE)

def run(cmd, stdin=b""):
    process = subprocess.Popen(cmd.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = process.communicate(stdin)
    rc = process.returncode
    assert rc == 0, f"Error running cmd: {cmd}\n output: {err}"
    return output.decode("utf-8") 

def find_free_target_id(target="P[0]"):
    xrun_output = run("xrun -l")
    escaped_target = ""
    for char in target:
        if "[" in char or "]" in char:
            escaped_target += "\\"
        escaped_target += char

    free_target_id = None
    for line in xrun_output.splitlines():
        # xrun will return [in use] if not available so not a match
        # we will find all matches and so this returns the last available target ID in the list
        match = re.match("\s+(\d+)\s+XMOS XTAG-\d\s+\w+\s+"+escaped_target, line)
        if match:
            free_target_id = int(match.group(1))
    return free_target_id

def get_open_port():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("",0))
        s.listen(1)
        port = s.getsockname()[1]
        s.close()
        return port

def run_on_target(xtag_id, infile, outfile):
    port = get_open_port()
    xrun_cmd = f"xrun --xscope-port localhost:{port} --id {xtag_id} {test_wav_exe}"
    xsim_cmd = ['xsim', '--xscope', f'-realtime localhost:{port}', test_wav_exe]

    #Run in background
    if USE_XSIM:
        xrun_proc = subprocess.Popen(xsim_cmd)
    else:
        xrun_proc = subprocess.Popen(xrun_cmd.split())

    #Time for xscope host process to start
    time.sleep(1)

    def get_child_xgdb_proc(port):
        ps_out = run("ps")
        report = ""
        for line in ps_out.splitlines():
            xgdb_match = re.match("\s+(\d+).+-x\s+(\S+)\s+.*", line)
            if(xgdb_match):
                pid = xgdb_match.group(1)
                with open(xgdb_match.group(2), 'r') as file:
                    xgdb_session = file.read().replace('\n', '')
                    port_match = re.match(".+localhost:(\d+).+", xgdb_session)
                    if port_match:
                        xgdb_port = int(port_match.group(1))
                        report += f"Found xgdb instance with PID: {pid} on port: {xgdb_port}"
                        if xgdb_port == port:
                            return pid
        print(report)
        print(f"ERROR: Did not find xgdb running on port: {port}")
        return None

    host_cmd = f"{host_exe} {infile} {outfile} {port}"
    run(host_cmd)

    # Was needed during dev but shouldn't be now as app quits nicely
    # xrun_proc.kill()
    # run(f"kill {get_child_xgdb_proc(port)}")




def run_test_wav_xscope():
    #Find target
    if USE_XSIM:
        id = None
    else:
        id = find_free_target_id("O[0]")
        assert id != None, "No free XTAG targets available"

    #Prepare file
    test_infile = "input.raw"
    run(f"sox {input_file} -b 32 -e signed-integer {test_infile}")
    test_outfile = "output.raw"
    
    run_on_target(id, test_infile, test_outfile)
    run(f"sox -b 32 -e signed-integer -c 4 -r 16000 {test_outfile} {output_file}")
    os.remove(test_infile)
    os.remove(test_outfile)



def test_test_wav_xscope(jenkins=True):
    global input_file, output_file

    if not jenkins:
        #Build fw
        run("waf configure build")
        #Build host app
        os.chdir(os.path.join(package_dir,"../../audio_test_tools/host/"))
        run("make")
        os.chdir(package_dir)
        #Build firmware


    #create test noise file
    length_rounded_to_frame = round((float(TEST_LEN_SECONDS) * 16000.0 / 240.0)) * 240 / 16000
    print(f"Generating a {length_rounded_to_frame}s test file")
    run(f"sox -n -c 4 -b 32 -r 16000 -e signed-integer {input_file} synth {length_rounded_to_frame} whitenoise vol 1.0")

    run_test_wav_xscope()

    in_rate, in_wav_data = scipy.io.wavfile.read(input_file, 'r')
    out_rate, out_wav_data = scipy.io.wavfile.read(output_file, 'r')

    assert(in_rate == out_rate)
    assert(np.array_equal(in_wav_data, out_wav_data) == True)

    print("TEST PASS")
    
if __name__ == "__main__":
    # subprocess.run(['xsim', '--xscope', '-realtime localhost:12334', test_wav_exe])
    test_test_wav_xscope(jenkins=False)


