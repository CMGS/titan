#!/usr/local/bin/python2.7
#coding:utf-8

from utils.helper import MethodView
from utils.account import login_required

class Alias(MethodView):
    decorators = [login_required('account.login')]
    def get(self):
        return self.render_template()

    def post(self):
        pass

    def render_template(self, error=None):
        keys = get_keys_by_uid(g.current_user.id)
        return MethodView.render_template(self, keys=keys, printer=get_fingerprint, error=error)

class VerifyAlias(MethodView):
    decorators = [login_required('account.login')]
    def get(self, stub):
        pass

class DelAlias(MethodView):
    decorators = [login_required('account.login')]
    def get(self, aid):
        pass

