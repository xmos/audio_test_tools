# Copyright (c) 2018-2019, XMOS Ltd, All rights reserved

AES_METRICS = set([
    'AES_ERLE'
])

AEC_AES_METRICS = set([
    'AEC+AES_ERLE'
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
    if metric == 'AEC+AES_ERLE':
        if value >= 50.0:
            grade = 'Outstanding'
        elif value >= 40.0:
            grade = 'Pass'
        elif value >= 30.0:
            grade = 'Warning'
        elif value < 30.0:
            grade = 'Fail'

    result['grade'] = grade
    
    return result