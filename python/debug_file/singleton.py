# Copyright (c) 2018-2019, XMOS Ltd, All rights reserved

from .writer import att_df

# These module functions allow you to not have to pass an instance of att_df around between objects or functions.

global instance
instance = None

class DoNothingCtxMgr(object):
    def __init__(self): pass
    def __enter__(self): return self
    def __exit__(self, exc_type, exc_val, exc_tb): pass
    def __getattribute__(self, att): 
        def func(*args, **kwargs):
            pass
        return func


def initialize(file):
    global instance
    instance = att_df()
    instance.open(file)

def deinitialize():
    if instance is not None:
        instance.close()

def scope_push(name, indexed = False):
    if instance is None: return DoNothingCtxMgr()
    return instance.scope_push(name, indexed)

def scope_pop():
    if instance is None: return 
    instance.scope_pop()

def index_set(index):
    if instance is None: return
    instance.index_set(index)

def index_increment():
    if instance is None: return
    instance.index_increment()

def write_scalar(var_name, val, index=None):
    if instance is None: return
    instance.write_scalar(var_name,val,index)

def write_vector(vec_name, vector, index=None):
    if instance is None: return
    instance.write_vector(vec_name,vector,index)

def write_nd_array(a_name, array, index=None):
    if instance is None: return
    instance.write_nd_array(a_name,array,index)

