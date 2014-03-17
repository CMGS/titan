#!/usr/bin/python
#coding:utf-8

import re
import time
import redis
import common
import config
import inspect
import logging
from functools import wraps

from werkzeug.contrib import cache

client = redis.Redis(connection_pool=common.cache_pool)

backend = cache.RedisCache(
        host=client, \
        default_timeout=config.CACHE_DEFAULT_TIMEOUT, \
        key_prefix=config.CACHE_PREFIX)

ONE_HOUR = 3600
ONE_DAY = 86400
ONE_WEEK = 604800

logger = logging.getLogger(__name__)

old_pattern = re.compile(r'%\w')
new_pattern = re.compile(r'\{(\w+(\.\w+|\[\w+\])?)\}')

__formaters = {}

def gen_key(key_pattern, arg_names, defaults, *a, **kw):
    return gen_key_factory(key_pattern, arg_names, defaults)(*a, **kw)

def gen_key_factory(key_pattern, arg_names, defaults):
    args = dict(zip(arg_names[-len(defaults):], defaults)) if defaults else {}
    if callable(key_pattern):
        names = inspect.getargspec(key_pattern)[0]
    def gen_key(*a, **kw):
        aa = args.copy()
        aa.update(zip(arg_names, a))
        aa.update(kw)
        if callable(key_pattern):
            key = key_pattern(*[aa[n] for n in names])
        else:
            key = format(key_pattern, *[aa[n] for n in arg_names], **aa)
        return key and key.replace(' ','_'), aa
    return gen_key

def cache(key_pattern, expire=ONE_DAY, max_retry=0):
    def deco(f):
        arg_names, varargs, varkw, defaults = inspect.getargspec(f)
        if varargs or varkw:
            raise Exception("do not support varargs")
        gen_key = gen_key_factory(key_pattern, arg_names, defaults)
        @wraps(f)
        def _(*a, **kw):
            key, args = gen_key(*a, **kw)
            if not key:
                return f(*a, **kw)
            logger.info('get key %s', key)
            try:
                if isinstance(key, unicode):
                    key = key.encode('utf8')
                r = backend.get(key)
            except Exception, e:
                logger.exception(e)
                return f(*a, **kw)

            # anti miss-storm
            retry = max_retry
            while r is None and retry > 0:
                # when node is down, add() will failed
                if backend.add(key + '#mutex', 1, int(max_retry * 0.1)):
                    break
                time.sleep(0.1)
                r = backend.get(key)
                retry -= 1

            if r is None:
                r = f(*a, **kw)
                if r is not None:
                    logger.info('set key %s', key)
                    backend.set(key, r, expire)
                if max_retry > 0:
                    backend.delete(key + '#mutex')
            return r
        _.original_function = f
        return _
    return deco

def pcache(key_pattern, count=300, expire=ONE_DAY, max_retry=0):
    def deco(f):
        arg_names, varargs, varkw, defaults = inspect.getargspec(f)
        if varargs or varkw:
            raise Exception("do not support varargs")
        if not ('limit' in arg_names):
            raise Exception("function must has 'limit' in args")
        gen_key = gen_key_factory(key_pattern, arg_names, defaults)
        @wraps(f)
        def _(*a, **kw):
            key, args = gen_key(*a, **kw)
            start = args.pop('start', 0)
            limit = args.pop('limit')
            if not key or limit is None or start+limit > count:
                return f(*a, **kw)

            force = kw.pop('force', False)
            r = backend.get(key) if not force else None
            # anti miss-storm
            retry = max_retry
            while r is None and retry > 0:
                # when node is down, add() will failed
                if backend.add(key + '#mutex', 1, int(max_retry * 0.1)):
                    break
                time.sleep(0.1)
                r = backend.get(key)
                retry -= 1

            if r is None:
                r = f(start=0, limit=count, **args)
                backend.set(key, r, expire)
            return r[start:start+limit]
        _.original_function = f
        return _
    return deco

def npcache(key_pattern, count=300, expire=ONE_DAY):
    def deco(f):
        arg_names, varargs, varkw, defaults = inspect.getargspec(f)
        if varargs or varkw:
            raise Exception("do not support varargs")
        if not ('limit' in arg_names):
            raise Exception("function must has 'limit' in args")
        gen_key = gen_key_factory(key_pattern, arg_names, defaults)
        @wraps(f)
        def _(*a, **kw):
            key, args = gen_key(*a, **kw)
            start = args.pop('start', 0)
            limit = args.pop('limit')
            if not key or limit is None or start+limit > count:
                return f(*a, **kw)

            n = 0
            force = kw.pop('force', False)
            d = backend.get(key) if not force else None
            if d is None:
                n, r = f(start=0, limit=count, **args)
                backend.set(key, (n, r), expire)
            else:
                n, r = d
            return (n, r[start:start+limit])
        _.original_function = f
        return _
    return deco

def format(text, *a, **kw):
    f = __formaters.get(text)
    if f is None:
        f = formater(text)
        __formaters[text] = f
    return f(*a, **kw)

def formater(text):
    """
    >>> format('%s %s', 3, 2, 7, a=7, id=8)
    '3 2'
    >>> format('%(a)d %(id)s', 3, 2, 7, a=7, id=8)
    '7 8'
    >>> format('{1} {id}', 3, 2, a=7, id=8)
    '2 8'
    >>> class Obj: id = 3
    >>> format('{obj.id} {0.id}', Obj(), obj=Obj())
    '3 3'
    """
    def translator(k):
        if '.' in k:
            name,attr = k.split('.')
            if name.isdigit():
                k = int(name)
                return lambda *a, **kw: getattr(a[k], attr)
            return lambda *a, **kw: getattr(kw[name], attr)
        else:
            if k.isdigit():
                return lambda *a, **kw: a[int(k)]
            return lambda *a, **kw: kw[k]
    args = [translator(k) for k,_1 in new_pattern.findall(text)]
    if args:
        if old_pattern.findall(text):
            raise Exception('mixed format is not allowed')
        f = new_pattern.sub('%s', text)
        def _(*a, **kw):
            return f % tuple([k(*a,**kw) for k in args])
        return _
    elif '%(' in text:
        return lambda *a, **kw: text % kw 
    else:
        n = len(old_pattern.findall(text))
        return lambda *a, **kw: text % tuple(a[:n])

