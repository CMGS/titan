#!/usr/local/bin/python2.7
#coding:utf-8

import logging
from datetime import datetime

from flask import request, abort

from sheep.api.local import reqcache

import config
from utils.jagare import get_jagare
from utils.formatter import format_time
from utils.account import login_required
from utils.organization import member_required
from utils.helper import MethodView, Obj, get_avatar
from utils.repos import repo_required, get_branches, \
        render_commits_page, get_url

from query.account import get_user_from_alias

logger = logging.getLogger(__name__)

class Commits(MethodView):
    #TODO not support filter by path
    decorators = [repo_required(), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, repo, admin, team, team_member, version=None):
        page = request.args.get('p', 1)
        try:
            page = int(page)
        except ValueError:
            raise abort(403)
        version = version or repo.default

        jagare = get_jagare(repo.id, repo.parent)
        error, commits = jagare.get_log(
                repo.get_real_path(), page=page, \
                size=config.COMMITS_PER_PAGE, shortstat=1, \
                start=version,
        )
        if not commits:
            raise abort(404)

        list_page = render_commits_page(repo, page)
        commits = self.render_commits(jagare, organization, repo, commits, list_page)
        return self.render_template(
                    member=member, repo=repo, \
                    organization=organization, \
                    branches=get_branches(repo, jagare), \
                    error=error, \
                    version=version, \
                    admin=admin, team=team, team_member=team_member, \
                    commits=commits, \
                    list_page=list_page, \
                )

    def render_commits(self, jagare, organization, repo, commits, list_page):
        pre = None
        for commit in commits:
            self.render_commit(commit, organization, repo)
            if not pre:
                pre = commit
            else:
                commit['pre'] = pre
                pre = commit
            yield commit

    def render_commit(self, commit, organization, repo):
        commit['view'] = get_url(organization, repo, version=commit['sha'])
        commit['author_date'] = datetime.fromtimestamp(float(commit['author_time'])).date()
        commit['author_time'] = format_time(commit['author_time'])
        author = reqcache.get(commit['author_email'])
        if not author:
            author = get_user_from_alias(commit['author_email'])
            reqcache.set(commit['author_email'], author)
        if not author:
            author = Obj()
            author.email = commit['author_email']
            author.name = None
            author.avatar = lambda size:get_avatar(author.email, size)
        commit['author'] = author

