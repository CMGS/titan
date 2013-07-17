#!/usr/local/bin/python2.7
#coding:utf-8

import logging
from flask import abort
from functools import wraps
from query.gists import get_gist

logger = logging.getLogger(__name__)

def gist_require(f):
    @wraps(f)
    def _(organization, member, *args, **kwargs):
        gid = kwargs.pop('gid', None)
        if not gid:
            raise abort(404)
        gist = get_gist(gid)
        if not gist:
            raise abort(404)
        return f(organization, member, gist, *args, **kwargs)
    return _

