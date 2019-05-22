# Copyright (c) 2019, XMOS Ltd, All rights reserved
""" This module contains common util functions used by all the VTB libs """

from __future__ import division
from __future__ import print_function

import os
import configparser
import ast

def att_convert_ini_file_to_dict(config_file, section, print_param=1):
    """ Parse a section in an ini file, convert the parameters to
        the expected type using AST and return the dictionary with the parameters

    Args:
        config_file: path of the file to parse
        section: section to parse
        print_param: flag to print parsed parameters, 1 by default

    Returns:
        Dictionary of parameters with values in the expected data type
    """

    if os.path.isfile(config_file):
        print("Reading {} file".format(config_file))
    else:
        print("Error: {} not found".format(config_file))
        exit(1)
    config_params = configparser.ConfigParser()
    config_params.read(config_file)
    if section not in config_params.sections():
        print("Error: section {} not found".format(section))
        exit(2)

    #parameters_str = config_params._sections[section]
    parameters_str = config_params[section]

    # Interpret the parameters using the AST module
    parameters_dict = {}
    for item_name in parameters_str:
        parameters_dict[item_name] = ast.literal_eval(parameters_str[item_name])
        if print_param:
            print("{}: {}".format(item_name, parameters_dict[item_name]))
    return parameters_dict


import json

def json_to_dict(config_file, print_param=False):
    datastore = None
    with open(config_file, "r") as f:
        json_string = f.read()
        datastore = json.loads(json_string)
        f.close()
    return datastore

def dict_to_json(config_dict, config_file, print_param=False):
    json_dump = json.dumps(config_dict, indent=4)
    with open(config_file, "w") as f:
        f.write(json_dump)
        f.close()





