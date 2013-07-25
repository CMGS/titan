#!/usr/local/bin/python2.7
#coding:utf-8

from flask import g, abort, Response, stream_with_context

from utils.jagare import get_jagare
from utils.helper import MethodView
from utils.account import login_required
from utils.organization import member_required
from utils.gists import gist_require, render_tree, get_url

from query.account import get_user
from query.gists import get_gist_watcher, get_gist_forks

class View(MethodView):
    decorators = [gist_require(), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, gist, version='master'):
        jagare = get_jagare(gist.id, gist.parent)
        error, tree = jagare.ls_tree(gist.get_real_path(), version=version)
        if not error:
            tree, meta = tree['content'], tree['meta']
            tree = render_tree(jagare, tree, gist, organization, version=version)
        watcher = get_gist_watcher(g.current_user.id, gist.id)
        return self.render_template(
                    organization=organization, \
                    member=member, \
                    error=error, \
                    tree=tree, \
                    gist=gist, \
                    watcher=watcher, \
                )

class Raw(MethodView):
    decorators = [gist_require(), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, gist, path):
        jagare = get_jagare(gist.id, gist.parent)
        error, res = jagare.cat_file(gist.get_real_path(), path)
        if error:
            raise abort(error)
        resp = Response(stream_with_context(res))
        resp.headers['X-Accel-Buffering'] = 'no'
        resp.headers['Cache-Control'] = 'no-cache'
        resp.headers['Content-Type'] = res.headers.get('content-type', 'application/octet-stream')
        return resp

class Forks(MethodView):
    decorators = [gist_require(), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, gist):
        forks = get_gist_forks(gist.id)
        return self.render_template(
                    organization=organization, \
                    member=member, \
                    gist=gist, \
                    forks=self.render_forks(organization, forks)
                )

    def render_forks(self, organization, forks):
        for fork in forks:
            view_url = get_url(organization, fork, 'gists.view')
            setattr(fork, 'view', view_url)
            setattr(fork, 'user', get_user(fork.uid))
            yield fork

