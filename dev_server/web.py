#!/usr/local/bin/python2.7
#coding:utf-8

import sys
import logging
from threading import Lock

from gunicorn import util

from base import BaseHandler, WholeMatchMixIn

_LAZY_LOAD_LOCK = Lock()

class LazyLoader(object):

    def __init__(self, func, obj, config):
        self._app = None
        self._func = func
        self._obj = obj
        self._config = config

    def __call__(self, *a, **kw):
        if self._app is None:
            with _LAZY_LOAD_LOCK:
                if self._app is None:
                    try:
                        self._app = self._func(self._obj, self._config)
                    except Exception:
                        logging.exception("load handler failed")
                        self.traceback = sys.exc_info()
                        def _(e, sr):
                            exc_type, exc_value, tb = self.traceback
                            raise exc_type, exc_value, tb
                        self._app = _
        return self._app(*a, **kw)

def lazy():
    def deco(f):
        def _(obj, config):
            return LazyLoader(f, obj, config)
        return _
    return deco

class WSGIAppHandler(BaseHandler, WholeMatchMixIn):
    @lazy()
    def make_app(self, config):
        return util.import_app(config['wsgi_app'])

