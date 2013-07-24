#!/usr/local/bin/python2.7
#coding:utf-8

from flask import g, abort, Response, stream_with_context

from utils.jagare import get_jagare
from utils.helper import MethodView
from utils.account import login_required
from utils.organization import member_required
from utils.gists import gist_require, render_tree

from query.gists import get_gist_watcher

class View(MethodView):
    decorators = [gist_require(), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, gist, private=None, version='master'):
        if not private and gist.private:
            raise abort(403)
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
    def get(self, organization, member, gist, path, private=None):
        jagare = get_jagare(gist.id, gist.parent)
        error, res = jagare.cat_file(gist.get_real_path(), path)
        if error:
            raise abort(error)
        resp = Response(stream_with_context(res))
        resp.headers['X-Accel-Buffering'] = 'no'
        resp.headers['Cache-Control'] = 'no-cache'
        resp.headers['Content-Type'] = res.headers.get('content-type', 'application/octet-stream')
        return resp

class Network(MethodView):
    decorators = [gist_require(), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, gist, private=None):
        pass

