
import debug_file.utils as utils

from functools import reduce
from itertools import starmap

TARGET_WILDCARD = "*"

def _get_or_default(kwargs, name, default_value):
    return kwargs[name] if name in kwargs else default_value

class metadata(object):
    def __init__(self):
        self.version = None

class df_scope_level(object):
    """
    df_scope_levels are basically wrappers around a dictionary of children.
    Targets/Key chains in an df_scope_level are always in normalized (list) form.
    """

    def __init__(self, cache_loaded = True):
        self.children = dict()
        self.cache_loaded = cache_loaded

    def _resolvechild(self, key):
        v = self.children[key]
        if not isinstance(v, utils.deferred_value_loader):
            return v
        
        v = v.load()
        if self.cache_loaded:
            self.children[key] = v

        return v

    def child_count(self):
        return len(self.children)

    def keys(self):
        return self.children.keys()

    def select_many(self, key_chain, resolve_values=True):
        key,subchain = key_chain[0],key_chain[1:]

        keys = self.children.keys() if (key == TARGET_WILDCARD) else [key]

        for k in keys:
            if subchain:
                child = self.children[k]

                cres = child.select_many(subchain, resolve_values=resolve_values)
                if resolve_values:
                    for kk,vv in cres:
                        yield ([k]+kk, vv)
                else:
                    for kk in cres:
                        yield [k]+kk
            else:
                yield ([k], self._resolvechild(k)) if resolve_values else [k]
                


    def __setitem__(self, key_chain, value):
        key,subchain = key_chain[0],key_chain[1:]

        if subchain:
            if key not in self.children:
                self.children[key] = df_scope_level(cache_loaded = self.cache_loaded)
            self.children[key][subchain] = value
        else:
            self.children[key] = value

    def __getitem__(self, key_chain):
        key,subchain = key_chain[0],key_chain[1:]

        if subchain:
            return (self.children[key])[subchain]
        else:
            return self._resolvechild(key)
            

class scope_level_view(object):
    """
    Users of this module should generally be interacting with the debug files through
    one of these. Targets can be specified in either standard or normalized form (dotted string or list)
    """
    def __init__(self, scope_level, parent_keys, root_view=None):
        self.scope_level = scope_level
        self.parent_keys = parent_keys
        self.root_view = root_view if root_view is not None else self

    def _get_raw(target):
        key = utils.normalize_target(key)
        return self.scope_level[key]
    def _get_scope(target):
        sl = self._get_raw(target)
        if not isinstance(sl, df_scope_level):
            raise Exception("Requested target is a leaf node.")
        return sl

    def root(self):
        return self.root_view

    def select_many(self, target, include_keys = True, include_values = True, **kwargs):
        standard_keys = _get_or_default(kwargs, 'standard_keys', False)
        index_keys    = _get_or_default(kwargs, 'index_keys', False)
        parent_keys = _get_or_default(kwargs, 'parent_keys', False)

        target = utils.normalize_target(target)

        cres = self.scope_level.select_many(target, resolve_values=include_values)

        for k in cres:
            k,v = k if include_values else (k,None)

            if(include_keys):
                k = self.parent_keys+k if parent_keys else k
                k = utils.standardize_target(k) if standard_keys else k
                k = utils.extract_indices(k) if index_keys else k
            
            if include_values:
                yield (k,v) if include_keys else v
            else:
                yield k


    def child_count(self, target):
        return self._get_scope(target).child_count()
    def keys(self, target):
        return self._get_scope(target).keys()
    def indices(self, target):
        return self._get_scope(target).keys()


    def __getitem__(self, key):
        key = utils.normalize_target(key)
        val = self.scope_level[key]
        if isinstance(val, df_scope_level):
            val = scope_level_view(val, key)
        return val

    def __setitem__(self, key, value):
        key = utils.normalize_target(key)
        self.scope_level[key] = value

class debug_file(scope_level_view):

    def __init__(self, file, cache_loaded = True, **kwargs):
        root = df_scope_level(cache_loaded = cache_loaded)
        super(debug_file, self).__init__(root, [])
        self.file = file
        self.meta = metadata()

    def __del__(self):
        self.close()

    def close(self):
        if self.file is not None:
            self.file.close()
            self.file = None

    def handle_directive(self, dname, dvalue):
        if(dname == "VERSION"):
            self.meta.version = int(dvalue)

        setattr(self.meta, dname, dvalue)



        