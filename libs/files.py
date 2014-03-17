#!/usr/bin/python
#coding:utf-8

import os
import logging
from shutil import copyfileobj

logger = logging.getLogger(__name__)

uploaders = {}
def get_uploader(**kwargs):
    global uploaders
    path = kwargs['path']
    if not os.path.exists(path):
        logger.info('create upload dir %s' % path)
        os.mkdir(path)
    key = tuple(kwargs.values())
    uploader = uploaders.get(key, None)
    if not uploader:
        uploader = LocalFileSystem(**kwargs)
        uploaders[key] = uploader
    return uploader

class LocalFileSystem(object):
    def __init__(self, path):
        self.path = path

    def writeFile(self, path, data, auto = True, headers={}, metadata={}):
        try:
            path = os.path.join(self.path, path)
            dirs = os.path.dirname(path)
            if not os.path.exists(dirs):
                os.makedirs(dirs)
            with open(path, 'w') as f:
                if isinstance(data, file):
                    f.write(data.read())
                elif isinstance(data, basestring):
                    f.write(data)
                elif getattr(data, 'read'):
                    copyfileobj(data, f)
                else:
                    raise Exception('Not support')
                f.flush()
        except Exception:
            logger.exception('store file failed')
            return False
        else:
            logger.info('store in %s' % path)
            return True

def purge(*args):
    pass

