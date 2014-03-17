#!/usr/local/bin/python2.7
#coding:utf-8

from base import BaseHandler, WholeMatchMixIn
from application import StaticFilesApplication

class StaticFilesHandler(BaseHandler, WholeMatchMixIn):
    def make_app(self, config):
        return StaticFilesApplication(config['static_files'])

