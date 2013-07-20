#!/usr/local/bin/python2.7
#coding:utf-8

import logging

from views.gists.gists import get_url

from utils.repos import format_time
from utils.gists import gist_require
from utils.helper import MethodView, Obj
from utils.account import login_required
from utils.organization import member_required
from utils.jagare import get_jagare

from query.account import get_user_from_alias

logger = logging.getLogger(__name__)

class Revisions(MethodView):
    decorators = [gist_require(owner=True), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, gist, private=None):
        jagare = get_jagare(gist.id, gist.parent)
        error, revisions = jagare.get_log(gist.get_real_path())
        if not error:
            revisions = self.render_revisions(revisions)
        return self.render_template(
                    organization=organization, \
                    member=member, \
                    error=error, \
                    revisions=revisions, \
                    gist=gist, \
                    url=get_url(organization, gist), \
                )

    def render_revisions(self, revisions):
        for rev in revisions:
            rev['committer_time'] = format_time(rev['committer_time'])
            author = get_user_from_alias(rev['author_email'])
            if not author:
                author = Obj()
                author.email = rev['author_email']
                author.name = None
            rev['author'] = author
            yield rev

