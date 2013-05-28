#!/usr/local/bin/python2.7
#coding:utf-8

import logging

from flask.views import MethodView
from flask import redirect, request, url_for, render_template

from utils.account import login_required, account_login, \
        account_logout
from utils.validators import check_register_info, check_login_info
from query.account import create_user, get_user_by, clear_user_cache

logger = logging.getLogger(__name__)

class Register(MethodView):
    decorators = [login_required(need=False)]
    def get(self):
        return render_template('account.register.html')

    def post(self):
        username = request.form.get('name', None)
        password = request.form.get('password', None)
        email = request.form.get('email', None)
        check, error = check_register_info(username, email, password)
        if not check:
            return render_template('account.register.html', error=error)
        user = create_user(username, password, email)
        #clear cache
        clear_user_cache(user)
        account_login(user)
        return redirect(url_for('index'))

class Login(MethodView):
    decorators = [login_required(need=False)]
    def get(self):
        login_url = url_for('account.login', **request.args)
        return render_template('account.login.html', login_url=login_url)

    def post(self):
        login_url = url_for('account.login', **request.args)
        password = request.form.get('password', None)
        email = request.form.get('email', None)
        check, error = check_login_info(email, password)
        if not check:
            return render_template('account.login.html', login_info=error, login_url=login_url)

        user = get_user_by(email=email).limit(1).first()
        if not user:
            logger.info('no such user')
            return render_template('account.login.html', login_info='no such user', login_url=login_url)
        if not user.check_password(password):
            logger.info('invaild passwd')
            return render_template('account.login.html', login_info='invaild passwd', login_url=login_url)

        account_login(user)
        redirect_url = request.args.get('redirect', None)
        return redirect(redirect_url or url_for('index'))

class Logout(MethodView):
    def get(self):
        account_logout()
        return redirect(request.referrer or url_for('index'))

