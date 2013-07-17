#!/usr/local/bin/python2.7
#coding:utf-8

import logging
from flask import abort, g
from functools import wraps
from query.gists import get_gist

logger = logging.getLogger(__name__)

def gist_require(owner=False):
    def _gist_require(f):
        @wraps(f)
        def _(organization, member, *args, **kwargs):
            gid = kwargs.pop('gid', None)
            if not gid:
                raise abort(404)
            gist = get_gist(gid)
            if not gist:
                raise abort(404)
            if owner and (g.current_user.id != gist.uid or not member.admin):
                raise abort(403)
            return f(organization, member, gist, *args, **kwargs)
        return _
    return _gist_require

