#!/usr/bin/env python
# Copyright (c) 2018-2019, XMOS Ltd, All rights reserved

import sys
import os
import hashlib
import argparse
import json
import csv
import tempfile
import subprocess
import multiprocessing

import numpy as np
import scipy.io.wavfile
import audio_utils as au

import aec_performance
import sup_performance
import keyword_performance

ASR_CHANNEL = 0
COMMS_CHANNEL = 1

def process_aec(testset):
    input_file = testset['input_file']
    output_file = testset['aec_output_file']
    y_channel_count = testset['y_channel_count']

    if not os.path.isfile(output_file):
        # process input
        if y_channel_count == 2:
            config_file = '../../lib_aec/lib_aec/config/stereo_aec_two_mic.json'
            cmd = f'test_wav_aec.py {input_file} {output_file} {config_file}'
        else:
            raise Exception(f'y_channel_count = {y_channel_count}, only stereo is supported')
        
        subprocess.call(cmd, stdin=None, stdout=None, stderr=None, shell=True)

def gather_aec(testset):
    input_file = testset['input_file']
    output_file = testset['aec_output_file']
    output_file_keyword = None
    y_channel_count = testset['y_channel_count']

    results = []

    # load output
    rate, wav_file = scipy.io.wavfile.read(output_file, 'r')
    wav_data, channel_count, file_length = au.parse_audio(wav_file)
    error_data = wav_data[0:y_channel_count] # processed audio

    # load reference
    rate, wav_file = scipy.io.wavfile.read(input_file, 'r')
    wav_data, channel_count, file_length = au.parse_audio(wav_file)
    x_wav_data = wav_data[y_channel_count:] # reference audio

    error_signal, far_signal = aec_performance.apply_phase_compensation(error_data, x_wav_data)

    # compute metrics
    for annotation in testset['annotations']:
        duration = annotation['end']
        start = int(annotation['start'] * rate)
        end = int(annotation['end'] * rate)
        for metric in annotation['metrics']:
            if metric == 'AEC_ERLE':
                erle = aec_performance.get_erle(far_signal[:,start:end], error_signal[ASR_CHANNEL][start:end])
                for ch, e in enumerate(erle):
                    results.append(aec_performance.get_result('AEC_ERLE',
                        e, testset['filename'], ch, annotation['start'], annotation['end'])
                    )
            elif metric == 'AEC_ERLE_RECOVERY':
                start = int((annotation['start'] - 2) * rate)
                end = int((annotation['start'] - 0.25) * rate)
                before_erle = aec_performance.get_erle(far_signal[:,start:end], error_signal[ASR_CHANNEL][start:end])
                start = int((annotation['end'] + 0.25) * rate)
                end = int((annotation['end'] + 2) * rate)
                after_erle = aec_performance.get_erle(far_signal[:,start:end], error_signal[ASR_CHANNEL][start:end])
                erle = after_erle - before_erle
                for ch, e in enumerate(erle):
                    results.append(aec_performance.get_result('AEC_ERLE_RECOVERY',
                        e, testset['filename'], ch, annotation['start'], annotation['end'])
                    )
            elif metric == 'AEC_ERLE_RECONVERGE':
                start = int(annotation['end'] * rate)
                end = start + int(2 * rate)
                erle = aec_performance.get_erle(far_signal[:,start:end], error_signal[ASR_CHANNEL][start:end])
                for ch, e in enumerate(erle):
                    results.append(aec_performance.get_result('AEC_ERLE_RECONVERGE',
                        e, testset['filename'], ch, annotation['start'], annotation['end'])
                    )
            elif metric == 'AEC_ERLE_INTERFERENCE':
                erle = aec_performance.get_erle(far_signal[:,start:end], error_signal[ASR_CHANNEL][start:end])
                for ch, e in enumerate(erle):
                    results.append(aec_performance.get_result('AEC_ERLE_INTERFERENCE',
                        e, testset['filename'], ch, annotation['start'], annotation['end'])
                    )
            elif metric == 'AEC_KEYWORD_COUNT':
                if not output_file_keyword:
                    output_file_keyword = testset['aec_output_file_keyword']
                    cmd = f'sox {output_file} -b 16 {output_file_keyword} remix {ASR_CHANNEL+1}'
                    subprocess.call(cmd, stdin=None, stdout=None, stderr=None, shell=True)

                detections = keyword_performance.get_sensory_detections(output_file_keyword)
                results.append(keyword_performance.get_result('AEC_KEYWORD_COUNT',
                    len(detections), annotation['keywords'], testset['filename'], 0, annotation['start'], annotation['end'])
                )

    return results

def process_aes(testset, use_aec):
    if use_aec:
        input_file = testset['aec_output_file']
        output_file = testset['aec_aes_output_file']
        output_file_keyword = None
    else:
        input_file = testset['input_file']
        output_file = testset['aes_output_file']
        output_file_keyword = None

    y_channel_count = testset['y_channel_count']

    if not os.path.isfile(output_file):
        # process input
        if y_channel_count == 2:
            # make config files
            sup_config_file = '../../lib_noise_suppression/lib_noise_suppression/config/stereo_two_mic.json'
            with open(sup_config_file, 'r') as fd:
                config = json.loads(fd.read())
                config['ns_parameters'] = None
                aes_config_file = os.path.join(tempfile.gettempdir(), 'aes.config')
                with open(aes_config_file, 'w') as out:
                    out.write(json.dumps(config))
            cmd = f'test_wav_suppression.py {input_file} {output_file} {aes_config_file}'

            # develop branch
            #cmd = f'test_wav_suppression.py {input_file} 2 2 {output_file}'
        else:
            raise Exception(f'y_channel_count = {y_channel_count}, only stereo is supported')

        subprocess.call(cmd, stdin=None, stdout=None, stderr=None, shell=True)

def gather_aes(testset):
    input_file = testset['input_file']
    output_file = testset['aes_output_file']
    output_file_keyword = None

    y_channel_count = testset['y_channel_count']

    results = []

    # load output
    rate, wav_file = scipy.io.wavfile.read(output_file, 'r')
    wav_data, channel_count, file_length = au.parse_audio(wav_file)
    error_data = wav_data[0:y_channel_count] # processed audio

    # load reference
    rate, wav_file = scipy.io.wavfile.read(input_file, 'r')
    wav_data, channel_count, file_length = au.parse_audio(wav_file)
    x_wav_data = wav_data[y_channel_count:] # reference audio

    error_signal, far_signal = aec_performance.apply_phase_compensation(error_data, x_wav_data)

    # compute metrics
    for annotation in testset['annotations']:
        duration = annotation['end']
        start = int(annotation['start'] * rate)
        end = int(annotation['end'] * rate)
        for metric in annotation['metrics']:
            if metric == 'AES_ERLE':
                erle = aec_performance.get_erle(far_signal[:,start:end], error_signal[ASR_CHANNEL][start:end])
                for ch, e in enumerate(erle):
                    results.append(sup_performance.get_result('AES_ERLE',
                        e, testset['filename'], ch, annotation['start'], annotation['end'])
                    )

    return results

def gather_aec_aes(testset):
    input_file = testset['input_file']
    output_file = testset['aec_aes_output_file']
    output_file_keyword = None

    y_channel_count = testset['y_channel_count']

    results = []

    # load output
    rate, wav_file = scipy.io.wavfile.read(output_file, 'r')
    wav_data, channel_count, file_length = au.parse_audio(wav_file)
    error_data = wav_data[0:y_channel_count] # processed audio

    # load reference
    rate, wav_file = scipy.io.wavfile.read(input_file, 'r')
    wav_data, channel_count, file_length = au.parse_audio(wav_file)
    x_wav_data = wav_data[y_channel_count:] # reference audio

    error_signal, far_signal = aec_performance.apply_phase_compensation(error_data, x_wav_data)

    # compute metrics
    for annotation in testset['annotations']:
        duration = annotation['end']
        start = int(annotation['start'] * rate)
        end = int(annotation['end'] * rate)
        for metric in annotation['metrics']:
            if metric == 'AEC+AES_ERLE':
                erle = aec_performance.get_erle(far_signal[:,start:end], error_signal[ASR_CHANNEL][start:end])
                for ch, e in enumerate(erle):
                    results.append(sup_performance.get_result('AEC+AES_ERLE',
                        e, testset['filename'], ch, annotation['start'], annotation['end'])
                    )
            elif metric == 'AEC+AES_KEYWORD_COUNT':
                if not output_file_keyword:
                    output_file_keyword = testset['aec_output_file_keyword']
                    cmd = f'sox {output_file} -b 16 {output_file_keyword} remix {ASR_CHANNEL+1}'
                    subprocess.call(cmd, stdin=None, stdout=None, stderr=None, shell=True)

                detections = keyword_performance.get_sensory_detections(output_file_keyword)
                results.append(keyword_performance.get_result('AEC+AES_KEYWORD_COUNT',
                    len(detections), annotation['keywords'], testset['filename'], 0, annotation['start'], annotation['end'])
                )

    return results

def process_ns(testset):
    input_file = testset['input_file']
    output_file = testset['ns_output_file']
    output_file_keyword = None

    y_channel_count = testset['y_channel_count']

    if not os.path.isfile(output_file):
        # process input
        if y_channel_count == 2:
            # make config files
            sup_config_file = '../../lib_noise_suppression/lib_noise_suppression/config/stereo_two_mic.json'
            with open(sup_config_file, 'r') as fd:
                config = json.loads(fd.read())
                config['aes_parameters'] = None
                aes_config_file = os.path.join(tempfile.gettempdir(), 'ns.config')
                with open(aes_config_file, 'w') as out:
                    out.write(json.dumps(config))
            cmd = f'test_wav_suppression.py {input_file} {output_file} {aes_config_file}'
            
            # develop
            #cmd = f'test_wav_suppression.py {input_file} 2 2 {output_file} 0 1'
        else:
            raise Exception(f'y_channel_count = {y_channel_count}, only stereo is supported')

        subprocess.call(cmd, stdin=None, stdout=None, stderr=None, shell=True)

def gather_ns(testset):
    input_file = testset['input_file']
    output_file = testset['ns_output_file']
    output_file_keyword = None

    y_channel_count = testset['y_channel_count']

    results = []

    # load output
    rate, wav_file = scipy.io.wavfile.read(output_file, 'r')
    wav_data, channel_count, file_length = au.parse_audio(wav_file)
    proc_data = wav_data[0:y_channel_count] # processed audio

    # load mic data
    rate, wav_file = scipy.io.wavfile.read(input_file, 'r')
    wav_data, channel_count, file_length = au.parse_audio(wav_file)
    orig_data = wav_data[0:y_channel_count] # original audio

    # compute metrics
    for annotation in testset['annotations']:
        duration = annotation['end']
        start = int(annotation['start'] * rate)
        end = int(annotation['end'] * rate)
        for metric in annotation['metrics']:
            if metric == 'NS':
                sup = sup_performance.get_suppression(orig_data[:,start:end], proc_data[ASR_CHANNEL][start:end])
                for ch, e in enumerate(sup):
                    results.append(sup_performance.get_result('NS',
                        e, testset['filename'], ch, annotation['start'], annotation['end'])
                    )

    return results

def dispatch_workunit(testset):
    input_file = testset['input_file']

    print(f'dispatching {input_file}')

    results = []

    components = set(testset['components'])

    if 'aec' in components:
        process_aec(testset)
        results.extend(gather_aec(testset))
    if 'aes' in components:
        process_aes(testset, False)
        results.extend(gather_aes(testset))
    if 'aec+aes' in components:
        process_aec(testset)
        process_aes(testset, True)
        results.extend(gather_aec_aes(testset))
    if 'ns' in components:
        process_ns(testset)
        results.extend(gather_ns(testset))

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
                # determine processing components
                components = set()
                for annotation in f['annotations']:
                    for metric in annotation['metrics']:
                        if metric in aec_performance.METRICS:
                            components.add('aec')
                        elif metric in sup_performance.AES_METRICS:
                            components.add('aes')
                        elif metric in sup_performance.AEC_AES_METRICS:
                            components.add('aec+aes')
                        elif metric in sup_performance.NS_METRICS:
                            components.add('ns')
                f['components'] = list(components)

                # aec output
                aec_output_path = os.path.join(output_path, 'aec')
                if not os.path.exists(aec_output_path):
                    os.makedirs(aec_output_path)
                if 'aec' in components:
                    f['aec_output_file'] = os.path.join(aec_output_path, basename +'-aec_output.wav')
                    f['aec_output_file_keyword'] = os.path.join(aec_output_path, basename +'-aec_output-keyword.wav')
                # suppression output
                sup_output_path = os.path.join(output_path, 'sup')
                if not os.path.exists(sup_output_path):
                    os.makedirs(sup_output_path)
                if 'ns' in components:
                    f['ns_output_file'] = os.path.join(sup_output_path, basename+'-ns_output.wav')
                    f['ns_output_file_keyword'] = os.path.join(sup_output_path, basename +'-ns_output-keyword.wav')
                if 'aes' in components:
                    f['aes_output_file'] = os.path.join(sup_output_path, basename+'-aes_output.wav')
                    f['aes_output_file_keyword'] = os.path.join(sup_output_path, basename +'-aes_output-keyword.wav')
                if 'aec+aes' in components:
                    f['aec_aes_output_file'] = os.path.join(sup_output_path, basename +'-aec_aes_output.wav')
                    f['aec_aes_output_file_keyword'] = os.path.join(sup_output_path, basename +'-aec_aes_output-keyword.wav')
                # if 'sup' in components:
                #     f['sup_output_file'] = os.path.join(sup_output_path, basename +'-sup_output.wav')
                #     f['sup_output_file_keyword'] = os.path.join(sup_output_path, basename +'-sup_output-keyword.wav')
                # verify input file
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
    parser.add_argument('-i', '--input-path', required=True, help="Input path")
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
