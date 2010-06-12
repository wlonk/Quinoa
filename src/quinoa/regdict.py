"""
This class is such a bad idea.
"""

import re

class RegDict(dict):
    """
    A dict designed to take regex objects as keys, and accept any key that
    maches a regex as an index.  This is *not* O(1), just a mapping.

    This is a many-to-many mapping, if you're not careful.  If multiple regexes
    match, which one will be used is not defined.  Don't be stupid.
    """
    def __contains__(self, key):
        for kt, v in self.items():
            k = kt[0]
            if k.match(key):
                return v
    def __getitem__(self, key):
        for kt, v in self.items():
            k = kt[0]
            if k.match(key):
                return v
    def __setitem__(self, key, value):
        if isinstance(key, basestring):
            rekey = re.compile(key)
        else:
            raise KeyError, "Use only strings as keys"
        dict.__setitem__(self, (rekey, key), value)
    def __unicode__(self):
        return "RegDict({%s})" % ', '.join("%s: %s" % (repr(kt[1]), v) \
                for kt, v in self.items())
    __str__ = __unicode__
    __repr__ = __unicode__
