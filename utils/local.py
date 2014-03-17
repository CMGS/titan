#!/usr/bin/python
#coding:utf-8

import inspect

from utils.helper import get_environ
from libs.localmemcache import LocalMemcache

class NotExists(object):
    pass

class RequestCache(object):
    @property
    def _cache(self):
        environ = get_environ()
        return environ.setdefault('titan.reqcache', {})

    def set(self, key, value):
        self._cache[key] = value

    def get(self, key, default=None):
        return self._cache.get(key, default)

    def __call__(self, key_formatter):
        def deco(func):
            arg_names, varargs, varkw, defaults = inspect.getargspec(func)
            args = dict(zip(arg_names[-len(defaults):], defaults)) if defaults else {}
            if varargs or varkw:
                raise Exception("do not support varargs")
            def _(*a, **kw):
                if callable(key_formatter):
                    key = key_formatter(*a, **kw)
                else:
                    aa = args.copy()
                    aa.update(zip(arg_names, a))
                    aa.update(kw)
                    key = key_formatter.format(**aa)
                val = self.get(key, NotExists)
                if val is NotExists:
                    val = func(*a, **kw)
                    self.set(key, val)
                return val
            return _
        return deco

reqcache = RequestCache()
processcache = LocalMemcache()

