#coding:utf-8

import os
import sys
import yaml

def init_config(config, local_config=None):
    c = yaml.load(open(config, 'r'))
    if local_config and os.path.isfile(local_config):
        c.update(yaml.load(open(local_config, 'r')))
    s = sys.modules[__name__]
    for k, v in c.iteritems():
        setattr(s, k ,v)

