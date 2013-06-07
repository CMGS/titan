#!/usr/local/bin/python2.7
#coding:utf-8

import time
import logging

from sheep.api.files import get_uploader, purge
from flask import g, request, redirect, url_for

from utils import code
from utils.helper import MethodView, Obj
from utils.account import login_required
from utils.validators import check_team_name, check_git
from utils.organization import member_required, team_member_required, \
        process_file

from query.account import get_user
from query.organization import create_team, create_team_members, \
        quit_team, update_team, get_team_members

logger = logging.getLogger(__name__)

class CreateTeam(MethodView):
    decorators = [member_required(admin=False), login_required('account.login'),]
    def get(self, organization, member):
        return self.render_template(organization=organization)

    def post(self, organization, member):
        name = request.form.get('name', None)
        display = request.form.get('display', None)
        status = check_git(name)
        if not status:
            return self.render_template(error=code.ORGANIZATION_NAME_INVALID)
        status = check_team_name(display)
        if not status:
            return self.render_template(error=code.ORGANIZATION_NAME_INVALID)
        team, error = create_team(name, display, g.current_user, organization, members=1)
        if error:
            return self.render_template(organization=organization, error=error)
        return redirect(url_for('organization.viewteam', git=organization.git, tname=team.name))

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
        if team_member:
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
        return self.render_template(organization=organization, team_member=team_member, \
                team=team, users=users)

class SetTeam(MethodView):
    decorators = [
        team_member_required(), \
        member_required(admin=False), \
        login_required('account.login')
    ]
    def get(self, organization, member, team, team_member):
        return self.render_template(organization=organization, team=team, salt=time.time())

    def post(self, organization, member, team, team_member):
        upload_avatar = request.files['file']
        name = request.form.get('name', None)
        display = request.form.get('display', None)
        pic = None
        attr = {}
        if name:
            status = check_git(name)
            if not status:
                return self.render_template(error=code.ORGANIZATION_NAME_INVALID)
            attr['name'] = name
        if display:
            status = check_team_name(display)
            if not status:
                return self.render_template(error=code.ORGANIZATION_NAME_INVALID)
            attr['display'] = display
        if upload_avatar:
            pic = self.get_pic(organization, team, upload_avatar)
            attr['pic'] = pic

        old_team = self.get_old_team(team)
        team, error = update_team(organization, old_team, team, **attr)
        if error:
            return self.render_template(team=team, error=error)
        return redirect(url_for('organization.setteam', git=organization.git, tname=team.name))

    def get_pic(self, organization, team, upload_avatar):
        uploader = get_uploader()
        filename, stream, error = process_file(team, upload_avatar)
        if error:
            return self.render_template(team=team, error=error, salt=time.time())
        uploader.writeFile(filename, stream)
        purge(filename)
        return filename

    def get_old_team(self, team):
        # TODO ugly implement
        old_team = Obj()
        old_team.id = team.id
        old_team.name = team.name
        return old_team

