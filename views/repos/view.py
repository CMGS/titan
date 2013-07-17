#!/usr/local/bin/python2.7
#coding:utf-8

import base64
import logging

from flask import g, url_for, abort, \
        Response, stream_with_context, request

from utils.jagare import get_jagare
from utils.helper import MethodView, Obj
from utils.account import login_required
from utils.organization import member_required
from utils.activities import render_push_action
from utils.timeline import render_activities_page
from utils.repos import repo_required, format_time, \
        format_content

from libs.code import render_code
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
    def get(self, organization, member, repo, path=None, **kwargs):
        version = kwargs.get('version', repo.default)
        team = kwargs.get('team', None)
        file_path = path

        watcher = get_repo_watcher(g.current_user.id, repo.id)
        jagare = get_jagare(repo.id, repo.parent)
        tname = team.name if team else None

        error, tree = jagare.ls_tree(repo.get_real_path(), path=path, version=version)
        readme = None
        if not error:
            tree, meta = tree['content'], tree['meta']
            readme, tree = self.render_tree(
                                jagare, \
                                repo, organization, \
                                tree, version, tname, \
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
                    watcher=watcher, file_path=file_path, \
                    branches=get_branches(repo, jagare), \
                    tree=tree, error=error, \
                    readme=readme,
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

    def render_tree(self, jagare, repo, organization, tree, version, tname):
        ret = []
        readme = None
        for d in tree:
            data = Obj()
            if d['type'] == 'tree':
                data.url = url_for('repos.view', git=organization.git, tname=tname, rname=repo.name, version=version, path=d['path'])
            elif d['type'] == 'blob':
                data.url = url_for('repos.blob', git=organization.git, tname=tname, rname=repo.name, version=version, path=d['path'])
                if d['name'].startswith('README.'):
                    readme, content_type, _ = format_content(jagare, repo, d['path'], version=version)
                    if content_type != 'file':
                        readme = None
            elif d['type'] == 'submodule':
                data.url = self.get_submodule_url(d['submodule'], d['sha'])
                d['name'] = '%s@%s' % (d['name'], d['sha'][:10])
            data.name = d['name']
            data.sha = d['sha']
            data.type = d['type']
            data.ago = format_time(d['commit']['committer']['ts'])
            data.message = d['commit']['message'][:150]
            data.commit = d['commit']['sha']
            data.path = d['path']
            ret.append(data)
        return readme, ret

    def get_submodule_url(self, submodule, sha):
        url = submodule['url']
        host = submodule['host']
        if host == '218.245.3.148':
            git, url = url.split('@', 1)
            _, name= url.split(':', 1)
            tname = None
            if '/' in name:
                tname, name = name.split('/', 1)
            #TODO not production
            url = 'http://%s:12307%s' % (host, url_for('repos.view', git=git, tname=tname, rname=name, version=sha))
        return url

class Blob(MethodView):
    decorators = [repo_required(), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, repo, path, **kwargs):
        version = kwargs.get('version', repo.default)
        team = kwargs.get('team', None)

        watcher = get_repo_watcher(g.current_user.id, repo.id)
        jagare = get_jagare(repo.id, repo.parent)
        tname = team.name if team else None

        content, content_type, content_length = format_content(jagare, repo, path, version=version)
        kwargs['path'] = render_path(
                            path, version, organization.git, \
                            tname, repo.name
                        )

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

class Activities(MethodView):
    decorators = [repo_required(), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, repo, **kwargs):
        page = request.args.get('p', 1)
        try:
            page = int(page)
        except ValueError:
            raise abort(403)
        data, list_page = render_activities_page(page, t='repo', repo=repo)
        return self.render_template(
                    data=self.render_activities(data, organization, repo, kwargs), \
                    list_page=list_page, \
                    member=member, repo=repo, \
                    organization=organization, \
                    **kwargs
                )

    def render_activities(self, data, organization, repo, kwargs):
        for action, original, timestamp in data:
            if action['type'] == 'push':
                yield render_push_action(action, organization, repo=repo, team=kwargs.get('team'))
            else:
                #TODO for merge data
                continue

