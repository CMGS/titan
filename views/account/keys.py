#!/usr/local/bin/python2.7
#coding:utf-8

from flask import request
from utils.helper import MethodView
from utils.account import login_required
from query.account import get_keys_by_uid

class Keys(MethodView):
    decorators = [login_required('account.login')]
    def get(self):
        keys = get_keys_by_uid(g.current_user.id)
        return self.render_template(keys=keys)

    def post(self):
        key = request.form.get('key', None)
        usage = request.form.get('usage', None)

class DelKey(MethodView):
    decorators = [login_required('account.login')]
    def post(self, kid):
        pass

