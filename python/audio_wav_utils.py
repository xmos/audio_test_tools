# Copyright (c) 2018-2020, XMOS Ltd, All rights reserved
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from builtins import str
from builtins import range
from pathlib import Path
import numpy as np
import scipy.io.wavfile
import pandas
import subprocess
import re
import socket
import time
import os
import sh

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


def iter_frames(input_wav, frame_advance):
    """ Generator that iterates through a wav in `frame_advance` chunks

    input_wav
        A Path-like, output from scipy.io.wavfile.read, or output from soundfile.read
    """
    try:
        is_file = Path(input_wav).exists()
    except TypeError:
        is_file = False

    if is_file:
        # Load the wav
        _, input_wav_data = scipy.io.wavfile.read(input_wav, 'r')
    else:
        input_wav_data = input_wav

    input_data, input_channel_count, file_length = parse_audio(input_wav_data)

    for frame_start in range(0, file_length-frame_advance, frame_advance):
        new_frame = get_frame(input_data, frame_start, frame_advance)
        yield frame_start, new_frame

def find_free_target_id(target):
    xrun_output = sh.xrun("-l")
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
    if free_target_id is None:
        print(f"Cannot find target: {target}")
    return free_target_id


def get_open_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("",0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port

def test_port_is_open(port):
    port_open = True
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("", port))
    except OSError:
        port_open = False
    s.close()
    return port_open


def run_on_target(xtag_id, infile, outfile, test_wav_exe, host_exe, use_xsim=False):
    port = get_open_port()
    xrun_cmd = f"--xscope-port localhost:{port} --id {xtag_id} {test_wav_exe}"
    xsim_cmd = ['--xscope', f'-realtime localhost:{port}', test_wav_exe]

    def process_output(line):
           print(line)

    #Start and run in background
    if use_xsim:
        print(xsim_cmd)
        xrun_proc = sh.xsim(xsim_cmd, _bg=True)
    else:
        print(xrun_cmd)
        xrun_proc = sh.xrun(xrun_cmd.split(), _bg=True)

    print("Waiting for xrun", end ="")
    while test_port_is_open(port):
        print(".",  end ="", flush=True)
        time.sleep(0.1)
    print()

    print("Starting host app", end ="\n")
    host_cmd = f"{host_exe} {infile} {outfile} {port}"
    host_args = f"{infile} {outfile} {port}"
    host_proc = sh.Command(host_exe)(host_args.split(), _bg=True)
    print(host_proc)
    # for line in host_proc.stdout.decode():
    #     print("****" + line, end ="", flush=True) #Prints output from host and device 
    #     # print(".",  end ="", flush=True) #Prints ....
    print("\nRunning on target finished")

    # Was needed during dev but shouldn't be now as app quits nicely
    # xrun_proc.kill()
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
    # run(f"kill {get_child_xgdb_proc(port)}")



def run_test_wav_xscope(input_file, output_file, test_wav_exe, host_exe, use_xsim=False, target="P[0]"):
    #Find target
    if use_xsim:
        id = None
    else:
        id = find_free_target_id(target)
        assert id != None, "No free XTAG targets available"

    #Prepare file
    test_infile = "input.raw"
    sh.sox(f"{input_file} -b 32 -e signed-integer {test_infile}".split())
    test_outfile = "output.raw"
    
    run_on_target(id, test_infile, test_outfile, test_wav_exe, host_exe, use_xsim)
    sh.sox(f"-b 32 -e signed-integer -c 4 -r 16000 {test_outfile} {output_file}".split())
    os.remove(test_infile)
    os.remove(test_outfile)
