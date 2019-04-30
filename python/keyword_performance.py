#!/usr/bin/env python
# Copyright (c) 2019, XMOS Ltd, All rights reserved

import os
import subprocess
import argparse

SPOT_EVAL_EXE = 'spot-eval'
SPOT_EVAL_MODEL = 'thfft_alexa_enus_v6_1mb.snsr'

def get_sensory_detections(filename, sensory_path=None):
    sensory_path = sensory_path or os.environ.get('SENSORY_PATH')

    spot_eval_exe = os.path.expanduser(os.path.join(sensory_path, SPOT_EVAL_EXE))
    spot_model = os.path.expanduser(os.path.join(sensory_path, SPOT_EVAL_MODEL))
    if not os.path.isfile(spot_eval_exe):
        raise Exception(f'spot-eval not present in {spot_eval_exe}')
    if not os.path.isfile(spot_model):
        raise Exception(f'model not present in {spot_model}')

    cmd = f'{spot_eval_exe} -t {spot_model} -s operating-point=5 -v {filename}'
    output = subprocess.check_output(cmd, shell=True)
    
    # get result
    detections = []
    lines = output.decode('utf-8').strip().split('\n')
    for ln in lines:
        fields = ln.strip().split()
        detections.append({
            'start': int(fields[0]),
            'end': int(fields[1]),
        })
    
    return detections

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', help='input wav file')
    args = parser.parse_args()

    detections = run_sensory(args.input)
    print(f'Wakewords: {detections}')
