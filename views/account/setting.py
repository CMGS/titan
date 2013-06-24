#!/usr/local/bin/python2.7
#coding:utf-8

from flask import g, request

from utils import code
from utils.helper import MethodView
from utils.account import login_required, account_login
from utils.validators import check_password, check_display

from query.account import get_current_user, update_account

class Setting(MethodView):
    decorators = [login_required('account.login')]
    def get(self):
        return self.render_template()

    def post(self):
        user = g.current_user
        password = request.form.get('password', None)
        display = request.form.get('display', None)
        city = request.form.get('city', '')
        title = request.form.get('title', '')

        attrs = {}

        if display != user.display:
            status = check_display(display)
            if not status:
                return self.render_template(error=code.ACCOUNT_USERNAME_INVAILD)
            attrs['display'] = display

        if password:
            status = check_password(password)
            if not status:
                return self.render_template(error=code.ACCOUNT_PASSWORD_INVAILD)
            attrs['password'] = password

        attrs['city'] = city
        attrs['title'] = title

        error = update_account(user, **attrs)
        if error:
            return self.render_template(error=error)

        #relogin
        account_login(user)
        g.current_user = get_current_user()
        return self.render_template(error=code.ACCOUNT_SETTING_SUCCESS)

