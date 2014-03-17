#!/usr/bin/python
#coding:utf-8

from __future__ import absolute_import
import redis
import pickle
from redis import DataError

class Redis(redis.Redis):
    def hmset(self, name, mapping):
        """
        Sets each key in the ``mapping`` dict to its corresponding value
        in the hash ``name``
        """
        if not mapping:
            raise DataError("'hmset' with 'mapping' of length 0")
        items = []
        for pair in mapping.iteritems():
            items.extend([str(pair[0]), pickle.dumps(pair[1])])
        return self.execute_command('HMSET', name, *items)

    def hgetall(self, name):
        "Return a Python dict of the hash's name/value pairs"
        results = {}
        for k, v in self.execute_command('HGETALL', name).iteritems():
            results[k] = pickle.loads(v)
        return results

