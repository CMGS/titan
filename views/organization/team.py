#!/usr/local/bin/python2.7
#coding:utf-8

import time
import logging

from sheep.api.files import get_uploader, purge
from flask import g, request, redirect, url_for

import code
from utils.helper import MethodView, Obj
from utils.account import login_required
from utils.validators import check_organization_name
from utils.organization import member_required, team_member_required, \
        process_file

from query.account import get_user
from query.organization import create_team, create_team_members, \
        clear_team_cache, get_team_members, clear_organization_cache

logger = logging.getLogger(__name__)

class CreateTeam(MethodView):
    decorators = [member_required(admin=False), login_required('account.login'),]
    def get(self, organization, member):
        return self.render_template(organization=organization)

    def post(self, organization, member):
        name = request.form.get('name', None)
        if check_organization_name(name):
            return self.render_template(error=code.ORGANIZATION_NAME_INVALID)

        team = create_team(name, g.current_user, organization, members=1)
        organization.update_teams(1)
        clear_organization_cache(organization)
        clear_team_cache(organization, team, g.current_user)
        return redirect(url_for('organization.viewteam', git=organization.git, tname=team.name))

class JoinTeam(MethodView):
    decorators = [
        team_member_required(need=False), \
        member_required(admin=False), \
        login_required('account.login')
    ]
    def post(self, organization, member, team, team_member):
        if not team_member:
            create_team_members(team.id, member.uid)
            team.update_members(1)
            clear_team_cache(organization, team, g.current_user)
        return redirect(url_for('organization.viewteam', git=organization.git, tname=team.name))

class QuitTeam(MethodView):
    decorators = [
        team_member_required(), \
        member_required(admin=False), \
        login_required('account.login')
    ]
    def post(self, organization, member, team, team_member):
        if team_member:
            team_member.delete()
            team.update_members(-1)
            clear_team_cache(organization, team, g.current_user)
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
        old_team = self.get_old_team(team)
        upload_avatar = request.files['file']
        if upload_avatar:
            self.update_pic(organization, team, upload_avatar)
        name = request.form.get('name', None)
        if name:
            self.update_info(organization, team, name)
        if upload_avatar or name:
            clear_team_cache(organization, old_team)
        return redirect(url_for('organization.setteam', git=organization.git, tname=team.name))

    def update_pic(self, organization, team, upload_avatar):
        uploader = get_uploader()
        filename, stream, error = process_file(team, upload_avatar)
        if error:
            return self.render_template(team=team, error=error, salt=time.time())
        uploader.writeFile(filename, stream)
        purge(filename)
        team.set_args(pic=filename)

    def update_info(self, organization, team, name):
        if check_organization_name(name):
            return self.render_template(error=code.ORGANIZATION_NAME_INVALID)
        team.set_args(name=name)

    def get_old_team(self, team):
        # TODO ugly implement
        old_team = Obj()
        old_team.id = team.id
        old_team.name = team.name
        return old_team

