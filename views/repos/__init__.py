#!/usr/local/bin/python2.7
#coding:utf-8

from flask import Blueprint
from utils.helper import make_view
from views.repos.repos import Create, View

MODULE_NAME = 'repos'
view_func = make_view(MODULE_NAME)

repos = Blueprint(MODULE_NAME, __name__)

view = view_func(View)
create = view_func(Create)

repos.add_url_rule('/<git>/new', view_func=create, methods=['GET', 'POST'])
repos.add_url_rule('/<git>/<rname>/', view_func=view, methods=['GET'])
repos.add_url_rule('/<git>/<tname>/<rname>/', view_func=view, methods=['GET'])

