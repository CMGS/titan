#!/usr/local/bin/python2.7
#coding:utf-8

import logging

from flask import request, redirect, url_for

from utils import code
from utils.helper import MethodView
from utils.repos import repo_required
from utils.account import login_required
from utils.organization import member_required

from query.account import get_user
from query.organization import get_organization_member
from query.repos import create_commiter, get_repo_commiter, get_repo_commiters, \
        delete_commiter

logger = logging.getLogger(__name__)

class Commiters(MethodView):
    decorators = [repo_required(admin=True), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, repo, **kwargs):
        return self.render_template(
                    member=member, repo=repo, organization=organization, \
                    commiters = self.get_commiters(repo), \
                    **kwargs
                )
    def post(self, organization, member, repo, **kwargs):
        name = request.form.get('name')
        user = get_user(name)
        if not user:
            return self.render_template(
                        member=member, repo=repo, organization=organization, \
                        commiters = self.get_commiters(repo), \
                        error=code.ACCOUNT_NO_SUCH_USER, \
                        **kwargs
                    )
        if user.id == repo.uid:
            return self.render_template(
                        member=member, repo=repo, organization=organization, \
                        commiters = self.get_commiters(repo), \
                        error=code.REPOS_COMMITER_EXISTS, \
                        **kwargs
                    )
        is_member = get_organization_member(organization.id, user.id)
        if not is_member:
            return self.render_template(
                        member=member, repo=repo, organization=organization, \
                        commiters = self.get_commiters(repo), \
                        error=code.ORGANIZATION_MEMBER_NOT_EXISTS, \
                        **kwargs
                    )
        create_commiter(user, repo, organization, kwargs.get('team', None))
        return redirect(url_for('repos.commiters', \
            git=organization.git, rname=repo.name, \
            tname=kwargs['team'].name if kwargs.get('team') else None))

    def get_commiters(self, repo):
        commiters = get_repo_commiters(repo.id)
        commiters = (get_user(commiter.uid) for commiter in commiters)
        return commiters

class RemoveCommiter(MethodView):
    decorators = [repo_required(admin=True), member_required(admin=False), login_required('account.login')]
    def post(self, organization, member, repo, **kwargs):
        name = request.form.get('name')
        user = get_user(name)
        if not user:
            return redirect(url_for('repos.commiters', \
                git=organization.git, rname=repo.name, \
                tname=kwargs['team'].name if kwargs.get('team') else None))
        if user.id == repo.uid:
            return redirect(url_for('repos.commiters', \
                git=organization.git, rname=repo.name, \
                tname=kwargs['team'].name if kwargs.get('team') else None))
        commiter = get_repo_commiter(user.id, repo.id)
        if user and commiter:
            delete_commiter(user, commiter, repo, organization, kwargs.get('team', None))
        return redirect(url_for('repos.commiters', \
            git=organization.git, rname=repo.name, \
            tname=kwargs['team'].name if kwargs.get('team') else None))

