#!/usr/local/bin/python2.7
#coding:utf-8

from flask import Blueprint
from utils.helper import get_as_view
from views.organization.organization import Register, Invite, View, Setting

MODULE_NAME = 'organization'
as_view = get_as_view(MODULE_NAME)

organization = Blueprint(MODULE_NAME, __name__)

view = as_view(View)
invite = as_view(Invite)
setting = as_view(Setting)
register = as_view(Register)

organization.add_url_rule('/<git>/', view_func=view, methods=['GET', ])
organization.add_url_rule('/<git>/setting/', view_func=setting, methods=['GET', 'POST'])
organization.add_url_rule('/<git>/invite/', view_func=invite, methods=['GET', 'POST'])
organization.add_url_rule('/register/', view_func=register, methods=['GET', 'POST'])

