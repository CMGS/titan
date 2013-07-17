#!/usr/local/bin/python2.7
#coding:utf-8

import base64
import logging
from flask import abort
from libs.jagare import Jagare
from libs.code import render_code

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

def format_content(jagare, repo, path, version='master', render=True):
    error, res = jagare.cat_file(repo.get_real_path(), path, version=version)
    if error:
        raise abort(error)

    content_type = res.headers.get('content-type', 'application/octet-stream')
    content_length = float(res.headers.get('content-length', 0.0)) / 1024

    if 'image' in content_type:
        content_type = 'image'
        content = lambda: base64.b64encode(res.content)
    elif 'text' in content_type:
        content_type = 'file'
        def _():
            c = res.content
            if not isinstance(c, unicode):
                c = c.decode('utf8')
            if render:
                c = render_code(path, c)
            return c
        content = _
    else:
        content_type = 'binary'
        content = lambda: res.content
    return content, content_type, content_length

