# Copyright (c) 2018-2019, XMOS Ltd, All rights reserved

from .debug_file import debug_file

import debug_file.utils as utils

import re
import numpy as np

regex_directive = re.compile(r"^!(.*): (.*)$")
regex_name_dims_value = re.compile(r"^(.*):( <(.+)>)? (.*)$")

parsible_types = {int, float, complex}

preferred_types = {np.int64, np.float64, np.complex128}

type_remap = {
    float: np.float64,
    int: np.int64,
    complex: np.complex128,
}

def parse_scalar(val_str):
    tmp = eval(val_str)
    # return type_remap[type(tmp)](val_str)
    assert(type(tmp) in parsible_types)
    return tmp

def parse_value(val_str, dims):
    if dims is None:
        return parse_scalar(val_str)

    length = np.product(dims)
    if(length == 0):
        return np.zeros(shape=dims)

    elms = val_str.split(",")

    #We'll use the first val to decide the type
    first = eval(elms[0])
    vtype = type(first)
    if vtype not in preferred_types:
        vtype = type_remap[vtype]
    
    elms = np.array(list(map(vtype, elms)))
    return elms.reshape(dims)
    
def _get_or_default(kwargs, name, default_value):
    return kwargs[name] if name in kwargs else default_value


class deferred_loader(utils.deferred_value_loader):
    def __init__(self, file, offset):
        super(deferred_loader, self).__init__()
        self.file = file
        self.offset = offset

    def read_file(self):
        was = self.file.tell()
        self.file.seek(self.offset)
        val_str = self.file.readline()
        self.file.seek(was)
        return val_str

    def load(self):
        return self.parse(self.read_file())
    
    def parse(self, val_str):
        raise NotImplementedError()

class loader(deferred_loader):
    def __init__(self, file, offset, dims):
        super(loader, self).__init__(file, offset)
        self.dims = dims
    def parse(self, val_str):
        return parse_value(val_str, self.dims)


class parser_base(object):
    def __init__(self, file, **kwargs):

        self.cache_loaded = _get_or_default(kwargs, 'cache_loaded', True)
        self.lazy_load = _get_or_default(kwargs, 'lazy_load', True)
        self.file = file
        self.df = debug_file(self.file, **kwargs)

        self.line_handlers = []

        self.register_line_handlers()

    def register_line_handlers(self):
        raise NotImplementedError()

    def parse_line(self, line, linestart):
        for check,handler in self.line_handlers:
            if check(line):
                handler(line=line, linestart=linestart)
                return

        raise Exception("Could not parse line: " + line)
        
    def parse_file(self, **kwargs):
        
        self.file.seek(0)

        linestart = self.file.tell()
        line = self.file.readline()

        while line != "":
            self.parse_line(line=line, linestart=linestart)
            linestart = self.file.tell()
            line = self.file.readline()

        return self.df


class parser(parser_base):
    
    def __init__(self, file, **kwargs):
        super(parser, self).__init__(file, **kwargs)

    def register_line_handlers(self):
        self.line_handlers += [
            (lambda x: x[0] == "!", self.parse_directive),
            (lambda x: x[0] == "#", self.parse_comment),
            #Trying to match the entry regex takes too long.
            (lambda x: True, self.parse_entry), 
        ]

    def parse_directive(self, line, **kwargs):
        match = regex_directive.match(line)
        self.df.handle_directive(match.group(1), match.group(2))

    def parse_comment(self, line, **kwargs):
        #do nothing with comments
        pass

    def parse_entry(self, line, linestart, **kwargs):
        # entry if it matches this regex
        match = regex_name_dims_value.match(line)

        target = match.group(1)
        dims = match.group(3)

        if dims is not None:
            dims = tuple(int(d) for d in dims.split(","))

        if self.lazy_load:
            vstart,_ = match.span(4)
            value = loader(self.file, vstart+linestart, dims)
        else:
            value = parse_value(match.group(4), dims)
        
        self.df[target] = value
