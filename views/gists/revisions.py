#!/usr/local/bin/python2.7
#coding:utf-8

import logging

from sheep.api.local import reqcache

from libs.code import render_diff
from utils.jagare import get_jagare
from utils.repos import format_time
from utils.helper import MethodView, Obj
from utils.account import login_required
from utils.gists import gist_require, get_url
from utils.organization import member_required

from query.account import get_user_from_alias

logger = logging.getLogger(__name__)

class Revisions(MethodView):
    decorators = [gist_require(owner=True), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, gist, private=None):
        jagare = get_jagare(gist.id, gist.parent)
        error, revisions = jagare.get_log(gist.get_real_path())
        if not error:
            revisions = self.render_revisions(jagare, organization, gist, revisions)
        return self.render_template(
                    organization=organization, \
                    member=member, \
                    error=error, \
                    revisions=revisions, \
                    gist=gist, \
                )

    def render_revisions(self, jagare, organization, gist, revisions):
        for rev in revisions[:-1]:
            self.render_rev(rev, organization, gist)
            rev['type'] = 'update'
            yield rev
        rev = revisions[-1]
        self.render_rev(rev, organization, gist)
        rev['type'] = 'create'
        yield rev

    def render_rev(self, rev, organization, gist):
        rev['view'] = get_url(organization, gist, version=rev['sha'])
        rev['committer_time'] = format_time(rev['committer_time'])
        author = reqcache.get(rev['author_email'])
        if not author:
            author = get_user_from_alias(rev['author_email'])
            reqcache.set(rev['author_email'], author)
        if not author:
            author = Obj()
            author.email = rev['author_email']
            author.name = None
        rev['author'] = author
        rev['diff'] = render_diff(rev['diff'])

