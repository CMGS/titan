#!/usr/local/bin/python2.7
#coding:utf-8

from flask import request, redirect, url_for, g

from utils import code
from utils.helper import MethodView
from utils.account import login_required, get_key, \
        get_pubkey_finger, get_fingerprint
from utils.validators import check_key_usage
from query.account import get_keys_by_uid, create_key

class Keys(MethodView):
    decorators = [login_required('account.login')]
    def get(self):
        keys = get_keys_by_uid(g.current_user.id)
        return self.render_template(keys=keys, printer=get_fingerprint)

    def post(self):
        key = request.form.get('key', None)
        usage = request.form.get('usage', None)
        key = get_key(key)
        if not key:
            return self.render_template(error=code.ACCOUNT_KEY_INVAILD)
        if check_key_usage(usage):
            return self.render_template(error=code.ACCOUNT_USAGE_INVAILD)
        finger = get_pubkey_finger(key)
        key, error = create_key(g.current_user, usage, key, finger)
        if error:
            return self.render_template(error=error)
        return redirect(url_for('account.keys'))

class DelKey(MethodView):
    decorators = [login_required('account.login')]
    def post(self, kid):
        pass

