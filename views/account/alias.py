#!/usr/local/bin/python2.7
#coding:utf-8

from utils.helper import MethodView
from utils.account import login_required

class Alias(MethodView):
    decorators = [login_required('account.login')]
    def get(self):
        pass

    def post(self):
        pass

class VerifyAlias(MethodView):
    decorators = [login_required('account.login')]
    def get(self, stub):
        pass

class DelAlias(MethodView):
    decorators = [login_required('account.login')]
    def get(self, aid):
        pass

