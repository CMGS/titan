#!/usr/local/bin/python2.7
#coding:utf-8

import base64
import logging

from flask import g, url_for, abort, \
        Response, stream_with_context

from utils.jagare import get_jagare
from utils.helper import MethodView, Obj
from utils.account import login_required
from utils.organization import member_required
from utils.repos import repo_required, format_time

from query.repos import get_repo_watcher
from query.account import get_user, get_alias_by_email

logger = logging.getLogger(__name__)

def render_path(path, version, git, tname, rname):
    if not path:
        raise StopIteration()
    pre = ''
    paths = path.split('/')
    for i in paths[:-1]:
        p = i if not pre else '/'.join([pre, i])
        pre = p
        yield (i, url_for('repos.view', git=git, tname=tname, rname=rname, version=version, path=p))
    yield (paths[-1], '')

def get_branches(repo, jagare=None):
    if not jagare:
        jagare = get_jagare(repo.id, repo.parent)
    return jagare.get_branches_names(repo.get_real_path())

class View(MethodView):
    decorators = [repo_required(), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, repo, **kwargs):
        version = kwargs.get('version', repo.default)
        path = kwargs.get('path', '')
        team = kwargs.get('team', None)

        watcher = get_repo_watcher(g.current_user.id, repo.id)
        jagare = get_jagare(repo.id, repo.parent)
        tname = team.name if team else None

        error, tree = jagare.ls_tree(repo.get_real_path(), path=path, version=version)
        if not error:
            tree, meta = tree['content'], tree['meta']
            tree = self.render_tree(
                        tree, version, organization.git, \
                        tname, repo.name
                    )
            path = render_path(
                        path, version, organization.git, \
                        tname, repo.name
                    )
            kwargs['commit'] = self.get_commit_user(meta)
            kwargs['path'] = path
        return self.render_template(
                    member=member, repo=repo, \
                    organization=organization, \
                    watcher=watcher, \
                    branches=get_branches(repo, jagare), \
                    tree=tree, error=error, \
                    **kwargs
                )

    def get_commit_user(self, meta):
        user = Obj()
        commit = Obj()
        user.name = meta['committer']['name']
        user.email = meta['committer']['email']
        user.avatar = None
        commit.message = meta['message']
        commit.user = user
        commit.sha = meta['sha']
        commit.date = meta['committer']['date']
        alias = get_alias_by_email(user.email)
        if alias:
            user = get_user(alias.uid)
            commit.user.name = user.name
            commit.user.avatar = user.avatar(18)
        return commit

    def render_tree(self, tree, version, git, tname, rname):
        for d in tree:
            data = Obj()
            if d['type'] == 'tree':
                data.url = url_for('repos.view', git=git, tname=tname, rname=rname, version=version, path=d['path'])
            elif d['type'] == 'blob':
                #TODO blob reader
                data.url = url_for('repos.blob', git=git, tname=tname, rname=rname, version=version, path=d['path'])
            else:
                continue
            data.name = d['name']
            data.sha = d['sha']
            data.type = d['type']
            data.ago = format_time(d['commit']['committer']['ts'])
            data.message = d['commit']['message'][:150]
            data.commit = d['commit']['sha']
            yield data

class Blob(MethodView):
    decorators = [repo_required(), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, repo, path, **kwargs):
        version = kwargs.get('version', repo.default)
        team = kwargs.get('team', None)

        watcher = get_repo_watcher(g.current_user.id, repo.id)
        jagare = get_jagare(repo.id, repo.parent)
        tname = team.name if team else None

        repo_path = repo.get_real_path()
        error, res = jagare.cat_file(repo_path, path, version=version)
        if error:
            raise abort(error)
        kwargs['path'] = render_path(
                            path, version, organization.git, \
                            tname, repo.name
                        )

        content = res.content
        content_type = res.headers.get('content-type', 'application/octet-stream')
        content_length = float(res.headers.get('content-length', 0.0)) / 1024
        if 'image' in content_type:
            content_type = 'image'
            content = base64.b64encode(content)
        elif 'text' in content_type:
            content_type = 'file'
            if not isinstance(content, unicode):
                content = content.decode('utf8')
        else:
            content_type = 'binary'

        return self.render_template(
                    member=member, repo=repo, \
                    organization=organization, \
                    watcher=watcher, file_path=path, \
                    branches=get_branches(repo, jagare), \
                    content=content, \
                    content_length=content_length, \
                    content_type=content_type, \
                    **kwargs
                )

class Raw(MethodView):
    decorators = [repo_required(), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, repo, path, **kwargs):
        version = kwargs.get('version', repo.default)
        jagare = get_jagare(repo.id, repo.parent)
        repo_path = repo.get_real_path()
        error, res = jagare.cat_file(repo_path, path, version=version)
        if error:
            raise abort(error)
        resp = Response(stream_with_context(res))
        resp.headers['X-Accel-Buffering'] = 'no'
        resp.headers['Cache-Control'] = 'no-cache'
        resp.headers['Content-Type'] = res.headers.get('content-type', 'application/octet-stream')
        return resp

