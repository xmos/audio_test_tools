# Copyright (c) 2019, XMOS Ltd, All rights reserved
""" This module contains common util functions used by all the VTB libs """

from __future__ import division
from __future__ import print_function

import os
import re
import configparser
import ast
import numpy as np
import json

def json_to_dict(config_file):
    datastore = None
    with open(config_file, "r") as f:
        input_str = f.read()
        # Remove '//' comments
        json_str = re.sub(r'//.*\n', '\n', input_str)
        datastore = json.loads(json_str)
        f.close()
    return datastore

def dict_to_json(config_dict, config_file):
    json_dump = json.dumps(config_dict, indent=4)
    with open(config_file, "w") as f:
        f.write(json_dump)
        f.close()


def select_process_channels(y_wav_data, channels_to_process):

    if channels_to_process == None:
        y_channel_count = len(y_wav_data)

    else:
        channels_to_process = np.asarray(channels_to_process)
        channels_to_process = channels_to_process[(channels_to_process  >= 0) & (channels_to_process < len(y_wav_data))]
        y_channel_count = min( len(y_wav_data), len(channels_to_process))

        y_wav_data = y_wav_data[channels_to_process]

    return y_wav_data, y_channel_count
