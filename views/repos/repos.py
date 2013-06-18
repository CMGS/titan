#!/usr/local/bin/python2.7
#coding:utf-8

import logging

from utils.helper import MethodView
from utils.account import login_required
from utils.organization import member_required

logger = logging.getLogger(__name__)

class Create(MethodView):
    decorators = [member_required(admin=False), login_required('account.login')]
    def get(self, organization, members):
        pass

    def post(self, organization, members):
        pass
