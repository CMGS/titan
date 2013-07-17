#!/usr/local/bin/python2.7
#coding:utf-8

import logging

from flask import url_for, request, redirect, \
        g, abort, Response, stream_with_context

from utils import code
from utils.repos import format_time
from utils.gists import gist_require
from utils.token import create_token
from utils.account import login_required
from utils.organization import member_required
from utils.helper import MethodView, Obj, get_hash
from utils.jagare import get_jagare, format_content

from query.gists import create_gist, update_gist

logger = logging.getLogger(__name__)

def render_tree(jagare, tree, gist, organization, render=True):
    ret = []
    for d in tree:
        data = Obj()
        if d['type'] == 'blob':
            data.content, data.content_type, data.length = format_content(
                    jagare, gist, d['path'], render=render, \
            )
        else:
            continue
        data.download = url_for('gists.raw', git=organization.git, path=d['path'], gid=gist.id)
        data.name = d['name']
        data.sha = d['sha']
        data.type = d['type']
        data.ago = format_time(d['commit']['committer']['ts'])
        data.message = d['commit']['message'][:150]
        data.commit = d['commit']['sha']
        data.path = d['path']
        ret.append(data)
    return ret

class Create(MethodView):
    decorators = [member_required(admin=False), login_required('account.login')]
    def get(self, organization, member):
        return self.render_template(
                    organization=organization, \
                    member=member, \
                )

    def post(self, organization, member):
        summary = request.form.get('summary')
        filenames = request.form.getlist('filename')
        codes = request.form.getlist('code')
        private = create_token(20) if request.form.get('private') else None
        length = len(filenames)
        data = {}
        for i in xrange(0, length):
            filename = filenames[i]
            if not filename:
                return self.render_template(
                            organization=organization, \
                            member=member, \
                            error=code.GIST_WITHOUT_FILENAME, \
                            filenames=filenames, \
                            codes=codes, \
                        )
            if data.get(filename):
                return self.render_template(
                            organization=organization, \
                            member=member, \
                            error=code.GIST_FILENAME_EXISTS, \
                            filenames=filenames, \
                            codes=codes, \
                        )
            data[filename] = codes[i]
        gist, err = create_gist(data, organization, g.current_user, summary, private=private)
        if err:
            return self.render_template(
                        organization=organization, \
                        member=member, \
                        error=code.GIST_WITHOUT_FILENAME, \
                        filenames=filenames, \
                        codes=codes, \
                    )
        return redirect(url_for('gists.view', git=organization.git, gid=gist.id))

class View(MethodView):
    decorators = [gist_require(), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, gist):
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

class Edit(MethodView):
    decorators = [gist_require(owner=True), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, gist):
        jagare = get_jagare(gist.id, gist.parent)
        error, tree = jagare.ls_tree(gist.get_real_path())
        if not error:
            tree, meta = tree['content'], tree['meta']
            tree = render_tree(jagare, tree, gist, organization, False)
        return self.render_template(
                    organization=organization, \
                    member=member, \
                    error=error, \
                    tree=tree, \
                    gist=gist, \
                )

    def post(self, organization, member, gist):
        summary = request.form.get('summary')
        filenames = request.form.getlist('filename')
        codes = request.form.getlist('code')
        data = {}
        length = len(filenames)
        for i in xrange(0, length):
            filename = filenames[i]
            if not filename:
                return self.render_template(
                            organization=organization, \
                            member=member, \
                            error=code.GIST_WITHOUT_FILENAME, \
                            tree=self.gen_tree(length, filenames, codes), \
                            gist=gist,
                        )
            if data.get(filename):
                return self.render_template(
                            organization=organization, \
                            member=member, \
                            error=code.GIST_FILENAME_EXISTS, \
                            tree=self.gen_tree(length, filenames, codes), \
                            gist=gist,
                        )
            data[filename] = codes[i]
        jagare = get_jagare(gist.id, gist.parent)
        error, tree = jagare.ls_tree(gist.get_real_path())
        if error:
            return self.render_template(
                        organization=organization, \
                        member=member, \
                        error=code.REPOS_LS_TREE_FAILED, \
                        tree=self.gen_tree(length, filenames, codes), \
                        gist=gist,
                    )
        data = self.diff(jagare, tree, gist, organization, data)
        _, error = update_gist(g.current_user, gist, data, summary)
        if error:
            return self.render_template(
                        organization=organization, \
                        member=member, \
                        error=code.GIST_UPDATE_FAILED, \
                        tree=self.gen_tree(length, filenames, codes), \
                        gist=gist,
                    )
        return redirect(url_for('gists.view', git=organization.git, gid=gist.id))

    def diff(self, jagare, tree, gist, organization, data):
        tree, meta = tree['content'], tree['meta']
        tree = render_tree(jagare, tree, gist, organization, False)
        for d in tree:
            name = d.name
            if data.get(name, None) is None:
                # set delete flag
                data[d.path] = ''
                continue
            old_hash = get_hash(d.content())
            new_hash = get_hash(data[name])
            if old_hash != new_hash:
                continue
            del data[name]
        return data

    def gen_tree(self, length, filenames, codes):
        for i in xrange(0, length):
            d = Obj()
            d.name = filenames[i]
            d.content = lambda: codes[i]
            yield d

