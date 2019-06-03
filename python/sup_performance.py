# Copyright (c) 2018-2019, XMOS Ltd, All rights reserved

import numpy as np

EPSILON = 1e-99

AES_METRICS = set([
    'AES_ERLE'
])

AEC_AES_METRICS = set([
    'AEC+AES_ERLE',
    'AEC+AES_KEYWORD_COUNT'
])

NS_METRICS = set([
    'NS'
])

def get_result(metric, value, filename, channel, start, end):
    result = {
        'filename':  filename,
        'channel':  channel,
        'start': start,
        'end': end,
        'metric':  metric,
        'result': value
    }

    grade = None
    if metric == 'AES_ERLE':
        if value >= 30.0:
            grade = 'Outstanding'
        elif value >= 20.0:
            grade = 'Pass'
        elif value >= 10.0:
            grade = 'Warning'
        elif value < 10.0:
            grade = 'Fail'
    elif metric == 'AEC+AES_ERLE':
        if value >= 50.0:
            grade = 'Outstanding'
        elif value >= 40.0:
            grade = 'Pass'
        elif value >= 30.0:
            grade = 'Warning'
        elif value < 30.0:
            grade = 'Fail'
    elif metric == 'NS':
        if value >= 10.0:
            grade = 'Outstanding'
        elif value >= 6.0:
            grade = 'Pass'
        elif value >= 3.0:
            grade = 'Warning'
        elif value < 3.0:
            grade = 'Fail'

    result['grade'] = grade
    
    return result

def get_suppression(orig_signal, sup_signal):
    orig_power = np.power(orig_signal, 2)
    sup_power = np.power(sup_signal, 2)

    orig_sum = np.sum(orig_power, axis=1)
    sup_sum = np.sum(sup_power)
    
    sup = 10 * np.log10(orig_sum / (sup_sum + EPSILON))

    sup[sup < 0] = 0
    sup[sup > 100] = 100

    return sup
