#!/usr/local/bin/python2.7
#coding:utf-8

from flask import Blueprint
from flaskext.csrf import csrf_exempt

from views.organization.organization import Register, Invite, View

organization = Blueprint('organization', __name__)

view = View.as_view('view')
invite = Invite.as_view('invite')
register = Register.as_view('register')

organization.add_url_rule('/<int:oid>/', view_func=view, methods=['GET', ])
organization.add_url_rule('/<int:oid>/invite/', view_func=invite, methods=['GET', 'POST'])
organization.add_url_rule('/register/', view_func=register, methods=['GET', 'POST'])

