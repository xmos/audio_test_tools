# Copyright (c) 2018-2019, XMOS Ltd, All rights reserved

import numpy as np


class stack_frame(object):

    def __init__(self, name, indexed = False):
        self.nm = name
        self.dex = (0 if indexed else None)

    @property
    def name(self):
        return self.nm

    @property
    def index(self):
        return self.dex

    def index_set(self, index):
        if(self.dex is None):
            raise Exception("Cannot increment index on unindexed scope frame.")
        self.dex = index

    def index_incr(self):
        if(self.dex is None):
            raise Exception("Cannot increment index on unindexed scope frame.")
        self.dex += 1

def fmt_complex(x): return "%0.032f+%0.032fj" % (x.real, x.imag)
def fmt_float(x):   return "%0.032f" % x
def fmt_int(x):     return "%d" % x

PRIMITIVE_MAP = {
    int: fmt_int,
    np.int32: fmt_int,

    float: fmt_float,
    np.float64: fmt_float,

    complex:       fmt_complex,
    np.complex128: fmt_complex
}


class scope_ctx_mgr(object):
    def __init__(self, ff):
        self.ff = ff
    def __enter__(self):
        return self.ff
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.ff.scope_pop()

class att_df(object):

    VERSION = 0

    def __init__(self):
        self.file = None
        self.stack = []

    def _full_scope(self, var_name, index = None):
        r = ""
        for i,frame in enumerate(self.stack):
            fname = frame.name
            fdex = frame.index
            
            a = fname if fname else ""
            b = "[%d]" % fdex if fdex is not None else ""
            c = "." if fname is not None else ""
            r += "%s%s%s" % (a,b,c)

        a = var_name
        b = "[%d]" % index if index is not None else ""
        c = ": "

        return "%s%s%s%s" % (r,a,b,c)

    def _dimensions(self, dims):
        return "<%s> " % ",".join(map(str, dim))

    def open(self, filename):
        self.file = open(filename, "w")
        self.file.write("!VERSION: %d\n" % att_df.VERSION)

    def close(self):
        self.file.close()

    def scope_push(self, name, indexed = False):
        self.stack.append(stack_frame(name, indexed))
        return scope_ctx_mgr(self)

    def scope_pop(self):
        self.stack.pop()

    def index_set(self, index):
        self.stack[-1].index_set(index)

    def index_increment(self):
        self.stack[-1].index_incr()

    def write_scalar(self, var_name, val, index = None):
        r = self._full_scope(var_name, index)
        r += PRIMITIVE_MAP[type(val)](val)
        r += "\n"
        self.file.write(r)

    def write_vector(self, vec_name, vector, index = None):
        r = self._full_scope(vec_name, index)
        r += "<%d> " % len(vector)

        if(len(vector) > 0):
            tp = type(vector[0])
            r += ", ".join(map(PRIMITIVE_MAP[tp],vector))
        r += "\n"
        self.file.write(r)

    def write_nd_array(self, a_name, array, index = None):
        length = np.product(array.shape)
        flattened = array.reshape(length)
        
        r = self._full_scope(a_name, index)
        r += "<%s> " % ",".join(map(str, array.shape))

        if(length > 0):
            tp = type(flattened[0])
            r += ", ".join(map(PRIMITIVE_MAP[tp],flattened))
        r += "\n"
        self.file.write(r)


