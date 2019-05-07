# Copyright (c) 2019, XMOS Ltd, All rights reserved

import numpy as np

EPSILON = 1e-99

def apply_phase_compensation(y_wav_data, x_wav_data, phase_compensation=32):
    return (y_wav_data[:, phase_compensation:], x_wav_data[:, :-phase_compensation])

'''
Misalignment: is a measure of the system identification performance (in dB)
'''
def get_misalignment(true_filter, estimated_filter):
    raise('This has not been tested!')

    delta = true_filter - estimated_filter
    misalignment = 0 * np.log10(np.power(np.linalg.norm(delta, 2, 1), 2) / 
                                np.power(np.linalg.norm(true_filter, 2, 1), 2))

    return misalignment

'''
Error rate loss enhancement (ERLE): is a measure of the amount (in dB) that the echo has been attenuated
'''
def get_erle(far_signal, error_signal):
    far_power = np.power(far_signal, 2)
    error_power = np.power(error_signal, 2)

    far_sum = np.sum(far_power, axis=1)
    error_sum = np.sum(error_power)
    
    erle = 10 * np.log10(far_sum / (error_sum + EPSILON))
    #print('erle=', erle)

    erle[erle < 0] = 0
    erle[erle > 100] = 100

    return erle

def get_result(metric, value, filename, start, end):
    result = {
        'filename':  filename,
        'start': start,
        'end': end,
        'metric':  metric,
        'result': value
    }

    grade = None
    if metric == 'ERLE':
        if value >= 40.0:
            grade = 'Outstanding'
        elif value >= 30.0:
            grade = 'Pass'
        elif value >= 20.0:
            grade = 'Warning'
        elif value < 20.0:
            grade = 'Fail'
    elif metric == 'ERLE_RECOVERY':
        if value >= -5.0:
            grade = 'Outstanding'
        elif value >= -10.0:
            grade = 'Pass'
        elif value >= -15.0:
            grade = 'Warning'
        elif value < -15.0:
            grade = 'Fail'
    elif metric == 'ERLE_RECONVERGE':
        if value >= 30.0:
            grade = 'Outstanding'
        elif value >= 25.0:
            grade = 'Pass'
        elif value >= 20.0:
            grade = 'Warning'
        elif value < 20.0:
            grade = 'Fail'

    result['grade'] = grade
    return result