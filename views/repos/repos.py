#!/usr/local/bin/python2.7
#coding:utf-8

import logging

from flask import g, request

from utils import code
from utils.helper import MethodView
from utils.account import login_required
from utils.validators import check_reponame
from utils.organization import member_required

from query.organization import get_teams_by_ogranization, get_team_member, \
        get_team_by_name

logger = logging.getLogger(__name__)

class Create(MethodView):
    decorators = [member_required(admin=False), login_required('account.login')]
    def get(self, organization, members):
        return self.render_template(
                    organization=organization, \
                    teams=self.get_joined_teams(organization)
                )

    def post(self, organization, members):
        repopath = request.form.get('path', '')
        reponame = request.form.get('name', '')
        team_name = repopath.strip('/').split('/', 1)[0]

        if not check_reponame(reponame):
            return self.render_template(
                        organization=organization, \
                        teams=self.get_joined_teams(organization), \
                        error = code.REPOS_NAME_INVALID, \
                    )

        if team_name and not get_team_by_name(organization.id, team_name):
            return self.render_template(
                        organization=organization, \
                        teams=self.get_joined_teams(organization), \
                        error = code.REPOS_PATH_INVALID, \
                    )

        return 'Hello World'

    def get_joined_teams(self, organization):
        for team in get_teams_by_ogranization(organization.id):
            if not get_team_member(team.id, g.current_user.id):
                continue
            yield team

