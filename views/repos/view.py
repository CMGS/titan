#!/usr/local/bin/python2.7
#coding:utf-8

import logging

from flask import g, url_for, abort, request, \
        stream_with_context, Response

from utils.jagare import get_jagare
from utils.repos import repo_required
from utils.helper import MethodView, Obj
from utils.account import login_required
from utils.organization import member_required

from query.repos import get_repo_watcher

logger = logging.getLogger(__name__)

class View(MethodView):
    decorators = [repo_required(), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, repo, **kwargs):
        version = kwargs.get('version', 'master')
        path = kwargs.get('path', '')
        team = kwargs.get('team', None)

        watcher = get_repo_watcher(g.current_user.id, repo.id)
        jagare = get_jagare(repo.id, repo.parent)
        tname = team.name if team else None

        error, tree = jagare.ls_tree(repo.get_real_path(), path=path, version=version)
        if not error:
            tree = self.render_tree(
                        tree, version, organization.git, \
                        tname, repo.name
                    )
            path = self.render_path(
                        path, version, organization.git, \
                        tname, repo.name
                    )
            kwargs['path'] = path
        return self.render_template(
                    member=member, repo=repo, \
                    organization=organization, \
                    watcher=watcher, \
                    tree=tree, error=error, \
                    **kwargs
                )

    def render_path(self, path, version, git, tname, rname):
        if not path:
            raise StopIteration()
        pre = ''
        paths = path.split('/')
        for i in paths[:-1]:
            p = i if not pre else '/'.join([pre, i])
            pre = p
            yield (i, url_for('repos.view', git=git, tname=tname, rname=rname, version=version, path=p))
        yield (paths[-1], '')

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
            yield data

class Blob(MethodView):
    decorators = [repo_required(), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, repo, path, **kwargs):
        version = kwargs.get('version', 'master')
        team = kwargs.get('team', None)

        watcher = get_repo_watcher(g.current_user.id, repo.id)
        jagare = get_jagare(repo.id, repo.parent)
        tname = team.name if team else None

        repo_path = repo.get_real_path()
        content = None
        error, tree = jagare.ls_tree(repo_path, path=path, version=version)
        if not error:
            error, content = self.get_file(repo_path, tree, jagare)
            if not error:
                kwargs['path'] = self.render_path(
                                    path, version, organization.git, \
                                    tname, repo.name
                                 )
        if not self.need_download(path, version, organization.git, tname, repo.name):
            return self.render_template(
                        member=member, repo=repo, \
                        organization=organization, \
                        watcher=watcher, \
                        content=content, error=error, **kwargs
                    )
        res = Response(stream_with_context(content))
        res.headers['X-Accel-Buffering'] = 'no'
        res.headers['Cache-Control'] = 'no-cache'
        res.headers['Content-Type'] = 'application/octet-stream'
        return res

    def need_download(self, path, version, git, tname, rname):
        if '/raw/' in request.url:
            return True
        return False

    def get_file(self, repo_path, tree, jagare):
        file_obj = tree[0]
        if file_obj['type'] != 'blob':
            raise abort(404)
        return jagare.cat(repo_path, file_obj['sha'])

    def render_path(self, path, version, git, tname, rname):
        if not path:
            raise StopIteration()
        pre = ''
        paths = path.split('/')
        for i in paths[:-1]:
            p = i if not pre else '/'.join([pre, i])
            pre = p
            yield (i, url_for('repos.view', git=git, tname=tname, rname=rname, version=version, path=p))
        yield (paths[-1], '')

