#!/usr/local/bin/python2.7
#coding:utf-8

import logging

from flask import g, request, redirect, url_for

import code
from utils.helper import MethodView
from utils.account import login_required
from utils.organization import member_required
from utils.validators import check_organization_name

from query.account import get_user
from query.organization import create_team, create_team_members, \
        get_team, clear_team_cache, get_team_member, get_team_members, \
        clear_organization_cache

logger = logging.getLogger(__name__)

class CreateTeam(MethodView):
    decorators = [login_required('account.login'), member_required(admin=False)]
    def get(self, organization, member, git):
        return self.render_template(organization=organization)

    def post(self, organization, member, git):
        name = request.form.get('name', None)
        if check_organization_name(name):
            return self.render_template(error=code.ORGANIZATION_NAME_INVALID)

        team = create_team(name, g.current_user, organization, members=1)
        organization.update_teams(1)
        clear_organization_cache(organization)
        clear_team_cache(team, g.current_user)
        return redirect(url_for('organization.viewteam', git=git, tid=team.id))

class JoinTeam(MethodView):
    decorators = [login_required('account.login'), member_required(admin=False)]
    def post(self, organization, member, git, tid):
        team = get_team(tid)
        is_member = get_team_member(team.id, g.current_user.id)
        if not team:
            return redirect(url_for('organization.index', git=organization.git))
        if not is_member:
            create_team_members(tid, member.uid)
            team.update_members(1)
            clear_team_cache(team, g.current_user)
        return redirect(url_for('organization.viewteam', git=git, tid=team.id))

class QuitTeam(MethodView):
    decorators = [login_required('account.login'), member_required(admin=False)]
    def post(self, organization, member, git, tid):
        team = get_team(tid)
        team_member = get_team_member(team.id, g.current_user.id)
        if team and  team_member:
            team_member.delete()
            team.update_members(-1)
            clear_team_cache(team, g.current_user)
        return redirect(url_for('organization.viewteam', git=git, tid=team.id))

class ViewTeam(MethodView):
    decorators = [login_required('account.login'), member_required(admin=False)]
    def get(self, organization, member, git, tid):
        team = get_team(tid)
        if not team:
            return redirect(url_for('organization.index', git=organization.git))
        members = get_team_members(tid)
        users = (get_user(member.uid) for member in members)
        team_member = get_team_member(team.id, g.current_user.id)
        return self.render_template(organization=organization, team_member=team_member, \
                team=team, users=users)

class SetTeam(MethodView):
    decorators = [login_required('account.login'), member_required(admin=False)]
    def get(self, organization, member, git, tid):
        team = get_team(tid)
        if not team:
            return redirect(url_for('organization.index', git=organization.git))
        is_member = get_team_member(team.id, g.current_user.id)
        if not is_member:
            return redirect(url_for('organization.index', git=organization.git))
        return self.render_template(organization=organization, team=team)

    def post(self, organization, member, git, tid):
        # TODO pic set
        return 'Hello World'

