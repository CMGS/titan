#!/usr/local/bin/python2.7
#coding:utf-8

import os
import logging
from flask import g, abort, url_for, redirect

from functools import wraps
from query.repos import get_repo_by_path, get_repo_commiter
from query.organization import get_team_member, get_team_by_name, \
        get_team

logger = logging.getLogger(__name__)

# USE login_required first
def repo_required(admin=False, need_write=False):
    def _repo_required(f):
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
            team = team_member = None
            if teamname:
                team = get_team_by_name(organization.id, teamname)
                team_member = get_team_member(repo.tid, g.current_user.id)
                kwargs['team'] = team
                kwargs['team_member'] = team_member
            role = check_admin(g.current_user, repo, member, team_member)
            kwargs['admin'] = role
            if admin and not role:
                url = url_for('repos.view', git=organization.git, rname=repo.name, tname=teamname)
                return redirect(url)
            read, write = check_permits(g.current_user, repo, member, team, team_member, role)
            if not read:
                raise abort(403)
            if need_write and not write:
                raise abort(403)
            return f(organization, member, repo, *args, **kwargs)
        return _
    return _repo_required

def check_admin(user, repo, member, team_member):
    if repo.uid == user.id:
        return True
    elif member.admin:
        return True
    elif team_member and team_member.admin:
        return True
    else:
        return False

def check_permits(user, repo, member, team=None, team_member=None, role=None):
    if role is None and check_admin(user, repo, member, team_member):
            return True, True
    elif role:
        return True, True
    commiter = get_repo_commiter(user.id, repo.id)
    if commiter:
        return True, True
    if team:
        if team_member or not team.private:
            return True, False
        elif not team_member and team.private:
            return False, False
    else:
        return True, False

def get_url(organization, repo, view='repos.view', team=None, **kwargs):
    if repo.tid == 0:
        return url_for(view, git=organization.git, rname=repo.name, **kwargs)
    else:
        if not team:
            team = get_team(repo.tid)
        return url_for(view, git=organization.git, rname=repo.name, tname=team.name, **kwargs)

