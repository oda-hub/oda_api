from collections import OrderedDict
import hashlib
import pickle
import json
import os
import re
import logging

logger = logging.getLogger('oda_api.localcache')

def key_to_keyhash(key):
    return hashlib.md5(json.dumps(key, sort_keys=True).encode()).hexdigest()[:16]    

def keyhash_to_fn(key_hash):
    return f"cache/{key_hash}.pickle"

def store(key, r):
    fn = keyhash_to_fn(key_to_keyhash(key))
    os.makedirs(os.path.dirname(fn), exist_ok=True)
    pickle.dump(r, open(fn, "wb"))
    logger.info("writing to %s", fn)

def restore(key):
    fn = keyhash_to_fn(key_to_keyhash(key))
    logger.debug("loading from %s", fn)

    if not os.path.exists(fn):
        logger.debug("no file to load %s", fn)
        return None

    try:
        r = pickle.load(open(fn, 'rb'))
        logger.info("loaded something from %s", fn)
    except Exception as e:
        logger.warning("cache failed: corrupt entry in %s: %s", fn, e)
        return None
    
    return r

def call_to_fn(f, *args, **kwargs):
    return keyhash_to_fn(key_to_keyhash(call_to_key(f, *args, **kwargs)))

def call_to_key(f, *args, **kwargs):
    return (f.__name__, f_version(f), args, OrderedDict(kwargs))

def f_version(f):
    version = "default"
    if f.__doc__ is not None:
        r = re.search(r"version:(.*?)\n", f.__doc__, re.S)
        if r is not None:
            version = r.group(1).strip()
        
    logger.debug("function %s version %s", f.__name__, version)

    return version


def cached(f):
    """
    simple persistent cache decorator
    """    

    def nf(*args, **kwargs):
        version = f_version(f)

        key = call_to_key(f, *args, **kwargs)
        
        r = restore(key)

        if r is None:
            try:
                r = f(*args, **kwargs)
            except Exception as e:
                r = e

            store(key, r)
        
        logger.debug('stored result is not None')
        
        if isinstance(r, Exception):
            logger.info("stored result contains exception %s", r)
            raise r
        else:
            return r        
        
    return nf
