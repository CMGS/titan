#!/usr/local/bin/python2.7
#coding:utf-8

import hashlib
import logging

from flask.views import MethodView
from flask import redirect, request, url_for, render_template, \
        abort

from utils import code
from utils.account import login_required, account_login, \
        account_logout
from utils.validators import check_register_info, check_login_info, \
        check_org_token
from query.account import create_user, get_user_by, clear_user_cache
from query.organization import get_org_by_token, create_members, \
        clear_organization_cache

logger = logging.getLogger(__name__)

class Register(MethodView):
    decorators = [login_required(need=False)]
    def get(self):
        self.get_token()
        return render_template('account.register.html')

    def post(self):
        reg_type = request.form.get('regtype', None)
        if reg_type == 'new':
            return self.new_register()
        elif reg_type == 'bind':
            return self.bind()
        else:
            raise abort(404)

    def get_token(self):
        token = request.args.get('token')
        if not token or not check_org_token(token):
            raise abort(403)
        if len(token) == 8:
            return token, ''
        return token[:8], token[8:]

    def bind(self):
        org_token, reg_token = self.get_token()
        password = request.form.get('password', None)
        email = request.form.get('email', None)
        recv_email = request.form.get('recv_email', None)
        check, error = check_login_info(email, password)
        if not check:
            return render_template('account.register.html', error=error)
        if reg_token and not self.check_vaild(org_token, reg_token, recv_email):
            return render_template('account.register.html', error=code.ACCOUNT_REGISTER_EMAIL_INVAILD)

        user = get_user_by(email=email).limit(1).first()
        if not user:
            logger.info('no such user')
            return render_template('account.register.html', error=code.ACCOUNT_NO_SUCH_USER)
        if not user.check_password(password):
            logger.info('invaild passwd')
            return render_template('account.register.html', error=code.ACCOUNT_LOGIN_INFO_INVAILD)

        account_login(user)
        self.join_organization(org_token, reg_token, user)
        return redirect(url_for('index'))

    def new_register(self):
        org_token, reg_token = self.get_token()
        username = request.form.get('name', None)
        password = request.form.get('password', None)
        email = request.form.get('email', None)
        check, error = check_register_info(username, email, password)
        if not check:
            return render_template('account.register.html', error=error)
        if reg_token and  not self.check_vaild(org_token, reg_token, email):
            return render_template('account.register.html', error=code.ACCOUNT_REGISTER_EMAIL_INVAILD)
        user = create_user(username, password, email)
        # clear cache
        clear_user_cache(user)
        account_login(user)
        organization = self.join_organization(org_token, reg_token, user)
        return redirect(url_for('organization.view', oid=organization.id))

    def join_organization(self, org_token, reg_token, user):
        organization = get_org_by_token(org_token)
        admin = 1 if not reg_token else 0
        create_members(organization.id, user.id, admin)
        organization.update_members(1)
        clear_organization_cache(organization, user)
        return organization

    def check_vaild(self, org_token, reg_token, email):
        m = hashlib.new('md5', '%s%s' % (email, org_token))
        if m.hexdigest() != reg_token:
            return False
        return True

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
            return render_template('account.login.html', login_info=code.ACCOUNT_NO_SUCH_USER, login_url=login_url)
        if not user.check_password(password):
            logger.info('invaild passwd')
            return render_template('account.login.html', login_info=code.ACCOUNT_LOGIN_INFO_INVAILD, login_url=login_url)

        account_login(user)
        redirect_url = request.args.get('redirect', None)
        return redirect(redirect_url or url_for('index'))

class Logout(MethodView):
    def get(self):
        account_logout()
        return redirect(request.referrer or url_for('index'))

