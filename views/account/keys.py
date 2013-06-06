#!/usr/local/bin/python2.7
#coding:utf-8

from utils.helper import MethodView
from utils.account import login_required

class Keys(MethodView):
    decorators = [login_required('account.login')]
    def get(self):
        return self.render_template()

    def post(self):
        pass

class DelKey(MethodView):
    decorators = [login_required('account.login')]
    def post(self, kid):
        pass

