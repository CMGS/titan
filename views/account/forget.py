#!/usr/local/bin/python2.7
#coding:utf-8

import logging
from datetime import datetime

from flask import redirect, request, url_for, abort, g

import config
from utils import code
from utils.helper import MethodView
from utils.mail import async_send_mail
from utils.token import create_token
from utils.account import login_required
from utils.validators import check_email, check_password

from query.account import get_user_by_email, create_forget, \
        get_forget_by_stub, get_user, clear_user_cache, \
        check_uid_exists, clear_forget_stub

logger = logging.getLogger(__name__)

class Forget(MethodView):
    decorators = [login_required(need=False)]
    def get(self):
        if request.form and 'cancel' in request.form:
            return redirect(url_for('index'))
        return self.render_template()

    def post(self):
        if request.form and 'cancel' in request.form:
            return redirect(url_for('index'))
        email = request.form.get('email', None)
        status = check_email(email)
        if status:
            return self.render_template(error=status[1])
        user = get_user_by_email(email=email)
        if user and not check_uid_exists(user.id):
            stub = create_token(20)
            content = self.render_template(user=user, stub=stub)
            async_send_mail(user.email, code.EMAIL_FORGET_TITLE, content)
            create_forget(user.id, stub)
        return self.render_template(send=1)

class Reset(MethodView):
    def get(self, stub):
        forget = get_forget_by_stub(stub=stub)
        if g.current_user:
            clear_forget_stub(forget)
            return redirect(url_for('index'))

        if not forget:
            raise abort(404)

        if (datetime.now()  - forget.created).seconds > config.FORGET_STUB_EXPIRE:
            clear_forget_stub(forget)
            return self.render_template(error=code.ACCOUNT_FORGET_STUB_EXPIRED)
        return self.render_template()

    def post(self, stub):
        forget = get_forget_by_stub(stub=stub)
        if g.current_user:
            clear_forget_stub(forget)
            return redirect(url_for('index'))

        if not forget:
            raise abort(404)

        password = request.form.get('password', None)
        status = check_password(password)
        if status:
            return self.render_template(error=status[1])
        # TODO 考虑事物的一致性
        user = get_user(forget.uid)
        user.change_password(password)
        clear_forget_stub(forget)
        clear_user_cache(user)
        return redirect(url_for('account.login'))

