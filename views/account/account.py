#!/usr/local/bin/python2.7
#coding:utf-8

import logging

from flask import redirect, request, url_for, abort, g

from utils import code
from utils.helper import MethodView
from utils.account import login_required, account_login, \
        account_logout
from utils.validators import check_register_info, check_login_info
from query.account import create_user, get_user_by
from query.organization import create_members, get_verify_by_stub, \
        get_organization_by_git, create_organization

logger = logging.getLogger(__name__)

class Register(MethodView):
    def get(self, stub):
        verify = self.get_verify(stub)
        # if logined auto join organization (auto create organization if needed)
        # if user if member, clear verify
        if g.current_user:
            return self.join_organization(verify, g.current_user)
        return self.render_template(verify=verify)

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
        verify, error = get_verify_by_stub(stub=stub)
        if not verify:
            raise abort(403)
        return verify

    def bind(self, verify):
        if g.current_user:
            user = g.current_user
        else:
            email = request.form.get('email', None)
            password = request.form.get('password', None)
            check, error = check_login_info(email, password)
            if not check:
                return self.render_template(verify=verify, error=error)
            user = get_user_by(email=email).limit(1).first()
            if not user:
                return self.render_template(verify=verify, error=code.ACCOUNT_NO_SUCH_USER)
            if not user.check_password(password):
                return self.render_template(verify=verify, error=code.ACCOUNT_LOGIN_INFO_INVAILD)

        account_login(user)
        return self.join_organization(verify, user)

    def new_register(self, verify):
        username = request.form.get('name', None)
        password = request.form.get('password', None)
        email = request.form.get('email', None)
        check, error = check_register_info(username, email, password)
        if not check:
            return self.render_template(verify=verify, error=error)

        user, error = create_user(username, password, email)
        if error:
            return self.render_template(verify=verify, error=error)
        # clear cache
        account_login(user)
        return self.join_organization(verify, user)

    def join_organization(self, verify, user):
        organization = get_organization_by_git(verify.git)
        if not organization:
            # First member will be admin
            organization, error = create_organization(user, verify.name, verify.git, members=1, admin=1, verify=verify)
            if error:
                return self.render_template(verify=verify, error=error)
            return redirect(url_for('organization.view', git=organization.git))

        member, error = create_members(organization, user, verify)
        if error:
            return self.render_template(verify=verify, error=error)
        return redirect(url_for('organization.view', git=organization.git))

class Login(MethodView):
    decorators = [login_required(need=False)]
    def get(self):
        login_url = url_for('account.login', **request.args)
        return self.render_template(login_url=login_url)

    def post(self):
        login_url = url_for('account.login', **request.args)
        password = request.form.get('password', None)
        email = request.form.get('email', None)
        check, error = check_login_info(email, password)
        if not check:
            return self.render_template(login_info=error, login_url=login_url)

        user = get_user_by(email=email).limit(1).first()
        if not user:
            logger.info('no such user')
            return self.render_template(login_info=code.ACCOUNT_NO_SUCH_USER, login_url=login_url)
        if not user.check_password(password):
            logger.info('invaild passwd')
            return self.render_template(login_info=code.ACCOUNT_LOGIN_INFO_INVAILD, login_url=login_url)

        account_login(user)
        redirect_url = request.args.get('redirect', None)
        return redirect(redirect_url or url_for('index'))

class Logout(MethodView):
    def get(self):
        account_logout()
        return redirect(request.referrer or url_for('index'))

