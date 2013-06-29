#!/usr/local/bin/python2.7
#coding:utf-8

import json
import logging
import requests

from utils import code
from config import JAGARE_NODES

logger = logging.getLogger(__name__)

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
        except Exception, e:
            logger.exception(e)
            return False, code.UNHANDLE_EXCEPTION

    def ls_tree(self, repo_path, path='', version='master'):
        try:
            url = '%s/%s/ls-tree/%s' % (self.node, repo_path, version)
            params = {'path':path} if path else None
            r = requests.get(url, params=params)
            result = self.get_result(r)
            if not result:
                return code.REPOS_LS_TREE_FAILED, None
            if result['error']:
                return result['message'], None
            if not result['data']:
                return code.REPOS_PATH_NOT_FOUND, None
            return None, result['data']
        except Exception, e:
            logger.exception(e)
            return code.UNHANDLE_EXCEPTION, None

    def cat_file(self, repo_path, path, version='master'):
        try:
            r = requests.get(
                    '%s/%s/cat/p/%s' % (self.node, repo_path, version), \
                    params = {'path':path}, \
                    stream = True,
                )
            if not r.ok:
                return r.status_code, None
            return None, r
        except Exception, e:
            logger.exception(e)
            return 404, None

    def get_result(self, r):
        return json.loads(r.text)

