#!/usr/local/bin/python2.7
#coding:utf-8

import logging

from flask import g, abort, request

from utils.helper import MethodView, Obj
from utils.account import login_required
from utils.organization import member_required

from query.account import get_user
from query.repos import get_organization_repos, get_team_repos, \
        get_user_organization_repos, get_user_team_repos, \
        get_user_watcher_repos, get_user_watcher_team_repos
from query.organization import get_team_by_name, get_team_member, get_team, \
        get_team_members

logger = logging.getLogger(__name__)

class Explore(MethodView):
    decorators = [member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, **kwargs):
        f = request.args.get('f', None)
        if f not in ['w', 'm']:
            f = None
        else:
            f = 0 if f == 'w' else 1
        tname = kwargs.pop('tname', None)
        team, team_member = self.get_team(organization, member, tname)
        users = None
        if team:
            members = get_team_members(team.id)
            users = (get_user(member.uid) for member in members)
        return self.render_template(
                    organization = organization, \
                    member = member, \
                    team = team, \
                    team_member = team_member, \
                    repos = self.get_repos(organization, team, f), \
                    users = users,
                )

    def filter_repos(self, organization, team, f):
        if f is None:
            if team:
                ret = get_team_repos(organization.id, team.id)
            else:
                ret = get_organization_repos(organization.id)
        elif f == 0:
            if team:
                # Get user watch team repos
                ret = get_user_watcher_team_repos(g.current_user.id, organization.id, team.id)
            else:
                # Get user watch repos
                ret = get_user_watcher_repos(g.current_user.id, organization.id)
        elif f == 1:
            if team:
                # Get user team repos
                ret = get_user_team_repos(organization.id, team.id, g.current_user.id)
            else:
                # Get user repos
                ret = get_user_organization_repos(organization.id, g.current_user.id)
        else:
            ret = []
        return ret

    def get_repos(self, organization, team=None, f=None):
        ret = self.filter_repos(organization, team, f)
        for r in ret:
            t = Obj()
            t.name = None
            if not team and r.tid != 0:
                t = get_team(r.tid)
            elif team:
                t = team
            setattr(r, 'team', t)
            yield r

    def get_team(self, organization, member, tname):
        if not tname:
            return None, None
        team = get_team_by_name(organization.id, tname)
        if not team:
            raise abort(404)
        team_member = get_team_member(team.id, g.current_user.id)
        if team.private and (not team_member or not member.admin):
            raise abort(403)
        return team, team_member

