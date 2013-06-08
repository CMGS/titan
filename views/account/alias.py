#!/usr/local/bin/python2.7
#coding:utf-8

import config
from flask import request, url_for, g, redirect
from itsdangerous import TimestampSigner, URLSafeSerializer
from query.account import get_alias_by_uid, create_alias, \
        get_alias_by_email, get_alias_by_id, clear_alias_cache
from utils import code
from utils.helper import MethodView
from utils.validators import check_email
from utils.account import login_required, send_verify_mail

class Alias(MethodView):
    decorators = [login_required('account.login')]
    def get(self):
        error = request.args.get('error', None)
        return self.render_template(error)

    def post(self):
        email = request.form.get('email', None)
        if not check_email(email):
            return self.render_template(error=code.ACCOUNT_EMAIL_INVAILD)
        if get_alias_by_email(email):
            return redirect(url_for('account.alias', error=code.ACCOUNT_EMAIL_EXISTS))
        url = url_for('account.verifyalias', stub=self.encode(email), _external=True)
        send_verify_mail(email, url)
        return self.render_template(send=code.ACCOUNT_EMAIL_VERIFY)

    def render_template(self, error=None, send=None):
        alias = get_alias_by_uid(g.current_user.id)
        return MethodView.render_template(self, alias=alias, send=send, error=error)

    def encode(self, email):
        s = TimestampSigner(config.SECRET_KEY)
        e = s.sign(email)
        s = URLSafeSerializer(config.SECRET_KEY)
        e = s.dumps(e)
        return e

class VerifyAlias(MethodView):
    decorators = [login_required('account.login')]
    def get(self, stub):
        email = self.decode(stub)
        if not email:
            return redirect(url_for('account.alias', error=code.ACCOUNT_EMAIL_STUB_EXPIRED))
        if get_alias_by_email(email):
            return redirect(url_for('account.alias', error=code.ACCOUNT_EMAIL_EXISTS))
        alias, error = create_alias(g.current_user, email)
        return redirect(url_for('account.alias', error=error))

    def decode(self, stub):
        try:
            s = URLSafeSerializer(config.SECRET_KEY)
            e = s.loads(stub)
            s = TimestampSigner(config.SECRET_KEY)
            e = s.unsign(e, max_age=config.VERIFY_STUB_EXPIRE)
            return e
        except Exception:
            return None

class DelAlias(MethodView):
    decorators = [login_required('account.login')]
    def get(self, aid):
        alias = get_alias_by_id(aid)
        if alias or alias.uid == g.current_user.id:
            alias.delete()
            clear_alias_cache(g.current_user, alias.email, aid)
        return redirect(url_for('account.alias'))

