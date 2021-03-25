# Copyright (c) 2018-2021, XMOS Ltd, All rights reserved
# This software is available under the terms provided in LICENSE.txt.
# -*- coding: utf-8 -*-
"""
@author: Andrew
"""
from __future__ import division
from __future__ import print_function
from builtins import str
from builtins import range
import numpy as np
import scipy.io.wavfile
import matplotlib
import matplotlib.pyplot as plt
import pandas

speed_of_sound = 342.0

mic_d    = 0.043

circular_mic_array = np.asarray(
        [  [0.0,     0.0,                0.0], 
        [mic_d/2.0,   np.sin(np.pi/3)*mic_d,  0.0], 
        [mic_d,       0.0,                0.0], 
        [mic_d/2.0,  -np.sin(np.pi/3)*mic_d,  0.0], 
        [-mic_d/2.0,  -np.sin(np.pi/3)*mic_d, 0.0], 
        [-mic_d,       0.0,                0.0], 
        [-mic_d/2.0,   np.sin(np.pi/3)*mic_d,  0.0]]
    )

def distance_between_points(a, b):
    return np.sqrt(sum((a-b)**2))

def translate_position(p, x, y, z):
    p_t = p + np.asarray([x, y, z])
    return p_t

def rotate_around_x_axis(p, theta):
    R = np.asarray([[1., 0., 0.],[0., np.cos(theta), -np.sin(theta)],[0., np.sin(theta), np.cos(theta)]])
    p_t = np.dot(p, R)
    return p_t

def rotate_around_y_axis(p, theta):
    R = np.asarray([[np.cos(theta), 0., np.sin(theta)],[0., 1., 0.],[-np.sin(theta), 0., np.cos(theta)]])
    p_t = np.dot(p, R)
    return p_t

def rotate_around_z_axis(p, theta):
    R = np.asarray([[np.cos(theta), -np.sin(theta), 0.],[np.sin(theta), np.cos(theta), 0.],[0., 0., 1.,]])
    p_t = np.dot(p, R)
    return p_t

def print_phi(phi):
    for i in range(len(phi)):
        for j in range(len(phi[i])):
            print(('% .4f '%phi[i][j]), end=' ')
        print ('')
    print ('')
    print ('')
    return

def make_mvdr_matrices(f_bin_count, fft_length, channel_count, rate):
    W = np.zeros((f_bin_count, channel_count, channel_count))
    mu = 0.0000001
    for f_bin in range(f_bin_count):
        freq = 2.0*np.pi*float(f_bin) / float(fft_length)  * float(rate)
        for i in range(channel_count):
            for j in range(channel_count):
                v = np.sinc(freq*d(i, j)/speed_of_sound)
                if i==j:
                    v += mu
                W[f_bin][i][j] = v
        W[f_bin] = np.linalg.pinv(W[f_bin])
    return W

# Apply a sample delay to a frequency domain frame (can be -ve as well)
def steer_channel(Channel, delay):
    fft_length = ((len(Channel)-1) *2)
    w = np.exp(-2.0j*np.pi*np.arange(len(Channel))/float(fft_length) * float(delay))
    return Channel * w

def output_tdoa_graph(gcc_results, filename, max_spread = 2.0):
    plt.clf()
    plt.cla()
    for c in range(len(gcc_results)):
        plt.plot( gcc_results[c], label='ch ' + str(c))
    plt.ylim(-max_spread, max_spread)
    plt.title('TDOA')
    plt.legend()
    plt.xlabel('frame number')
    plt.ylabel('TDOA (samples)')
    plt.savefig(filename, dpi=100)  
    return

def output_multiple_tdoa_graphs(multiple_gcc_results, filename, max_spread = 2.0):
    plt.clf()
    plt.cla()
    for g in range(len(multiple_gcc_results)):
        plt.subplot(len(multiple_gcc_results), 1, g+1)
        for c in range(len(multiple_gcc_results[g])):
            plt.plot( multiple_gcc_results[g][c], label='ch ' + str(c))
        plt.ylim(-max_spread, max_spread)
        plt.title('TDOA')
        plt.legend()
        plt.xlabel('frame number')
        plt.ylabel('TDOA (samples)')
    plt.savefig(filename, dpi=100)  
    return

