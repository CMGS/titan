#!/usr/local/bin/python2.7
#coding:utf-8

import json
import requests
from utils import code
from config import JAGARE_NODES

def get_node(rid):
    #TODO consistent hash!
    return JAGARE_NODES[0]

cache = {}
def get_jagare(rid, parent=0):
    c = rid if not parent else parent
    node = get_node(c)
    if cache.get(node, None):
        return cache[node]
    jagare = Jagare(node)
    cache[node] = cache
    return jagare

class Jagare(object):
    def __init__(self, node):
        self.node = node

    def init(self, path):
        try:
            r = requests.post('%s/%s/init' % (self.node, path))
            result = self.get_result(r)
            if not result or result['error']:
                return False, code.REPOS_INIT_FAILED
            return True, None
        except Exception:
            return False, code.UNHANDLE_EXCEPTION

    def get_result(self, r):
        try:
            if not r.ok:
                return None
            result = json.loads(r.text)
        except Exception:
            return None
        else:
            return result

