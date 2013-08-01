#!/usr/local/bin/python2.7
#coding:utf-8

import os
import re
import logging
from functools import wraps
from sheep.api.local import reqcache
from flask import g, abort, url_for, redirect

import config
from utils.jagare import get_jagare
from utils.helper import Obj, generate_list_page
from utils.formatter import format_time, format_content
from query.organization import get_team_member, get_team_by_name, \
        get_team
from query.repos import get_repo_by_path, get_repo_commiter, get_repo

logger = logging.getLogger(__name__)
HEADER = re.compile(r"""^diff[ ]--git[ ]a/(?P<a_path>.+)[ ]b/(?P<b_path>.+)""")


# USE login_required first
def repo_required(admin=False, need_write=False):
    def _repo_required(f):
        @wraps(f)
        def _(organization, member, *args, **kwargs):
            teamname = kwargs.pop('tname', '')
            reponame = kwargs.pop('rname', '')
            if not reponame:
                raise abort(404)
            path = os.path.join(teamname, '%s.git' % reponame)
            repo = get_repo_by_path(organization.id, path)
            if not repo:
                raise abort(404)
            team = team_member = None
            if teamname:
                team = get_team_by_name(organization.id, teamname)
                team_member = get_team_member(repo.tid, g.current_user.id)
            role = check_admin(g.current_user, repo, member, team_member)
            kwargs['team'] = team
            kwargs['team_member'] = team_member
            kwargs['admin'] = role
            if admin and not role:
                url = url_for('repos.view', git=organization.git, rname=repo.name, tname=teamname)
                return redirect(url)
            read, write = check_permits(g.current_user, repo, member, team, team_member, role)
            if not read:
                raise abort(403)
            if need_write and not write:
                raise abort(403)
            set_repo_meta(organization, repo, team)
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

def key_formatter_maker(view_key):
    def key_formatter(*a, **kwargs):
        version = kwargs.get('version')
        path = kwargs.get('path')
        key = view_key
        if version:
            key += ':%s' % version
        if path:
            key += ':%s' % path
        return key
    return key_formatter

def get_url_maker(organization, repo, team, view):
    def _(version=None, path=None):
        return get_url(organization, repo, view, team=team, version=version or repo.default, path=path)
    return _

def set_repo_meta(organization, repo, team=None):
    meta = Obj()
    meta.watch = get_url(organization, repo, 'repos.watch', team=team)
    meta.unwatch = get_url(organization, repo, 'repos.unwatch', team=team)
    meta.watchers = get_url(organization, repo, 'repos.watchers', team=team)
    meta.view = get_url(organization, repo, 'repos.view', team=team)
    #meta.edit = get_url(organization, repo, 'repos.edit', team=team)
    #meta.fork = get_url(organization, repo, 'repos.fork', team=team)
    #meta.forks = get_url(organization, repo, 'repos.forks', team=team)
    meta.delete = get_url(organization, repo, 'repos.delete', team=team)
    meta.setting = get_url(organization, repo, 'repos.setting', team=team)
    meta.commiter = get_url(organization, repo, 'repos.commiters', team=team)
    meta.remove_commiter = get_url(organization, repo, 'repos.remove_commiter', team=team)
    meta.transport = get_url(organization, repo, 'repos.transport', team=team)
    meta.delete = get_url(organization, repo, 'repos.delete', team=team)
    meta.activities = get_url(organization, repo, 'repos.activities', team=team)
    meta.get_view = reqcache(key_formatter_maker('repos:view'))(get_url_maker(organization, repo, team, 'repos.view'))
    meta.get_blob = reqcache(key_formatter_maker('repos:blob'))(get_url_maker(organization, repo, team, 'repos.blob'))
    meta.get_raw = reqcache(key_formatter_maker('repos:raw'))(get_url_maker(organization, repo, team, 'repos.raw'))
    meta.get_commits = reqcache(key_formatter_maker('repos:commits'))(get_url_maker(organization, repo, team, 'repos.commits'))
    meta.get_commit = reqcache(key_formatter_maker('repos:commit'))(get_url_maker(organization, repo, team, 'repos.commit'))
    meta.get_delete_file = reqcache(key_formatter_maker('repos:delete:file'))(get_url_maker(organization, repo, team, 'repos.delete_file'))
    meta.get_edit_file = reqcache(key_formatter_maker('repos:edit:file'))(get_url_maker(organization, repo, team, 'repos.edit_file'))
    if repo.parent:
        parent = get_repo(repo.parent)
        #TODO valid check
        parent_team = get_team(parent.tid) if parent.tid else None
        meta.parent = set_repo_meta(organization, parent, team=parent_team)
    @reqcache('repo:commits:count:{gid}:{path}')
    def count_commits(gid, path):
        jagare = get_jagare(repo.id, repo.parent)
        error, ret = jagare.get_log(repo.get_real_path(), total=1, path=path)
        count = 0 if error else ret['total']
        return count
    meta.count_commits = lambda path: count_commits(repo.id, path)
    setattr(repo, 'meta', meta)

def get_url(organization, repo, view='repos.view', team=None, **kwargs):
    if repo.tid == 0:
        return url_for(view, git=organization.git, rname=repo.name, **kwargs)
    else:
        if not team:
            team = get_team(repo.tid)
        return url_for(view, git=organization.git, rname=repo.name, tname=team.name, **kwargs)

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

def get_submodule_url(submodule, sha):
    url = submodule['url']
    host = submodule['host']
    #TODO move to utils
    if host == '218.245.3.148':
        git, url = url.split('@', 1)
        _, name= url.split(':', 1)
        tname = None
        if '/' in name:
            tname, name = name.split('/', 1)
        #TODO not production
        url = 'http://%s:12307%s' % (host, url_for('repos.view', git=git, tname=tname, rname=name, version=sha))
    return url

def render_commits_page(repo, page=1, path=None):
    count = repo.meta.count_commits(path)
    has_prev = True if page > 1 else False
    has_next = True if page * config.COMMITS_PER_PAGE < count else False
    pages = count / config.COMMITS_PER_PAGE
    pages += 1 if count % config.COMMITS_PER_PAGE else 0
    list_page = generate_list_page(count, has_prev, has_next, page, pages)
    return list_page

def parse_raw_diff_patches(patches):
    result = []
    cur_patch_idx = -1
    find = -1
    for line in patches.splitlines():
        if line == '':
            continue
        if line.startswith('diff'):
            match = re.match(HEADER, line)
            if match:
                result.append({})
                cur_patch_idx += 1
                before = match.group('a_path')
                after = match.group('b_path')
                result[cur_patch_idx]['before'] = before
                result[cur_patch_idx]['after'] = after
            find = -1
            continue
        if line.startswith('@@'):
            result[cur_patch_idx]['diff'] = [line, ]
            find = 0
            continue
        if find < 0 or cur_patch_idx < 0:
            continue  # Lines before the real patch part
        result[cur_patch_idx]['diff'].append(line)
    return result

def get_tree_with_content(jagare, tree, repo, organization, render=True, version='master'):
    ret = []
    for d in tree:
        data = Obj()
        if d['type'] == 'blob':
            data.content, data.content_type, data.length = format_content(
                    jagare, repo, d['path'], render=render, version=version, \
            )
        else:
            continue
        data.name = d['name']
        data.sha = d['sha']
        data.type = d['type']
        data.ago = format_time(d['commit']['committer']['ts'])
        data.message = d['commit']['message'][:150]
        data.commit = d['commit']['sha']
        data.path = d['path']
        ret.append(data)
    return ret

