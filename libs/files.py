#!/usr/bin/python
#coding:utf-8

import os
import logging
from shutil import copyfileobj

logger = logging.getLogger(__name__)

uploads_dir = os.path.join('permdir', '.uploads')

if not os.path.exists(uploads_dir):
        os.mkdir(uploads_dir)

uploaders = {}
def get_uploader(**kwargs):
    global uploaders
    key = tuple(kwargs.values())
    uploader = uploaders.get(key, None)
    if not uploader:
        uploader = LocalFileSystem(**kwargs)
        uploaders[key] = uploader
    return uploader

class LocalFileSystem(object):
    def __init__(self):
        self.prefix = uploads_dir

    def writeFile(self, path, data, auto = True, headers={}, metadata={}):
        try:
            path = os.path.join(self.prefix, path)
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

