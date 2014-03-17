#!/usr/bin/python
#coding:utf-8

import config
from utils.helper import get_hash

def get_avatar(email, size):
    md5email = get_hash(email)
    query = "%s?s=%s%s" % (md5email, size, config.GRAVATAR_EXTRA)
    return '%s%s' % (config.GRAVATAR_BASE_URL, query)
