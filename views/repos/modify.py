#!/usr/local/bin/python2.7
#coding:utf-8

import logging

from flask import g, redirect

from utils import code
from utils.jagare import get_jagare
from utils.account import login_required
from utils.organization import member_required
from utils.helper import MethodView
from utils.repos import repo_required, get_tree_with_content

from query.repos import update_file

logger = logging.getLogger(__name__)

class AddFile(MethodView):
    decorators = [repo_required(need_write=True), member_required(admin=False), login_required('account.login')]
    def post(self, organization, member, repo, admin, team, team_member, version=None, path=None):
        pass

class EditFile(MethodView):
    decorators = [repo_required(need_write=True), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, repo, admin, team, team_member, version=None, path=None):
        jagare = get_jagare(repo.id, repo.parent)
        error, tree = jagare.ls_tree(repo.get_real_path(), path=path, version=version, with_commit=None)
        if not error:
            tree, meta = tree['content'], tree['meta']
            tree = get_tree_with_content(jagare, tree, repo, organization, render=False, version=version)

    def post(self, organization, member, repo, admin, team, team_member, version=None, path=None):
        pass

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

