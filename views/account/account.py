#!/usr/local/bin/python2.7
#coding:utf-8

import logging
from datetime import datetime

from flask.views import MethodView
from flask import redirect, request, url_for, render_template, \
        abort, g

import config
from utils import code
from utils.account import login_required, account_login, \
        account_logout
from utils.validators import check_register_info, check_login_info
from query.account import create_user, get_user_by, clear_user_cache
from query.organization import create_members, get_verify_by_stub, \
        clear_organization_cache, get_member, get_organization_by_git, \
        create_organization, clear_verify_stub

logger = logging.getLogger(__name__)

class Register(MethodView):
    def get(self, stub):
        verify = self.get_verify(stub)
        # Logined and verify.email equal to user.email
        # auto join organization (auto create organization if needed)
        # if user if member, clear verify
        if g.current_user and g.current_user.email == verify.email:
            organization = self.join_organization(verify, g.current_user)
            return redirect(url_for('organization.view', git=organization.git))
        return self.render_template(verify)

    def post(self, stub):
        verify = self.get_verify(stub)
        reg_type = request.form.get('regtype', None)
        if reg_type == 'new':
            return self.new_register(verify)
        elif reg_type == 'bind':
            return self.bind(verify)
        else:
            raise abort(404)

    def get_verify(self, stub):
        verify = get_verify_by_stub(stub=stub)
        if not verify:
            raise abort(404)
        if (datetime.now()  - verify.created).seconds > config.VERIFY_STUB_EXPIRE:
            clear_verify_stub(verify)
            raise abort(403)
        return verify

    def is_member(self, oid, user):
        if not user:
            return False
        member = get_member(oid, user.id)
        if member:
            return True
        return False

    def render_template(self, verify, error=None):
        return render_template('account.register.html', verify=verify, error=error)

    def bind(self, verify):
        recv_email = request.form.get('recv_email', None)
        if g.current_user:
            user = g.current_user
        else:
            email = request.form.get('email', None)
            password = request.form.get('password', None)
            check, error = check_login_info(email, password)
            if not check:
                return self.render_template(verify, error)
            user = get_user_by(email=email).limit(1).first()
            if not user:
                return self.render_template(verify, code.ACCOUNT_NO_SUCH_USER)
            if not user.check_password(password):
                return self.render_template(verify, code.ACCOUNT_LOGIN_INFO_INVAILD)
        if verify.email != recv_email:
            return self.render_template(verify, code.ACCOUNT_REGISTER_EMAIL_INVAILD)
        organization = self.join_organization(verify, user)
        account_login(user)
        return redirect(url_for('organization.view', git=organization.git))

    def new_register(self, verify):
        username = request.form.get('name', None)
        password = request.form.get('password', None)
        email = request.form.get('email', None)
        check, error = check_register_info(username, email, password)
        if not check:
            return self.render_template(verify, error)
        if email != verify.email:
            return self.render_template(verify, code.ACCOUNT_REGISTER_EMAIL_INVAILD)
        user = create_user(username, password, email)
        # clear cache
        clear_user_cache(user)
        account_login(user)
        organization = self.join_organization(verify, user)
        return redirect(url_for('organization.view', git=organization.git))

    def join_organization(self, verify, user):
        organization = get_organization_by_git(verify.git)
        if not organization:
            # First member will be admin
            organization = create_organization(user, verify.name, verify.git, members=1, admin=1)
        if not self.is_member(organization.id, user):
            create_members(organization.id, user.id, verify.admin)
            organization.update_members(1)
            clear_organization_cache(organization, user)
        clear_verify_stub(verify)
        return organization

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

