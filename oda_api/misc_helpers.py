import re
import hashlib
import json
from collections import OrderedDict

regex_url = re.compile(
                r'^https?://'  # http:// or https://
                r'[a-z0-9]([-a-z0-9]*[a-z0-9])?(\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*'  # domain...
                r'(?::\d+)?'  # optional port
                r'(?:/[a-z0-9/-]*)?$', re.IGNORECASE)


def validate_url(url):
    return regex_url.match(url) is not None


def clean_var_name(s):
    s = s.replace('-', 'm')
    s = s.replace('+', 'p')
    s = s.replace(' ', '_')

    # Remove invalid characters
    s = re.sub('[^0-9a-zA-Z_]', '', s)

    # Remove leading characters until we find a letter or underscore
    s = re.sub('^[^a-zA-Z_]+', '', s)

    return s


def make_hash(o):
    """
    Makes a hash from a dictionary, list, tuple or set to any level, that contains
    only other hashable types (including any lists, tuples, sets, and
    dictionaries).

    """

    def format_hash(x):
        return hashlib.md5(
            json.dumps(sorted(x)).encode()
        ).hexdigest()[:16]

    if isinstance(o, (set, tuple, list)):
        return format_hash(tuple(map(make_hash, o)))

    elif isinstance(o, (dict, OrderedDict)):
        return make_hash(tuple(o.items()))

    return format_hash(json.dumps(o))

