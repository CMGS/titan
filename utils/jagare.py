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
    cache[node] = jagare
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

    def ls_tree(self, repo_path, path='', version='master'):
        try:
            params = '%s/%s/ls-tree/%s' % (self.node, repo_path, version)
            if path:
                params = '%s?path=%s' % (params, path)
            r = requests.get(params)
            result = self.get_result(r)
            if not result:
                return code.REPOS_LS_TREE_FAILED, None
            if result['error']:
                return result['message'], None
            if not result['data']:
                return code.REPOS_PATH_NOT_FOUND, None
            return None, result['data']
        except Exception:
            return code.UNHANDLE_EXCEPTION, None

    def cat(self, repo_path, sha):
        try:
            r = requests.get('%s/%s/cat/%s' % (self.node, repo_path, sha))
            if not r.ok:
                return code.REPOS_CAT_FILE_FAILED, None
            return None, r.text
        except Exception:
            return code.UNHANDLE_EXCEPTION, None

    def is_empty(self, repo_path):
        try:
            r = requests.get('%s/%s' % (self.node, repo_path))
            result = self.get_result(r)
            if not result or result['error']:
                return False
            return result['data']['is_empty']
        except Exception:
            return False

    def get_result(self, r):
        try:
            result = json.loads(r.text)
        except Exception:
            return None
        else:
            return result

