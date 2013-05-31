#!/usr/local/bin/python2.7
#coding:utf-8

from flask import Blueprint
from utils.helper import make_view
from views.organization.organization import Register, Invite, View, Setting

MODULE_NAME = 'organization'
view_func = make_view(MODULE_NAME)

organization = Blueprint(MODULE_NAME, __name__)

view = view_func(View)
invite = view_func(Invite)
setting = view_func(Setting)
register = view_func(Register)

organization.add_url_rule('/<git>/', view_func=view, methods=['GET', ])
organization.add_url_rule('/<git>/setting/', view_func=setting, methods=['GET', 'POST'])
organization.add_url_rule('/<git>/invite/', view_func=invite, methods=['GET', 'POST'])
organization.add_url_rule('/register/', view_func=register, methods=['GET', 'POST'])

