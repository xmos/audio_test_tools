# Copyright (c) 2019, XMOS Ltd, All rights reserved
""" This module contains common util functions used by all the VTB libs """
from __future__ import division
from __future__ import print_function
import re
import json
import pprint
import numpy as np

def json_to_dict(config_file):
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

def dict_to_json(config_dict, config_file):
    json_dump = json.dumps(config_dict, indent=4)
    if print_param is True:
        print(json_dump)
    with open(config_file, "w") as f:
        f.write(json_dump)
        f.close()

class FieldData:
    def __init__(self, name, datatype, num):
        self.name = name
        self.datatype = datatype
        self.num = num
    def __repr__(self):
        return "<Name:{} DataType:{} Num:{}>".format(self.name, self.datatype, self.num)

    def __str__(self):
        return "<Name:{} DataType:{} Num:{}>".format(self.name, self.datatype, self.num)

class JsonHandler():
    def __init__(self, json_file, dubug_print):
        self.c_structs = {}
        self.json_dict = {}
        self.h_file_handle = ''
        self.header_file = ''
        self.json_file = json_file
        self.tabs = ''
        self.debug_print = dubug_print

    def collect_c_structs(self):
        with open(self.header_file, 'r') as f:
            lines = f.readlines()
            struct_found = 0
            current_struct = []
            for line in lines:
                line = re.sub(r'//.*\n', '\n', line)
                if re.match("typedef\s+struct\s*{", line):
                    struct_found = 1
                    continue
                if struct_found == 1:
                    s = re.match("\s*}\s*(.*)\s*;", line)
                    if s:
                        self.c_structs[s.group(1)[:-2]] = current_struct
                        struct_found = 0
                        current_struct = []
                        continue
                    s = re.match("\s*(.*)\s+([\w\d_]*)(\[.*\])?\s*;", line)
                    if s:
                        num_values = 1
                        if s.group(3) is not None:
                            num_values = s.group(3).replace('[', '').replace(']', '')
                        new_field = FieldData(s.group(2), s.group(1), int(num_values))
                        current_struct.append(new_field)
                    continue
        if self.debug_print:
            pprint.pprint(self.c_structs)


    def convert_value(self, datatype, val):
        if re.search('vtb_uq\d+_\d+_t', datatype):
            val = "{}({})".format(datatype[:-2].upper(), val)
        s = re.match('vtb_([su])((32)|(64))_float_t', datatype)
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
            val = "{}, {}".format(m, e)
        return val

    def add_item(self, json_dict, item):
        if item.name not in json_dict.keys():
            print("Error: {} not present in json file".format(item.name))
            return
        json_val = json_dict[item.name]
        value_to_print = self.convert_value(item.datatype, json_val)
        self.h_file_handle.write("{}// {} {} -> {}\n".format(self.tabs, item.datatype, item.name, json_val))
        self.h_file_handle.write("{}{{ {} }},\n".format(self.tabs, value_to_print))
        del json_dict[item.name]


    def parse_c_structs(self, top_struct, datastore):
        for top_struct_field in self.c_structs[top_struct]:
            for idx in range(top_struct_field.num):
                self.h_file_handle.write("{}{{\n".format(self.tabs))
                self.tabs += '    '

                datatype = re.sub('_t$', '', top_struct_field.datatype)
                # check if the data type is a struct
                if datatype in self.c_structs.keys():
                    sub_field = self.c_structs[top_struct_field.datatype.replace('_t', '')]
                    if datatype not in  datastore.keys():
                        for item in sub_field:
                            self.add_item(datastore[top_struct_field.name][idx], item)
                        self.tabs = self.tabs[:-4]
                        self.h_file_handle.write("{}}},\n".format(self.tabs))
                    else:
                        self.parse_c_structs(top_struct_field.name, datastore[top_struct_field.name])
                        self.tabs = self.tabs[:-4]
                else:
                    self.add_item(datastore, top_struct_field)
                    self.tabs = self.tabs[:-4]
                    self.h_file_handle.write("{}}},\n".format(self.tabs))

            if top_struct_field.name in datastore.keys():
                if type(datastore[top_struct_field.name]) == list:
                    while {} in datastore[top_struct_field.name]:
                        datastore[top_struct_field.name].remove({})
                if not datastore[top_struct_field.name]:
                    del datastore[top_struct_field.name]
        self.tabs = self.tabs[:-4]

        if datastore:
            print("Error: dict values not assigned:{}\n".format(datastore))
        self.h_file_handle.write('{}}};\n'.format(self.tabs))

    def create_header_file(self, header_file):
        self.header_file = header_file
        output_header_file = self.json_file.replace('.json', '.h')
        datastore = json_to_dict(self.json_file)
        if self.debug_print:
            pprint.pprint(datastore)

        #if 'module_name' not in datastore:
        #    print("Error: missing module_name in dictionary")
        #    exit(1)
        top_struct = self.header_file[:-2]
        self.collect_c_structs()
        with open(output_header_file, 'w') as self.h_file_handle:
            header_file_underscore = self.header_file.replace('.', '_')
            self.h_file_handle.write('#ifndef {}\n#define {}\n\n'.format(header_file_underscore, header_file_underscore))
            self.h_file_handle.write("/* This is an autogenerated file, please don't modify it manually*/\n\n")
            self.h_file_handle.write("{}_t {} = {{\n".format(top_struct, top_struct))
            self.tabs = '    '
            self.parse_c_structs(top_struct, datastore)
            self.h_file_handle.write('\n#endif // {}\n'.format(header_file_underscore))

def select_process_channels(y_wav_data, channels_to_process):
    if channels_to_process is None:
        y_channel_count = len(y_wav_data)
    else:
        channels_to_process = np.asarray(channels_to_process)
        channels_to_process = channels_to_process[(channels_to_process >= 0) &\
                             (channels_to_process < len(y_wav_data))]
        y_channel_count = min(len(y_wav_data), len(channels_to_process))
        y_wav_data = y_wav_data[channels_to_process]
    return y_wav_data, y_channel_count
