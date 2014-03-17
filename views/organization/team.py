#!/usr/local/bin/python2.7
#coding:utf-8

import time
import config
import logging

from libs.files import get_uploader, purge
from flask import g, request, redirect, url_for, abort

from utils import code
from utils.helper import MethodView
from utils.account import login_required
from utils.activities import render_push_action, \
        render_activities_page
from utils.validators import check_team_name, check_git
from utils.organization import member_required, team_member_required, \
        process_file

from query.account import get_user
from query.organization import create_team, create_team_members, \
        quit_team, update_team, get_team_members, get_organization_member

logger = logging.getLogger(__name__)

class CreateTeam(MethodView):
    decorators = [member_required(admin=False), login_required('account.login'),]
    def get(self, organization, member):
        if not self.check_permits(organization, member):
            raise abort(403)
        return self.render_template(
                    organization=organization, \
                    member=member, \
                )

    def post(self, organization, member):
        if not self.check_permits(organization, member):
            raise abort(403)
        name = request.form.get('name', None)
        display = request.form.get('display', None)
        private = 1 if 'private' in request.form else 0
        status = check_git(name)
        if not status:
            return self.render_template(
                        organization=organization, \
                        member=member, \
                        error=code.ORGANIZATION_GITNAME_INVALID, \
                    )
        status = check_team_name(display)
        if not status:
            return self.render_template(
                            organization=organization, \
                            member=member, \
                            error=code.ORGANIZATION_NAME_INVALID, \
                    )
        team, error = create_team(name, display, g.current_user, organization, private=private, members=1)
        if error:
            return self.render_template(
                    organization=organization, \
                    member=member, \
                    error=error, \
                    )
        return redirect(url_for('organization.viewteam', git=organization.git, tname=team.name))

    def check_permits(self, organization, member):
        if organization.allow:
            return True
        if member.admin:
            return True
        return False

class JoinTeam(MethodView):
    decorators = [
        team_member_required(need=False), \
        member_required(admin=False), \
        login_required('account.login')
    ]
    def post(self, organization, member, team, team_member):
        if not team_member:
            create_team_members(organization, team, g.current_user)
        return redirect(url_for('organization.viewteam', git=organization.git, tname=team.name))

class QuitTeam(MethodView):
    decorators = [
        team_member_required(), \
        member_required(admin=False), \
        login_required('account.login')
    ]
    def post(self, organization, member, team, team_member):
        quit_team(organization, team, team_member, g.current_user)
        return redirect(url_for('organization.viewteam', git=organization.git, tname=team.name))

class ViewTeam(MethodView):
    decorators = [
        team_member_required(need=False), \
        member_required(admin=False), \
        login_required('account.login')
    ]
    def get(self, organization, member, team, team_member):
        members = get_team_members(team.id)
        users = (get_user(member.uid) for member in members)
        page = request.args.get('p', 1)
        try:
            page = int(page)
        except ValueError:
            raise abort(403)
        data, list_page = render_activities_page(page, t='team', organization=organization, team=team)
        return self.render_template(
                    organization=organization, \
                    team_member=team_member, \
                    team=team, member=member, \
                    users=users, \
                    data=self.render_activities(data, organization, team), \
                    list_page=list_page, \
               )

    def render_activities(self, data, organization, team):
        for action, original, _ in data:
            if action['type'] == 'push':
                yield render_push_action(action, organization, team=team)
            else:
                #TODO for other data
                continue

class AddMember(MethodView):
    decorators = [
        team_member_required(admin=True), \
        member_required(admin=False), \
        login_required('account.login')
    ]
    def get(self, organization, member, team, team_member):
        return self.render_template(
                    organization=organization, \
                    team_member=team_member, \
                    team=team, member=member, \
               )

    def post(self, organization, member, team, team_member):
        name = request.form.get('name', None)
        admin = 1 if 'admin' in request.form else 0
        user = get_user(name)
        if not user:
            return self.render_template(
                        organization=organization, \
                        team_member=team_member, \
                        team=team, member=member, \
                        error=code.ACCOUNT_NO_SUCH_USER, \
                   )
        is_member = get_organization_member(organization.id, user.id)
        if not is_member:
            return self.render_template(
                        organization=organization, \
                        team_member=team_member, \
                        team=team, member=member, \
                        error=code.ORGANIZATION_MEMBER_NOT_EXISTS, \
                   )
        create_team_members(organization, team, user, admin=admin)
        return redirect(url_for('organization.viewteam', git=organization.git, tname=team.name))

class SetTeam(MethodView):
    decorators = [
        team_member_required(admin=True), \
        member_required(admin=False), \
        login_required('account.login')
    ]
    def get(self, organization, member, team, team_member):
        return self.render_template(
                    organization=organization, \
                    team_member=team_member, \
                    team=team, member=member, \
                    salt=time.time(), \
               )

    def post(self, organization, member, team, team_member):
        upload_avatar = request.files['file']
        display = request.form.get('display', None)
        pic = None
        attr = {}

        if display:
            status = check_team_name(display)
            if not status:
                return self.render_template(
                            organization=organization, \
                            team_member=team_member, \
                            team=team, member=member, \
                            salt=time.time(), \
                            error=code.ORGANIZATION_NAME_INVALID, \
                       )
            attr['display'] = display
        if upload_avatar:
            pic = self.get_pic(organization, team, member, team_member, upload_avatar)
            attr['pic'] = pic

        error = update_team(organization, team, **attr)
        if error:
            return self.render_template(
                        organization=organization, \
                        team_member=team_member, \
                        team=team, member=member, \
                        salt=time.time(), \
                        error=error, \
                   )
        return redirect(url_for('organization.setteam', git=organization.git, tname=team.name))

    def get_pic(self, organization, team, member, team_member, upload_avatar):
        uploader = get_uploader(path=config.UPLOAD_DIR_PATH)
        filename, stream, error = process_file(team, upload_avatar)
        if error:
            return self.render_template(
                        organization=organization, \
                        team_member=team_member, \
                        team=team, member=member, \
                        salt=time.time(), \
                        error=error, \
                   )
        uploader.writeFile(filename, stream)
        purge(filename)
        return filename

