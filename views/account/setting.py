#!/usr/local/bin/python2.7
#coding:utf-8

from flask import g, request

from utils import code
from utils.helper import MethodView
from utils.account import login_required, account_login
from utils.validators import check_password, check_domain, \
        check_username

from query.account import get_current_user, update_account

class Setting(MethodView):
    decorators = [login_required('account.login', redirect='/account/setting/')]
    def get(self):
        return self.render_template()

    def post(self):
        user = g.current_user
        username = request.form.get('name', None)
        password = request.form.get('password', None)
        domain = request.form.get('domain', None)
        city = request.form.get('city', '')
        title = request.form.get('title', '')

        attrs = {}

        if username != user.name:
            status = check_username(username)
            if status:
                return self.render_template(error=status[1])
            attrs['name'] = username

        if domain and not user.domain:
            status = check_domain(domain)
            if status:
                return self.render_template(error=status[1])
            attrs['domain'] = domain

        if password:
            status = check_password(password)
            if status:
                return self.render_template(error=status[1])
            attrs['password'] = password

        attrs['city'] = city
        attrs['title'] = title

        update_account(user, **attrs)

        #relogin
        account_login(user)
        g.current_user = get_current_user()
        return self.render_template(error=code.ACCOUNT_SETTING_SUCCESS)

