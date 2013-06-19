#!/usr/local/bin/python2.7
#coding:utf-8

import logging

from utils.helper import MethodView
from utils.account import login_required
from utils.organization import member_required

from query.organization import get_teams_by_ogranization

logger = logging.getLogger(__name__)

class Create(MethodView):
    decorators = [member_required(admin=False), login_required('account.login')]
    def get(self, organization, members):
        teams = get_teams_by_ogranization(organization.id)
        return self.render_template(organization=organization, teams=teams)

    def post(self, organization, members):
        name = request.form.get('name', None)
        path = request.form.get('path', None)

