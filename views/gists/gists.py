#!/usr/local/bin/python2.7
#coding:utf-8

import logging

from utils.helper import MethodView

from query.gists import get_gist

logger = logging.getLogger(__name__)

class Create(MethodView):
    def get(self):
        return 'Hello World'

class View(MethodView):
    def get(self):
        return 'Hello World'

