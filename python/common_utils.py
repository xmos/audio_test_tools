# Copyright (c) 2019, XMOS Ltd, All rights reserved
""" This module contains common util functions used by all the VTB libs """
from __future__ import division
from __future__ import print_function
import re
import json
import numpy as np

def json_to_dict(config_file, print_param=False):
    datastore = None
    with open(config_file, "r") as f:
        input_str = f.read()
        # Remove '//' comments
        json_str = re.sub(r'//.*\n', '\n', input_str)
        if print_param is True:
            print(json_str)
        datastore = json.loads(json_str)
        f.close()
    return datastore

def dict_to_json(config_dict, config_file, print_param=False):
    json_dump = json.dumps(config_dict, indent=4)
    if print_param is True:
        print(json_dump)
    with open(config_file, "w") as f:
        f.write(json_dump)
        f.close()

def json_to_header_params(module_name, elem_dict, header_file_name, print_param):
    with open(header_file_name, 'w') as f:
        header_file_underscore = header_file_name.replace('.', '_')
        f.write('#ifndef {}\n#define {}\n\n'.format(header_file_underscore, header_file_underscore))
        for key in elem_dict:
            if isinstance(elem_dict[key], dict) is False:
                if print_param:
                    print("#define {}_{} ({})".format(module_name.upper(),
                                                      key.upper(), elem_dict[key]))
                f.write("#define {}_{} ({})\n".format(module_name.upper(),
                                                      key.upper(), elem_dict[key]))
            else:
                header_sub_file = key+'.h'
                sub_module_name = module_name+'_'+key.replace('_conf', '').\
                                  replace('_parameters', '')
                json_to_header_params(sub_module_name,
                                      elem_dict[key], header_sub_file, print_param)
        f.write('\n#endif // {}\n'.format(header_file_underscore))

def json_to_header_file(config_file, header_file='', print_param=False):
    if header_file is '':
        header_file = config_file.replace('.json', '.h')
    datastore = json_to_dict(config_file)
    if 'algo_name' not in datastore:
        print("Error: missing algo_name in dictionary")
        exit(1)
    json_to_header_params(datastore['algo_name'], datastore, header_file, print_param)

def select_process_channels(y_wav_data, channels_to_process):
    if channels_to_process == None:
        y_channel_count = len(y_wav_data)
    else:
        channels_to_process = np.asarray(channels_to_process)
        channels_to_process = channels_to_process[(channels_to_process >= 0) &\
                             (channels_to_process < len(y_wav_data))]
        y_channel_count = min(len(y_wav_data), len(channels_to_process))
        y_wav_data = y_wav_data[channels_to_process]
    return y_wav_data, y_channel_count
