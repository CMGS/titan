#!/usr/local/bin/python2.7
#coding:utf-8

from flask import Blueprint
from utils.helper import make_view
from views.repos.repos import Create

MODULE_NAME = 'repos'
view_func = make_view(MODULE_NAME)

repos = Blueprint(MODULE_NAME, __name__)

create = view_func(Create)

repos.add_url_rule('/<git>/new', view_func=create, methods=['GET', 'POST'])

