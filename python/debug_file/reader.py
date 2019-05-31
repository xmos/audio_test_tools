# Copyright (c) 2018-2019, XMOS Ltd, All rights reserved


from .v0.parser import parser as parser_v0
import re

regex_version = re.compile(r"^!VERSION: (\d+)$")
    
parser_version_map = {
    0: parser_v0
}

def load_file(filepath, lazy_load = True, cache_loaded = True):
    file = open(filepath, 'r')
    line = file.readline()

    version = regex_version.match(line)
    if not version:
        raise Exception("First line of debug file must be a version directive.")

    version = int(version.group(1))
    parser_ver = parser_version_map[version]
    parser = parser_ver(file = file, 
                        lazy_load = lazy_load, 
                        cache_loaded = cache_loaded)

    return parser.parse_file()
