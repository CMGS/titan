#!/usr/local/bin/python2.7
#coding:utf-8

import logging
from flask import abort, g
from functools import wraps
from query.gists import get_gist, get_gist_by_private

logger = logging.getLogger(__name__)

def gist_require(owner=False):
    def _gist_require(f):
        @wraps(f)
        def _(organization, member, *args, **kwargs):
            gid = kwargs.pop('gid', None)
            private = kwargs.get('private', None)
            if not gid and not private:
                raise abort(404)
            gist = get_gist(gid) if gid else get_gist_by_private(private)
            if not gist:
                raise abort(404)
            if owner and g.current_user.id != gist.uid and not member.admin:
                raise abort(403)
            return f(organization, member, gist, *args, **kwargs)
        return _
    return _gist_require

