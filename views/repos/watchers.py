#!/usr/local/bin/python2.7
#coding:utf-8

import logging

from flask import g, redirect

from utils.helper import MethodView
from utils.repos import repo_required
from utils.account import login_required
from utils.organization import member_required

from query.account import get_user
from query.repos import create_watcher, delete_watcher, \
        get_repo_watcher, get_repo_watchers

logger = logging.getLogger(__name__)

class Watch(MethodView):
    decorators = [repo_required(), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, repo, admin, team, team_member):
        watcher = get_repo_watcher(g.current_user.id, repo.id)
        if not watcher:
            create_watcher(g.current_user, repo, organization, team=team)
        return redirect(repo.meta.view)

class Unwatch(MethodView):
    decorators = [repo_required(), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, repo, admin, team, team_member):
        watcher = get_repo_watcher(g.current_user.id, repo.id)
        if watcher:
            delete_watcher(g.current_user, watcher, repo, organization, team=team)
        return redirect(repo.meta.view)

class Watchers(MethodView):
    decorators = [repo_required(), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, repo, admin, team, team_member):
        watchers = get_repo_watchers(repo.id)
        return self.render_template(
                    member=member, repo=repo, organization=organization, \
                    watchers=self.render_forks(watchers), \
                    admin=admin, team=team, team_member=team_member, \
                )

    def render_forks(self, watchers):
        for watcher in watchers:
            setattr(watcher, 'user', get_user(watcher.uid))
            yield watcher

