
import numpy as np
import re
from functools import reduce

regex_replace_indices = re.compile(r"\[(.+?)\]")


def _try_int(x):
    try:    return int(x)
    except: return x

def _normalize_standard_target(standard_target):
    ts = regex_replace_indices.sub(lambda x: ".%s" % x.group(1), standard_target).split(".")
    return list(map(_try_int, ts))

def normalize_target(target):
    """
    Convert from standard to normalized form, if it is not already normalized.
    e.g. normalize_target("frame[20].something[2][4].val") -> ["frame", 20, "something", 2, 4, "val"]
    """
    if isinstance(target, str):
        return _normalize_standard_target(target)
    if isinstance(target, list):
        return target
    raise ValueError()

def _consolidate_indices(state, x):
    if isinstance(x, int):
        state[-1] = "%s[%d]" % (state[-1], x)
    else:
        state.append(x)
    return state

def standardize_target(target_list):
    """
    Convery target from normalized form to standard form.
    e.g. standardize_target(["frame", 20, "something", 2, 4, "val"]) -> "frame[20].something[2][4].val"
    """
    r = reduce(_consolidate_indices, target_list, [])
    return ".".join(r)


def extract_indices(normalized_target):
    """
    Extract all indices from a normalized scope target. Indices are any scope levels which are integers. 
    Note: This will not extract wildcarded indices.
    """
    return tuple(x for x in normalized_target if isinstance(x, int))


def big_array(debug_file, target, value_shape, dtype=np.float64):
    """
    Extract multiple entries from the debug_file and form them into one large numpy array.
    """
    if isinstance(value_shape,int):
        value_shape = [value_shape]

    dexes = list(debug_file.select_many(target, include_values=False, index_keys=True))

    mins = np.min(dexes, axis=0)
    maxes = np.max(dexes, axis=0)
    counts = map(lambda f,l: l-f+1, mins, maxes)

    res = np.zeros(shape=list(counts)+list(value_shape), dtype=dtype)

    for inds,val in debug_file.select_many(target, index_keys=True):
        res[inds] = val

    return res 

class deferred_value_loader(object):
    def __init__(self):
        super(deferred_value_loader, self).__init__()
    def load(self):
        raise NotImplementedError()
