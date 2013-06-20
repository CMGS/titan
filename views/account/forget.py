#!/usr/local/bin/python2.7
#coding:utf-8

import logging

from flask import redirect, request, url_for, g
from flaskext.csrf import csrf_exempt

from utils import code
from utils.helper import MethodView
from utils.token import create_token
from utils.validators import check_email, check_password
from utils.account import login_required, send_forget_mail

from query.account import get_user_by_email, create_forget, \
        get_forget_by_stub, get_user, clear_forget, update_account

logger = logging.getLogger(__name__)

class Forget(MethodView):
    decorators = [login_required(need=False), csrf_exempt]
    def get(self):
        return self.render_template()

    def post(self):
        email = request.form.get('email', None)
        if not check_email(email):
            return self.render_template(error=code.ACCOUNT_EMAIL_INVAILD)
        user = get_user_by_email(email=email)
        if user:
            stub = create_token(20)
            forget, error = create_forget(user.id, stub)
            if error:
                return self.render_template(error=error)
            send_forget_mail(user, forget)
        return self.render_template(send=code.ACCOUNT_EMAIL_FORGET)

class Reset(MethodView):
    def get(self, stub):
        forget, error = get_forget_by_stub(stub=stub)
        if error:
            return redirect(url_for('index'))

        if g.current_user:
            clear_forget(forget)
            return redirect(url_for('index'))
        return self.render_template()

    def post(self, stub):
        forget, error = get_forget_by_stub(stub=stub)
        if error:
            return self.render_template(error=error)

        if g.current_user:
            clear_forget(forget)
            return redirect(url_for('index'))

        password = request.form.get('password', None)
        if not check_password(password):
            return self.render_template(error=code.ACCOUNT_PASSWORD_INVAILD)

        user = get_user(forget.uid)
        user, error = update_account(user, _forget=forget, password=password)
        if error:
            return self.render_template(error=error)
        return redirect(url_for('account.login'))

