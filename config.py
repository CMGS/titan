#coding:utf-8

import os
import sys
import yaml

def init_config(config, local_config=None, reload=False):
    s = sys.modules[__name__]
    if not reload and getattr(s, '__initiated__', None):
        return
    c = yaml.load(open(config, 'r'))
    if local_config and os.path.isfile(local_config):
        c.update(yaml.load(open(local_config, 'r')))
    for k, v in c.iteritems():
        setattr(s, k ,v)
    setattr(s, '__initiated__', True)

