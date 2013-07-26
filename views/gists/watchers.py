#!/usr/local/bin/python2.7
#coding:utf-8

import logging

from flask import g, redirect

from utils.helper import MethodView
from utils.gists import gist_require
from utils.account import login_required
from utils.organization import member_required

from query.account import get_user
from query.gists import create_watcher, delete_watcher, get_gist_watcher, \
        get_gist_watchers

logger = logging.getLogger(__name__)

class Watch(MethodView):
    decorators = [gist_require(), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, gist):
        watcher = get_gist_watcher(g.current_user.id, gist.id)
        if not watcher:
            create_watcher(g.current_user, gist, organization)
        return redirect(gist.meta.view)

class Unwatch(MethodView):
    decorators = [gist_require(), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, gist):
        watcher = get_gist_watcher(g.current_user.id, gist.id)
        if watcher:
            delete_watcher(g.current_user, watcher, gist, organization)
        return redirect(gist.meta.view)

class Watchers(MethodView):
    decorators = [gist_require(), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, gist):
        watchers = get_gist_watchers(gist.id)
        return self.render_template(
                    organization=organization, \
                    member=member, \
                    gist=gist, \
                    watchers=self.render_watchers(watchers)
                )

    def render_watchers(self, watchers):
        for watcher in watchers:
            setattr(watcher, 'user', get_user(watcher.uid))
            yield watcher
