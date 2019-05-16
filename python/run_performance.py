#!/usr/bin/env python
# Copyright (c) 2019, XMOS Ltd, All rights reserved

import sys
import os
import hashlib
import argparse
import json
import csv
import subprocess
import multiprocessing

import numpy as np
import scipy.io.wavfile
import audio_utils as au

import aec_performance
import keyword_performance

ASR_CHANNEL = 0
COMMS_CHANNEL = 1

def dispatch_workunit(testset):
    input_file = testset['input_file']
    output_file = testset['output_file']
    output_file_keyword = None
    y_channel_count = testset['y_channel_count']

    results = []

    print(f'dispatching {input_file}')

    # process input
    cmd = f'test_wav_aec.py {input_file} {y_channel_count} {output_file}'
    subprocess.call(cmd, stdin=None, stdout=None, stderr=None, shell=True)

    # load output
    rate, wav_file = scipy.io.wavfile.read(output_file, 'r')
    wav_data, channel_count, file_length = au.parse_audio(wav_file)
    x_channel_count = channel_count - y_channel_count

    error_data = wav_data[0:y_channel_count] # processed audio
    x_wav_data = wav_data[y_channel_count:] # reference audio

    error_signal, far_signal = aec_performance.apply_phase_compensation(error_data, x_wav_data)

    # compute metrics
    for annotation in testset['annotations']:
        duration = annotation['end']
        start = int(annotation['start'] * rate)
        end = int(annotation['end'] * rate)
        for metric in annotation['metrics']:
            if metric['type'] == 'ERLE':
                erle = aec_performance.get_erle(far_signal[:,start:end], error_signal[ASR_CHANNEL][start:end])
                for ch, e in enumerate(erle):
                    results.append(aec_performance.get_result('ERLE',
                        e, testset['filename'], annotation['start'], annotation['end'])
                    )
            elif metric['type'] == 'ERLE_RECOVERY':
                start = int((annotation['start'] - 2) * rate)
                end = int((annotation['start'] - 0.25) * rate)
                before_erle = aec_performance.get_erle(far_signal[:,start:end], error_signal[ASR_CHANNEL][start:end])
                start = int((annotation['end'] + 0.25) * rate)
                end = int((annotation['end'] + 2) * rate)
                after_erle = aec_performance.get_erle(far_signal[:,start:end], error_signal[ASR_CHANNEL][start:end])
                erle = after_erle - before_erle
                for ch, e in enumerate(erle):
                    results.append(aec_performance.get_result('ERLE_RECOVERY',
                        e, testset['filename'], annotation['start'], annotation['end'])
                    )
            elif metric['type'] == 'ERLE_RECONVERGE':
                start = int(annotation['end'] * rate)
                end = start + int(2 * rate)
                erle = aec_performance.get_erle(far_signal[:,start:end], error_signal[ASR_CHANNEL][start:end])
                for ch, e in enumerate(erle):
                    results.append(aec_performance.get_result('ERLE_RECONVERGE',
                        e, testset['filename'], annotation['start'], annotation['end'])
                    )
            elif metric['type'] == 'ERLE_INTERFERENCE':
                erle = aec_performance.get_erle(far_signal[:,start:end], error_signal[ASR_CHANNEL][start:end])
                for ch, e in enumerate(erle):
                    results.append(aec_performance.get_result('ERLE_INTERFERENCE',
                        e, testset['filename'], annotation['start'], annotation['end'])
                    )
            elif metric['type'] == 'KEYWORD_COUNT':
                if not output_file_keyword:
                    output_file_keyword = testset['output_file_keyword']
                    cmd = f'sox {output_file} -b 16 {output_file_keyword} remix {ASR_CHANNEL+1}'
                    subprocess.call(cmd, stdin=None, stdout=None, stderr=None, shell=True)

                detections = keyword_performance.get_sensory_detections(output_file_keyword)
                results.append(keyword_performance.get_result('KEYWORD_COUNT',
                    len(detections), metric['truth'], testset['filename'], annotation['start'], annotation['end'])
                )

    return results

def load_dataset(input_path, output_path, dataset_file, tests):
    output_path = output_path or os.curdir
    if input_path==output_path:
        print('ERROR: Input path can not equal output path, aborting!')
        exit(1)

    dataset_file = dataset_file or os.path.join(input_path, 'dataset.json')
    dataset = []

    with open(dataset_file, 'r') as fd:
        files = json.load(fd)['files']
        for f in files:
            if f['filename'] in tests or len(tests) == 0:
                basename = os.path.splitext(f['filename'])[0]
                f['input_file'] = os.path.join(input_path, f['filename'])
                f['output_file'] = os.path.join(output_path, basename+'.wav')
                f['output_file_keyword'] = os.path.join(output_path, basename+'-keyword.wav')
                with open(f['input_file'],'rb') as fd:
                    md5sum = hashlib.md5(fd.read()).hexdigest()
                    if md5sum == f['md5sum']:
                        dataset.append(f)
                    else:
                        print(f'WARNING: Skipping {basename} due to checksum failure!')

    return dataset

def run_performance(args):
    dataset = load_dataset(args.input_path, args.output_path, args.dataset_file, set(args.test))
    jobs = args.jobs or len(dataset)

    pool = multiprocessing.Pool(processes=jobs)
    results = pool.map(dispatch_workunit, dataset)

    # save report
    if args.report:
        fd = open(args.report, 'w')
    else:
        fd = sys.stdout

    flat_results = [item for sublist in results for item in sublist]
    w = csv.DictWriter(fd, flat_results[0].keys())
    w.writeheader()
    for row in flat_results:
        w.writerow(row)

    if args.report:
        fd.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-path', help="Input path")
    parser.add_argument('-d', '--dataset-file', default=None, help="Input file (default=dataset.json)")
    parser.add_argument('-o', '--output-path', default=None, help="Output path (default=current directory)")
    parser.add_argument('-s', '--sensory-path', default=None, help="Sensory path")
    parser.add_argument('-j', '--jobs', type=int, default=None,
                        help="Allow N jobs at once; infinite jobs with no arg")
    parser.add_argument('--report', default=None, help="Output report")
    parser.add_argument('--test', action='append', default=[], help="Test to run (defaults to all)")
    args = parser.parse_args()

    if args.sensory_path:
        os.environ['SENSORY_PATH'] = args.sensory_path

    run_performance(args)
