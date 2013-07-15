#!/usr/local/bin/python2.7
#coding:utf-8

from models import db
from models.gists import Gists

def get_gist(gid):
    return Gists.query.get(gid)

