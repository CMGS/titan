#!/usr/local/bin/python2.7
#coding:utf-8

from models import db
from models.gists import Gists
from sheep.api.cache import cache, backend

@cache('gists:{gid}', 8640000)
def get_gist(gid):
    return Gists.query.get(gid)

