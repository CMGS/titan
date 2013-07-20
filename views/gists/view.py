#!/usr/local/bin/python2.7
#coding:utf-8

from flask import g, abort, Response, stream_with_context

from views.gists.gists import render_tree, get_url

from utils.jagare import get_jagare
from utils.helper import MethodView
from utils.gists import gist_require
from utils.account import login_required
from utils.organization import member_required

from query.gists import get_gist_watcher

class View(MethodView):
    decorators = [gist_require(), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, gist, private=None):
        if not private and gist.private:
            raise abort(403)
        jagare = get_jagare(gist.id, gist.parent)
        error, ret = jagare.get_log(gist.get_real_path(), total=1)
        revisions_count = 0 if error else ret['total']
        error, tree = jagare.ls_tree(gist.get_real_path())
        if not error:
            tree, meta = tree['content'], tree['meta']
            tree = render_tree(jagare, tree, gist, organization)
        watcher = get_gist_watcher(g.current_user.id, gist.id)
        watch_url = get_url(organization, gist, 'gists.watch') if not watcher else get_url(organization, gist, 'gists.unwatch')
        return self.render_template(
                    organization=organization, \
                    member=member, \
                    error=error, \
                    tree=tree, \
                    gist=gist, \
                    watcher=watcher, \
                    watch_url=watch_url, \
                    url=get_url(organization, gist, 'gists.edit'), \
                    delete=get_url(organization, gist, 'gists.delete'), \
                    revisions=get_url(organization, gist, 'gists.revisions'), \
                    revisions_count=revisions_count, \
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

