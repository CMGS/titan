#!/usr/local/bin/python2.7
#coding:utf-8

import time
import sys
from itertools import izip
from cPickle import dumps

class LocalMemcache(object):

    def __init__(self):
        self.dataset = {}

    def set(self, key, val, expire_secs=0, compress=True):
        self.dataset[key] = val
        return 1

    def set_multi(self, values, expire_secs=0, compress=True):
        self.dataset.update(values)
        return 1

    def delete(self, key, timeout=0):
        if key in self.dataset:
            del self.dataset[key]
        return 1    

    def delete_multi(self, keys):
        for k in keys:
            self.delete(k)
        return True

    def get(self, key):
        return self.dataset.get(key)

    def get_raw(self, key):
        raise NotImplementedError()

    def get_multi(self, keys):
        rets = {}
        for k in keys:
            r = self.dataset.get(k)
            if r is not None:
                rets[k] = r
        return rets    

    def get_list(self, keys):
        return [self.dataset.get(k) for k in keys]

    def incr(self, key, val=1):
        raise NotImplementedError()

    def decr(self, key, val=1):
        raise NotImplementedError()

    def clear(self):
        self.dataset.clear()

    def get_last_error(self):
        return 0

class FakeMemcacheClient(object):
    def set(self, key, val, expire_secs=0, compress=True):
        return 1

    def set_multi(self, values, expire_secs=0, compress=True):
        return 1

    def delete(self, key, timeout=0):
        return 1

    def delete_multi(self, keys):
        return 1

    def get(self, key):
        return None

    def get_raw(self, key):
        return None

    def get_multi(self, keys):
        return {}

    def get_list(self, keys):
        return [None] * len(keys)

    def incr(self, key, val=1):
        return 0

    def decr(self, key, val=1):
        return 0

    def clear(self):
        return

    def close(self):
        return

    def get_last_error(self):
        return 0

    def prepend_multi(self, *args, **kws):
        return

    def append(self, *args, **kws):
        return

    def add(self, *args, **kws):
        return 1

class LogMemcache:
    def __init__(self, mc):
        self.mc = mc

    def dumps(self, val):
        if val is None:
            return ''
        if isinstance(val, basestring):
            pass
        elif isinstance(val, int) or isinstance(val, long):
            val = str(val)
        else:
            val = dumps(val, -1)
        return val

    def log(self, s):
        print >> sys.stderr, "[%s] memcache %s" % (
                time.strftime("%Y-%m-%d %H:%M:%S"), s)

    def set(self, key, val, expire_secs=0):
        self.log("set %r:%d" % (key, len(self.dumps(val))))
        return self.mc.set(key, val, expire_secs)

    def delete(self, key, timeout=0):
        self.log("delete %r" % key)
        return self.mc.delete(key, timeout)

    def get(self, key):
        val = self.mc.get(key)
        self.log("get %r:%d" % (key, len(self.dumps(val))))
        return val

    def get_multi(self, keys):
        vals = self.mc.get_multi(keys)
        self.log("get_multi %s" % (", ".join(
            "%r:%d" % (k, len(self.dumps(v)))
            for k, v in vals.iteritems())))
        return vals

    def get_list(self, keys):
        vals = self.mc.get_list(keys)
        self.log("get_list %s" % (", ".join(
            "%r:%d" % (k, len(self.dumps(v)))
            for k, v in izip(keys, vals))))
        return vals

    def incr(self, key, val=1):
        self.log("incr %r" % key)
        return self.mc.incr(key, val)

    def decr(self, key, val=1):
        self.log("decr %r" % key)
        return self.mc.decr(key, val)

    def close(self):
        self.mc.close()

