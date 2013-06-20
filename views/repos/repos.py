#!/usr/local/bin/python2.7
#coding:utf-8

import os
import logging

from flask import g, request

from utils import code
from utils.helper import MethodView
from utils.account import login_required
from utils.validators import check_reponame
from utils.organization import member_required

from query.repos import create_repo

from query.organization import get_teams_by_ogranization, get_team_member, \
        get_team_by_name

logger = logging.getLogger(__name__)

class Create(MethodView):
    decorators = [member_required(admin=False), login_required('account.login')]
    def get(self, organization, member):
        return self.render_template(
                    organization=organization, \
                    member=member, \
                    teams=self.get_joined_teams(organization)
                )

    def post(self, organization, member):
        repopath = request.form.get('path', '')
        name = request.form.get('name', '')
        summary = request.form.get('summary', '')
        teamname = repopath.strip('/').split('/', 1)[0]

        if not check_reponame(name):
            return self.render_template(
                        organization=organization, \
                        member=member, \
                        teams=self.get_joined_teams(organization), \
                        error = code.REPOS_NAME_INVALID, \
                    )

        team = get_team_by_name(organization.id, teamname) if teamname else None
        if teamname and not team:
            return self.render_template(
                        organization=organization, \
                        member=member, \
                        teams=self.get_joined_teams(organization), \
                        error = code.REPOS_PATH_INVALID, \
                    )

        path = os.path.join(teamname, '%s.git' % name)
        repo, error = create_repo(name, path, g.current_user, organization, team=team, summary=summary)
        if error:
            return self.render_template(
                        organization=organization, \
                        member=member, \
                        teams=self.get_joined_teams(organization), \
                        error = error, \
                    )
        return 'Hello World'

    def get_joined_teams(self, organization):
        for team in get_teams_by_ogranization(organization.id):
            if not get_team_member(team.id, g.current_user.id):
                continue
            yield team

