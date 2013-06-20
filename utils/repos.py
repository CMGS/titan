#!/usr/local/bin/python2.7
#coding:utf-8

from config import JAGARE_NODES

def get_node(rid):
    #TODO consistent hash!
    return JAGARE_NODES[0]

class Jagare(object):
    def __init__(self, node):
        self.node = node

    def rpc(api, method, data):
        pass

