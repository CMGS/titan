#!/usr/local/bin/python2.7
#coding:utf-8

import logging

from flask import g, request, redirect, url_for

from utils import code
from utils.token import create_token
from utils.helper import MethodView
from utils.account import login_required
from utils.organization import send_verify_mail, member_required
from utils.validators import check_organization_name, check_git, check_git_exists, \
        check_organization_plan
from query.account import get_user_by_email
from query.organization import get_member, create_organization, \
        create_verify, clear_organization_cache

logger = logging.getLogger(__name__)

class Register(MethodView):
    def get(self):
        return self.render_template()

    def post(self):
        name = request.form.get('name', None)
        git = request.form.get('git', None)
        email = request.form.get('email', None)
        if check_organization_name(name):
            return self.render_template(error=code.ORGANIZATION_NAME_INVALID)
        for status in [check_git(git), check_git_exists(git)]:
            if status:
                return self.render_template(error=status[1])

        if g.current_user:
            organization = create_organization(g.current_user, name, git, members=1, admin=1)
            return redirect(url_for('organization.view', git=organization.git))

        stub = create_token(20)
        verify = create_verify(stub, email, name, git, admin=1)
        send_verify_mail(verify)
        return self.render_template(send=1)

class Invite(MethodView):
    decorators = [login_required('account.login'), member_required(admin=True)]
    def get(self, organization, member):
        return self.render_template()

    def post(self, organization, member):
        count = 0
        for flag in range(1, 6):
            email = request.form.get('email%d' % flag, None)
            if not email and self.is_member(organization.id, email):
                continue
            admin = request.form.get('admin%d' % flag, None)
            admin = 1 if admin else 0

            # 超过上限禁止增员
            count += 1
            status = check_organization_plan(organization, count)
            if status:
                return self.render_template(send=status[1])

            stub = create_token(20)
            verify = create_verify(stub, email, organization.name, organization.git, admin=admin)
            send_verify_mail(verify)
        return self.render_template(send=code.ORGANIZATION_INVITE_SUCCESS)

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
    def get(self, organization, member):
        return self.render_template(organization=organization, member=member)

class Setting(MethodView):
    decorators = [login_required('account.login'), member_required(admin=True)]
    def get(self, organization, member):
        return self.render_template(organization=organization)

    def post(self, organization, members):
        name = request.form.get('name', None)
        gitname = request.form.get('git', None)
        location = request.form.get('location', None)
        kw = {}

        if name and check_organization_name(name):
            return self.render_template(error=code.ORGANIZATION_NAME_INVALID)
            kw['name'] = name
        if gitname:
            for status in [check_git(gitname), check_git_exists(gitname)]:
                if status:
                    return self.render_template(error=status[1])
            kw['git'] = gitname
        if location:
            kw['location'] = location

        organization.update(name=name, **kw)
        clear_organization_cache(organization)
        return redirect(url_for('organization.view', git=organization.git))

