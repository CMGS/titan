#!/usr/local/bin/python2.7
#coding:utf-8

import os
import logging

from flask import g, redirect, request, abort

from utils import code
from utils.helper import MethodView
from utils.jagare import get_jagare
from utils.account import login_required
from utils.formatter import format_content
from utils.organization import member_required
from utils.repos import repo_required, get_branches, \
        render_path, check_obj_type

from query.repos import update_file, get_repo_watcher

logger = logging.getLogger(__name__)

class NewFile(MethodView):
    decorators = [repo_required(need_write=True), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, repo, admin, team, team_member, version=None, path=None):
        if not check_obj_type(repo, path, version, 'tree'):
            raise abort(403)
        return self.add(organization, repo, team, version, path)

    def post(self, organization, member, repo, admin, team, team_member, version=None, path=None):
        if not check_obj_type(repo, path, version, 'tree'):
            raise abort(403)
        filename = request.form.get('filename')
        content = request.form.get('content')
        if not filename or not content:
            return self.add(
                    organization, repo, team, version, path, \
                    filename=filename, content=content, \
                    error_message=code.REPOS_EDIT_WITHOUT_INFO
            )
        new_path = os.path.join(path if path else '', filename)
        data = {new_path: content}
        error = update_file(
                organization, \
                g.current_user, \
                repo, data, \
                version, \
                '%s %s' % (code.REPOS_NEW_FILE, new_path)
        )
        if error:
            return self.add(
                    organization, repo, team, version, path, \
                    filename=filename, content=content, \
                    error_message=code.REPOS_EDIT_FAILED
            )

        return redirect(repo.meta.get_blob(version=version, path=new_path))

    def add(self, organization, repo, team, version=None, path=None, error_message=None, content='', filename=''):
        watcher = get_repo_watcher(g.current_user.id, repo.id)
        tname = team.name if team else None
        return self.render_template(
                    repo=repo, \
                    organization=organization, \
                    file_path=path, \
                    watcher=watcher, \
                    content=content, \
                    branches=get_branches(repo), \
                    version=version, \
                    filename=filename, \
                    path = render_path(
                                path, version, organization.git, \
                                tname, repo.name
                            ), \
                    error_message=error_message, \
                )

class EditFile(MethodView):
    decorators = [repo_required(need_write=True), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, repo, admin, team, team_member, version=None, path=None):
        if not check_obj_type(repo, path, version, 'blob'):
            raise abort(403)
        return self.edit(organization, repo, team, version, path)

    def post(self, organization, member, repo, admin, team, team_member, version=None, path=None):
        if not check_obj_type(repo, path, version, 'blob'):
            raise abort(403)
        filename = request.form.get('filename')
        content = request.form.get('content')
        if not filename or not content:
            return self.edit(
                    organization, repo, team, \
                    version, path, \
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
                    organization, repo, team, \
                    version, path, \
                    error_message=code.REPOS_EDIT_FAILED, \
            )
        return redirect(repo.meta.get_blob(version=version, path=new_path))

    def edit(self, organization, repo, team, version=None, path=None, error_message=None):
        watcher = get_repo_watcher(g.current_user.id, repo.id)
        jagare = get_jagare(repo.id, repo.parent)
        tname = team.name if team else None
        content, content_type, _ = format_content(jagare, repo, path, version=version, render=False)
        return self.render_template(
                    repo=repo, \
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
        if not check_obj_type(repo, path, version, 'blob'):
            raise abort(403)
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

