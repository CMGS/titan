#!/usr/local/bin/python2.7
#coding:utf-8

import logging

from flask import g, abort

from utils.helper import MethodView, Obj
from utils.account import login_required
from utils.organization import member_required

from query.account import get_user
from query.repos import get_organization_repos, get_team_repos
from query.organization import get_team_by_name, get_team_member, get_team, \
        get_team_members

logger = logging.getLogger(__name__)

class Explore(MethodView):
    decorators = [member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, **kwargs):
        tname = kwargs.pop('tname', None)
        team = self.get_team(organization, member, tname)
        users = None
        if team:
            members = get_team_members(team.id)
            users = (get_user(member.uid) for member in members)
        return self.render_template(
                    organization = organization, \
                    member = member, \
                    team = team, \
                    repos = self.get_repos(organization, team), \
                    users = users,
                )

    def get_repos(self, organization, team=None):
        if team:
            ret = get_team_repos(organization.id, team.id)
        else:
            ret = get_organization_repos(organization.id)
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
            return None
        team = get_team_by_name(organization.id, tname)
        if not team:
            raise abort(404)
        if not team.private:
            return team
        else:
            team_member = get_team_member(team.id, g.current_user.id)
            if not team_member or not member.admin:
                raise abort(403)
        return team

