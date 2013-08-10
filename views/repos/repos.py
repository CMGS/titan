#!/usr/local/bin/python2.7
#coding:utf-8

import os
import logging

from flask import g, request, redirect, url_for

from utils import code
from utils.jagare import get_jagare
from utils.helper import MethodView
from utils.account import login_required
from utils.validators import check_reponame
from utils.repos import repo_required, get_url
from utils.organization import member_required

from query.account import get_user
from query.repos import create_repo, update_repo,transport_repo, \
        delete_repo
from query.organization import get_teams_by_ogranization, get_team_member, \
        get_team_by_name, get_organization_member

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
        if teamname and (not team or not get_team_member(team.id, g.current_user.id)):
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

        view_url = url_for('repos.view', git=organization.git, rname=name)
        if teamname:
            view_url = url_for('repos.view', git=organization.git, tname=teamname, rname=name)
        return redirect(view_url)

    def get_joined_teams(self, organization):
        for team in get_teams_by_ogranization(organization.id):
            if not get_team_member(team.id, g.current_user.id):
                continue
            yield team

class Setting(MethodView):
    decorators = [repo_required(admin=True), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, repo, admin, team, team_member):
        jagare = get_jagare(repo.id, repo.parent)
        branches = jagare.get_branches_names(repo.get_real_path())
        return self.render_template(
                    branches_switch=branches, \
                    member=member, repo=repo, \
                    organization=organization, \
                    admin=admin, team=team, team_member=team_member, \
                )

    def post(self, organization, member, repo, admin, team, team_member):
        name = request.form.get('name')
        default = request.form.get('default')
        params = {}
        if name != repo.name:
            params['name'] = name
        if default != repo.default:
            params['default'] = default
        if params:
            params['team'] = team
            error = update_repo(organization, repo, params)
            if error:
                return self.render_template(
                        member=member, repo=repo, organization=organization, \
                        error = error, \
                        admin=admin, team=team, team_member=team_member, \
                )
        return redirect(get_url(organization, repo, 'repos.setting', team=team))

class Transport(MethodView):
    decorators = [repo_required(admin=True), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, repo, admin, team, team_member):
        return self.render_template(
                    member=member, repo=repo, organization=organization, \
                    admin=admin, team=team, team_member=team_member, \
                )

    def post(self, organization, member, repo, admin, team, team_member):
        name = request.form.get('name')
        user = get_user(name)
        if not user:
            return self.render_template(
                        member=member, repo=repo, organization=organization, \
                        error=code.ACCOUNT_NO_SUCH_USER, \
                        admin=admin, team=team, team_member=team_member, \
                    )
        if user.id == repo.uid:
            return self.render_template(
                        member=member, repo=repo, organization=organization, \
                        error=code.REPOS_CANT_TRANSPORT_SELF, \
                        admin=admin, team=team, team_member=team_member, \
                    )
        is_member = get_organization_member(organization.id, user.id)
        if not is_member:
            return self.render_template(
                        member=member, repo=repo, organization=organization, \
                        error=code.ORGANIZATION_MEMBER_NOT_EXISTS, \
                        admin=admin, team=team, team_member=team_member, \
                    )

        error = transport_repo(organization, user, repo, team)
        if error:
            return self.render_template(
                        member=member, repo=repo, organization=organization, \
                        error=error, \
                        admin=admin, team=team, team_member=team_member, \
                    )
        return redirect(repo.meta.transport)

class Delete(MethodView):
    decorators = [repo_required(admin=True), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, repo, admin, team, team_member):
        delete_repo(organization, repo, team)
        return redirect(url_for('organization.view', git=organization.git))

class Fork(MethodView):
    decorators = [repo_required(), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, repo, admin, team, team_member):
        return self.render_template(
                    organization=organization, \
                    member=member, \
                    repo=repo, \
                )

    def post(self, organization, member, repo, admin, team, team_member):
        name = request.form.get('name', '')
        summary = request.form.get('summary', '')
        teamname = '' if not team else team.name

        if not check_reponame(name):
            return self.render_template(
                        organization=organization, \
                        member=member, \
                        repo=repo, \
                        error = code.REPOS_NAME_INVALID, \
                    )

        path = os.path.join(teamname, '%s.git' % name)
        fork_repo, error = create_repo(
                name, path, g.current_user, organization, \
                team=team, summary=summary, parent=repo, \
                default=repo.default
        )

        if error:
            return self.render_template(
                        organization=organization, \
                        member=member, \
                        repo=repo, \
                        error = error, \
                    )

        view_url = url_for('repos.view', git=organization.git, rname=name)
        if teamname:
            view_url = url_for('repos.view', git=organization.git, tname=teamname, rname=name)
        return redirect(view_url)

