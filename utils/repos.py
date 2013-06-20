#!/usr/local/bin/python2.7
#coding:utf-8

import os
from flask import g, abort

from functools import wraps
from query.repos import get_repo_by_path
from query.organization import get_team_member

# USE login_required first
def repo_required(f):
    @wraps(f)
    def _(organization, member, *args, **kwargs):
        teamname = kwargs.pop('tname', '')
        reponame = kwargs.pop('rname', '')
        path = os.path.join(teamname, '%s.git' % reponame)
        if not reponame:
            raise abort(404)
        repo = get_repo_by_path(organization.id, path)
        if not repo:
            raise abort(404)
        #TODO repo permits!
        #if repo.tid:
        #    team_member = get_team_member(repo.tid, g.current_user.id)
        #admin = member.admin or team_member.admin
        admin = member.admin
        return f(organization, member, repo, *args, **kwargs)
    return _

