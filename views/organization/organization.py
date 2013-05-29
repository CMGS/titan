#!/usr/local/bin/python2.7
#coding:utf-8

import logging

from flask.views import MethodView
from flask import redirect, request, url_for, render_template

from utils.account import login_required

logger = logging.getLogger(__name__)

class Register(MethodView):
    decorators = [login_required(need=False)]
    def get(self):
        return render_template('organization.register.html')

