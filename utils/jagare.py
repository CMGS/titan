#!/usr/local/bin/python2.7
#coding:utf-8

import logging
from libs.jagare import Jagare

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

