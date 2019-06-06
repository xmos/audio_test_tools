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

def json_to_header_params_old(module_name, elem_dict, header_file_name, print_param):
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

def json_to_header_file_old(config_file, header_file='', print_param=False):
    if header_file is '':
        header_file = config_file.replace('.json', '.h')
    datastore = json_to_dict(config_file)
    if 'module_name' not in datastore:
        print("Error: missing module_name in dictionary")


def json_to_header_params(module_name, elem_dict, list_of_structs, file_handle, print_param):
    #f.write("#define {}_{} ({})\n".format(module_name),
    file_handle.write("{}_t {} {{\n".format(module_name, module_name))
    tabs = '\t'
    file_handle.write("{}{{\n".format(tabs))

    for key in elem_dict:
        print(key)
        if isinstance(elem_dict[key], dict) is False and type(elem_dict[key]) is tuple:
            #print(module_name)
            #print(key)
            #print(list_of_structs)
            #print(list_of_structs[module_name][key])
            print('\n\n6666 {}\n\n\n'.format(key))
            print(elem_dict[key])
            
            #if print_param:
                #print("#define {}_{} ({})".format(module_name.upper(),
                #                                  key.upper(), elem_dict[key]))
            file_handle.write("#define {}_{} ({})\n".format(module_name.upper(),
                                                     key.upper(), elem_dict[key]))
        elif type(elem_dict[key]) is tuple:
            print("\n\n4444 {}\n\n".format(key))
        else:
            print("\n\n5555 {}\n\n".format(key))
            sub_module_name = key
            json_to_header_params(sub_module_name,
                                  elem_dict[key], list_of_structs, file_handle, print_param)
import pprint

class field_data:
    def __init__(self, name, datatype, num):
        self.name = name
        self.datatype = datatype
        self.num = num

def collect_structs(header_file):
    with open(header_file, 'r') as f:
        lines = f.readlines()
        struct_found = 0
        list_of_structs = {}
        current_struct = []
        for line in lines:
            re.sub(r'//.*\n', '', line)
            if re.match("typedef\s+struct\s*{", line):
                struct_found = 1
                continue
            if struct_found == 1:
                s = re.match("\s*}\s*(.*)\s*;", line)
                if s:
                    list_of_structs[s.group(1)[:-2]] = current_struct
                    struct_found = 0
                    current_struct = []
                    continue
                s = re.match("\s*(.*)\s+([\w\d_]*)(\[.*\])?\s*;", line)
                if s:
                    num_values = 1
                    if s.group(3) is not None:
                        num_values = s.group(3).replace('[', '').replace(']', '')
                    new_field = field_data(s.group(2), s.group(1), int(num_values))
                    current_struct.append(new_field)
                continue
    #pprint.pprint(list_of_structs)
    return list_of_structs

def convert_value(datatype, val):
    if re.search('vtb_uq\d+_\d+_t', datatype):
        val = "{}({})".format(datatype[:-2].upper(), val)
    s  = re.match('vtb_([su])((32)|(64))_float_t', datatype)
    if s:
        (m, e) = np.frexp(val)
        m_scale = 0
        if s.group(1) == 's' and s.group(2) == '32':
            m_scale = np.iinfo(np.int32).max
        elif s.group(1) == 'u' and s.group(2) == '32':
            m_scale = np.iinfo(np.uint32).max 
        elif s.group(1) == 's' and s.group(2) == '64':
            m_scale = np.iinfo(np.int64).max
        elif s.group(1) == 'u' and s.group(2) == '64':
            m_scale = np.iinfo(np.uint64).max
        m = int(m*m_scale)
        e -= 32
        val = "{}, {}".format(m,e)
    return val

def add_values_to_header_file(f_handle, top_struct, list_of_structs, datastore):
    f_handle.write("{}_t {} = {{\n".format(top_struct, top_struct))
    tabs = '\t'
    for top_struct_field in list_of_structs[top_struct]:
        for idx in range(top_struct_field.num):
            f_handle.write("{}{{\n".format(tabs))
            tabs += '\t'        
            sub_field = list_of_structs[top_struct_field.datatype.replace('_t','')]
            for item in sub_field:
                value_to_print = convert_value(item.datatype, datastore[top_struct_field.name][idx][item.name])
                f_handle.write("{}// {} {}\n".format(tabs, item.datatype, item.name))
                f_handle.write("{}{{ {} }},\n".format(tabs,value_to_print))
                del datastore[top_struct_field.name][idx][item.name]
            tabs = tabs[-1]
            f_handle.write("{}}},\n".format(tabs))
        while {} in datastore[top_struct_field.name]:
            datastore[top_struct_field.name].remove({})
        if not datastore[top_struct_field.name]:
            del datastore[top_struct_field.name]
        else:
            print("Error: dict values not assigned:\n".format(datastore[top_struct_field.name]))
        tabs = tabs[-1]

    if datastore:
        print("Error: dict values not assigned:\n".format(datastore))
    f_handle.write('};\n')

                


def json_to_header_file(config_file, header_file='agc_ch_state.h', print_param=False):
    output_header_file = config_file.replace('.json', '.h')
    datastore = json_to_dict(config_file)
    #if 'module_name' not in datastore:
    #    print("Error: missing module_name in dictionary")
    #    exit(1)
    pprint.pprint(datastore)
    list_of_structs = collect_structs(header_file)
    with open(output_header_file, 'w') as f_handle:
        header_file_underscore = header_file.replace('.', '_')
        f_handle.write('#ifndef {}\n#define {}\n\n'.format(header_file_underscore, header_file_underscore))
        add_values_to_header_file(f_handle, 'agc_state', list_of_structs, datastore)
        f_handle.write('\n#endif // {}\n'.format(header_file_underscore))
    pprint.pprint(datastore)


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
