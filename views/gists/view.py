#!/usr/local/bin/python2.7
#coding:utf-8

from flask import abort, Response, stream_with_context

from views.gists.gists import render_tree, get_url

from utils.jagare import get_jagare
from utils.helper import MethodView
from utils.gists import gist_require
from utils.account import login_required
from utils.organization import member_required

class View(MethodView):
    decorators = [gist_require(), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, gist, private=None):
        if not private and gist.private:
            raise abort(403)
        jagare = get_jagare(gist.id, gist.parent)
        error, tree = jagare.ls_tree(gist.get_real_path())
        if not error:
            tree, meta = tree['content'], tree['meta']
            tree = render_tree(jagare, tree, gist, organization)
        return self.render_template(
                    organization=organization, \
                    member=member, \
                    error=error, \
                    tree=tree, \
                    gist=gist, \
                    url=get_url(organization, gist, 'gists.edit'), \
                    delete=get_url(organization, gist, 'gists.delete'), \
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

