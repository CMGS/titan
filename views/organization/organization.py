#!/usr/local/bin/python2.7
#coding:utf-8

import hashlib
import logging

from flask.views import MethodView
from flask import g, redirect, request, url_for, render_template, \
        abort

from utils import code
from utils.mail import async_send_email
from utils.validators import check_name
from utils.account import login_required
from query.organization import create_organization, create_members, \
        get_member, get_organization

logger = logging.getLogger(__name__)

class Register(MethodView):
    def get(self):
        return render_template('organization.register.html')

    def post(self):
        name = request.form.get('name', None)
        if check_name(name):
            return render_template('organization.register.html', info=code.ORGANIZATION_NAME_INVALID)

        # TODO 开关，是否激活公开申请
        organization = create_organization(name)
        if g.current_user:
            create_members(organization.id, g.current_user.id, 1)
            return redirect(url_for('organization.view', organization=organization.id))

        return url_for('account.register', token=organization.token)

class Invite(MethodView):
    decorators = [login_required('account.login')]
    def get(self, oid):
        self.check_member(oid)
        return render_template('organization.invite.html')

    def post(self, oid):
        member = self.check_member(oid)
        organization = get_organization(member.oid)
        emails = request.form.get('email')
        # TODO send_email
        for email in emails:
            m = hashlib.new('md5')
            m.update('%s%s' % (email, organization.token))
            url = url_for('account.register', token=m.hexdigest(), _external=True)
            content = render_template('email.invite.html', user=g.current_user, organization=organization, url=url)
            async_send_email(email, code.EMAIL_INVITE_TITLE, content)
        return render_template('organization.invite.html', send=1)

    def check_member(self, oid):
        member = get_member(oid, g.current_user.id)
        if not member or not member.admin:
            raise abort(404)
        return member

class View(MethodView):
    decorators = [login_required('account.login')]
    def get(self, oid):
        member = self.check_member(oid)
        organization = get_organization(oid)
        return render_template('organization.view.html', organization=organization, member=member)

    def check_member(self, oid):
        member = get_member(oid, g.current_user.id)
        if not member or not member.admin:
            raise abort(404)
        return member

