#!/usr/local/bin/python2.7
#coding:utf-8

from flask import request, g

from utils.helper import MethodView
from utils.account import login_required
from utils.organization import member_required

from query.account import get_user
from query.gists import get_organization_gists, get_user_watch_gists, \
    get_user_organization_gists

from utils.gists import get_url

class Explore(MethodView):
    decorators = [member_required(admin=False), login_required('account.login')]
    def get(self, organization, member):
        f = request.args.get('f', None)
        if f not in ['w', 'm']:
            f = None
        else:
            f = 0 if f == 'w' else 1

        return self.render_template(
                organization = organization, \
                member = member, \
                gists = self.get_gists(organization, f), \
        )

    def filter_gists(self, organization, f):
        if f is None:
            ret = get_organization_gists(organization.id)
        elif f == 0:
            ret = get_user_watch_gists(g.current_user.id, organization.id)
        elif f == 1:
            ret = get_user_organization_gists(organization.id, g.current_user.id)
        else:
            ret = []
        return ret

    def get_gists(self, organization, f=None):
        ret = self.filter_gists(organization, f)
        for r in ret:
            setattr(r, 'user', get_user(r.uid))
            setattr(r, 'view', get_url(organization, r))
            yield r

