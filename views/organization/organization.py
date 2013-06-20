#!/usr/local/bin/python2.7
#coding:utf-8

import logging

from flask import g, request, redirect, url_for

from utils import code
from utils.token import create_token
from utils.helper import MethodView
from utils.account import login_required
from utils.organization import send_verify_mail, member_required
from utils.validators import check_organization_name, check_git, \
        check_members_limit, check_email
from query.account import get_user_by_email, get_user
from query.organization import get_organization_member, create_organization, \
        create_verify, update_organization, get_teams_by_ogranization, \
        get_team_members, get_team_member

logger = logging.getLogger(__name__)

class Create(MethodView):
    def get(self):
        return self.render_template()

    def post(self):
        name = request.form.get('name', None)
        git = request.form.get('git', None)
        email = request.form.get('email', None)
        if email and not check_email(email):
            return self.render_template(error=code.ACCOUNT_EMAIL_INVAILD)
        if not check_organization_name(name):
            return self.render_template(error=code.ORGANIZATION_NAME_INVALID)
        if not check_git(git):
            return self.render_template(error=code.ORGANIZATION_GITNAME_INVAILD)
        if g.current_user:
            organization, error = create_organization(g.current_user, name, git, members=1, admin=1)
            if error:
                return self.render_template(error=error)
            return redirect(url_for('organization.view', git=organization.git))
        stub = create_token(20)
        verify, error = create_verify(stub, email, name, git, admin=1)
        if error:
            return self.render_template(error=error)
        send_verify_mail(verify)
        return self.render_template(send=code.ORGANIZATION_CREATE_SUCCESS)

class Invite(MethodView):
    decorators = [member_required(admin=True), login_required('account.login')]
    def get(self, organization, member):
        return self.render_template(
                    organization=organization, \
                    member=member, \
               )

    def post(self, organization, member):
        count = 0
        for flag in range(1, 6):
            email = request.form.get('email%d' % flag, None)
            if not email or self.is_member(organization.id, email):
                continue
            admin = request.form.get('admin%d' % flag, None)
            admin = 1 if admin else 0

            # 超过上限禁止增员
            count += 1
            if not check_members_limit(organization, count):
                return self.render_template(
                            organization=organization, \
                            member=member, \
                            send=code.ORGANIZATION_LIMIT, \
                       )
            if not check_email(email):
                return self.render_template(
                            organization=organization, \
                            member=member, \
                            error=code.ACCOUNT_EMAIL_INVAILD, \
                       )
            stub = create_token(20)
            verify, error = create_verify(stub, email, organization.name, organization.git, admin=admin)
            if not verify:
                continue
            send_verify_mail(verify)
        return self.render_template(
                    organization=organization, \
                    member=member, \
                    send=code.ORGANIZATION_INVITE_SUCCESS, \
               )

    def is_member(self, oid, email):
        user = get_user_by_email(email)
        if not user:
            return False
        member = get_organization_member(oid, user.id)
        if member:
            return True
        return False

class View(MethodView):
    decorators = [member_required(admin=False), login_required('account.login')]
    def get(self, organization, member):
        return self.render_template(
                    organization=organization, \
                    member=member, \
                    teams=self.get_teams(organization)
                )

    def get_teams(self, organization):
        for team in get_teams_by_ogranization(organization.id):
            members = get_team_members(team.id)
            members = (get_user(m.uid) for m in members)
            joined = True if get_team_member(team.id, g.current_user.id) else False
            setattr(team, '__members', members)
            setattr(team, '__joined', joined)
            yield team

class Setting(MethodView):
    decorators = [member_required(admin=True), login_required('account.login')]
    def get(self, organization, member):
        return self.render_template(
                    organization=organization, \
                    member=member, \
               )

    def post(self, organization, member):
        name = request.form.get('name', None)
        gitname = request.form.get('git', None)
        location = request.form.get('location', None)
        allow = 1 if 'allow' in request.form else 0

        if name and not check_organization_name(name):
            return self.render_template(
                        organization=organization, \
                        member=member, \
                        error=code.ORGANIZATION_NAME_INVALID
                   )
        if gitname and not check_git(gitname):
            return self.render_template(
                        organization=organization, \
                        member=member, \
                        error=code.ORGANIZATION_GITNAME_INVAILD
                   )

        organization, error = update_organization(organization, name, gitname, location, allow)
        if error:
            return self.render_template(
                        organization=organization, \
                        member=member, \
                        error=error
                   )
        return redirect(url_for('organization.view', git=organization.git))

