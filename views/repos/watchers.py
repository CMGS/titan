#!/usr/local/bin/python2.7
#coding:utf-8

import logging

from flask import g, redirect, url_for

from utils.helper import MethodView
from utils.repos import repo_required
from utils.account import login_required
from utils.organization import member_required

from query.repos import create_watcher, delete_watcher, get_repo_watcher

logger = logging.getLogger(__name__)

class Watchers(MethodView):
    decorators = [repo_required(), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, repo, **kwargs):
        watcher = get_repo_watcher(g.current_user.id, repo.id)
        team = kwargs.get('team', None)
        if not watcher:
            create_watcher(g.current_user, repo, organization, team=team)
        tname = team.name if team else None
        return redirect(url_for('repos.view', git=organization.git, tname=tname, rname=repo.name))

class RemoveWatchers(MethodView):
    decorators = [repo_required(), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, repo, **kwargs):
        watcher = get_repo_watcher(g.current_user.id, repo.id)
        team = kwargs.get('team', None)
        if watcher:
            delete_watcher(g.current_user, watcher, repo, organization, team=team)
        tname = team.name if team else None
        return redirect(url_for('repos.view', git=organization.git, tname=tname, rname=repo.name))

