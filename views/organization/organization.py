#!/usr/local/bin/python2.7
#coding:utf-8

import logging

from flask.views import MethodView
from flask import g, request, render_template, redirect, url_for

from utils import code
from utils.token import create_token
from utils.account import login_required
from utils.organization import send_verify_mail, member_required
from utils.validators import check_organization_name, check_git, check_git_exists
from query.account import get_user_by_email
from query.organization import get_member, get_organization_by_git, \
        create_organization, create_verify

logger = logging.getLogger(__name__)

class Register(MethodView):
    def get(self):
        return render_template('organization.register.html')

    def post(self):
        name = request.form.get('name', None)
        git = request.form.get('git', None)
        email = request.form.get('email', None)
        if check_organization_name(name):
            return render_template('organization.register.html', error=code.ORGANIZATION_NAME_INVALID)
        for status in [check_git(git), check_git_exists(git)]:
            if status:
                return render_template('organization.register.html', error=status[1])

        if g.current_user:
            organization = create_organization(g.current_user, name, git, members=1, admin=1)
            return redirect(url_for('organization.view', oid=organization.id))

        stub = create_token(20)
        verify = create_verify(stub, email, name, git, admin=1)
        send_verify_mail(verify)
        return render_template('organization.register.html', send=1)

class Invite(MethodView):
    decorators = [login_required('account.login'), member_required(admin=True)]
    def get(self, git):
        return render_template('organization.invite.html')

    def post(self, git):
        emails = set(request.form.getlist('email'))
        organization = get_organization_by_git(git)
        for email in emails:
            if not email or self.is_member(organization.id, email):
                continue

            stub = create_token(20)
            verify = create_verify(stub, email, organization.name, organization.git)
            send_verify_mail(verify)
        return render_template('organization.invite.html', send=1)

    def is_member(self, oid, email):
        user = get_user_by_email(email)
        if not user:
            return False
        member = get_member(oid, user.id)
        if member:
            return True
        return False

class View(MethodView):
    decorators = [login_required('account.login'), member_required(admin=False)]
    def get(self, git):
        organization = get_organization_by_git(git)
        return render_template('organization.view.html', organization=organization)

