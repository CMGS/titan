#!/usr/local/bin/python2.7
#coding:utf-8

import os
import logging

from flask import g, redirect, request

from utils import code
from utils.jagare import get_jagare
from utils.account import login_required
from utils.organization import member_required
from utils.helper import MethodView
from utils.formatter import format_content
from utils.repos import repo_required, get_branches, \
        render_path

from query.repos import update_file, get_repo_watcher

logger = logging.getLogger(__name__)

class AddFile(MethodView):
    decorators = [repo_required(need_write=True), member_required(admin=False), login_required('account.login')]
    def post(self, organization, member, repo, admin, team, team_member, version=None, path=None):
        pass

class EditFile(MethodView):
    decorators = [repo_required(need_write=True), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, repo, admin, team, team_member, version=None, path=None):
        return self.edit(organization, member, repo, admin, team, team_member, version, path)

    def post(self, organization, member, repo, admin, team, team_member, version=None, path=None):
        filename = request.form.get('filename')
        content = request.form.get('content')
        if not filename or not content:
            return self.edit(
                    organization, member, repo, admin, team, \
                    team_member, version, path, \
                    error_message=code.REPOS_EDIT_WITHOUT_INFO
            )
        new_path = os.path.join(path.rsplit('/', 1)[0] if '/' in path else '', filename)
        data = {new_path: content}
        if path != new_path:
            data[path] = ''
        error = update_file(
                organization, \
                g.current_user, \
                repo, data, \
                version, \
                '%s %s' % (code.REPOS_EDIT_FILE, path)
        )
        if error:
            return self.edit(
                    organization, member, repo, admin, team, \
                    team_member, version, path, \
                    error_message=code.REPOS_EDIT_FAILED, \
            )
        return redirect(repo.meta.get_blob(version=version, path=new_path))

    def edit(self, organization, member, repo, admin, team, team_member, version=None, path=None, error_message=None):
        watcher = get_repo_watcher(g.current_user.id, repo.id)
        jagare = get_jagare(repo.id, repo.parent)
        tname = team.name if team else None
        content, content_type, _ = format_content(jagare, repo, path, version=version, render=False)
        return self.render_template(
                    member=member, repo=repo, \
                    organization=organization, \
                    file_path=path, \
                    watcher=watcher, \
                    content=content, \
                    content_type=content_type, \
                    branches=get_branches(repo, jagare), \
                    version=version, \
                    path = render_path(
                                path, version, organization.git, \
                                tname, repo.name
                            ), \
                    error_message=error_message, \
                )


class DeleteFile(MethodView):
    decorators = [repo_required(need_write=True), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, repo, admin, team, team_member, version=None, path=None):
        jagare = get_jagare(repo.id, repo.parent)
        error, tree = jagare.ls_tree(repo.get_real_path(), path=path, version=version, with_commit=None)
        if not error and len(tree['content']) == 1 and tree['content'][0]['type'] == 'blob':
            error = update_file(
                    organization, \
                    g.current_user, \
                    repo, {path: ''}, \
                    version, \
                    '%s %s' % (code.REPOS_DELETE_FILE, path)
            )
            if not error:
                path=path.rsplit('/', 1)[0] if '/' in path else None
        return redirect(repo.meta.get_view(version=version, path=path))

