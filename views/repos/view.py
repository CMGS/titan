#!/usr/local/bin/python2.7
#coding:utf-8

import logging

from flask import g, url_for, abort, \
        Response, stream_with_context, request

from utils.jagare import get_jagare
from utils.helper import MethodView, Obj
from utils.account import login_required
from utils.organization import member_required
from utils.activities import render_push_action, \
        render_activities_page
from utils.formatter import format_content, format_time
from utils.repos import repo_required, get_branches, render_path, \
        get_submodule_url

from query.repos import get_repo_watcher
from query.account import get_user, get_alias_by_email

logger = logging.getLogger(__name__)

class View(MethodView):
    decorators = [repo_required(), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, repo, admin, team, team_member, version=None, path=None):
        version = version or repo.default
        file_path = path

        watcher = get_repo_watcher(g.current_user.id, repo.id)
        jagare = get_jagare(repo.id, repo.parent)
        tname = team.name if team else None

        error, tree = jagare.ls_tree(repo.get_real_path(), path=path, version=version)
        readme = None
        commit = None
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
            commit = self.get_commit_user(meta)
        return self.render_template(
                    member=member, repo=repo, \
                    organization=organization, \
                    watcher=watcher, file_path=file_path, \
                    branches=get_branches(repo, jagare), \
                    tree=tree, error=error, \
                    readme=readme, \
                    version=version, \
                    admin=admin, team=team, team_member=team_member, \
                    path=path, commit=commit, \
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
                data.url = get_submodule_url(d['submodule'], d['sha'])
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

class Blob(MethodView):
    decorators = [repo_required(), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, repo, admin, team, team_member, version, path):
        watcher = get_repo_watcher(g.current_user.id, repo.id)
        jagare = get_jagare(repo.id, repo.parent)
        tname = team.name if team else None

        content, content_type, content_length = format_content(jagare, repo, path, version=version)

        return self.render_template(
                    member=member, repo=repo, \
                    organization=organization, \
                    watcher=watcher, file_path=path, \
                    branches=get_branches(repo, jagare), \
                    content=content, \
                    content_length=content_length, \
                    content_type=content_type, \
                    admin=admin, team=team, team_member=team_member, \
                    version=version, \
                    path=render_path(
                            path, version, organization.git, tname, repo.name
                    )
                )

class Raw(MethodView):
    decorators = [repo_required(), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, repo, admin, team, team_member, version, path):
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
    def get(self, organization, member, repo, admin, team, team_member):
        page = request.args.get('p', 1)
        try:
            page = int(page)
        except ValueError:
            raise abort(403)
        data, list_page = render_activities_page(page, t='repo', repo=repo)
        return self.render_template(
                    data=self.render_activities(data, organization, repo, team), \
                    list_page=list_page, \
                    member=member, repo=repo, \
                    organization=organization, \
                    admin=admin, team=team, team_member=team_member, \
                )

    def render_activities(self, data, organization, repo, team):
        for action, original, timestamp in data:
            if action['type'] == 'push':
                yield render_push_action(action, organization, repo=repo, team=team)
            else:
                #TODO for merge data
                continue

