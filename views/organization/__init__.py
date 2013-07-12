#!/usr/local/bin/python2.7
#coding:utf-8

from flask import Blueprint
from utils.helper import make_view
from views.organization.team import CreateTeam, JoinTeam, \
        QuitTeam, ViewTeam, SetTeam, AddMember
from views.organization.organization import Create, Invite, View, \
        Setting, Teams, Public

MODULE_NAME = 'organization'
view_func = make_view(MODULE_NAME)

organization = Blueprint(MODULE_NAME, __name__)

public = view_func(Public)
view = view_func(View)
teams = view_func(Teams)
invite = view_func(Invite)
setting = view_func(Setting)
create = view_func(Create)

join_team = view_func(JoinTeam)
quit_team = view_func(QuitTeam)
add_member = view_func(AddMember, module='team', tmpl='add')
view_team = view_func(ViewTeam, module='team', tmpl='view')
set_team = view_func(SetTeam, module='team', tmpl='setting')
create_team = view_func(CreateTeam, module='team', tmpl='create')

organization.add_url_rule('/create', view_func=create, methods=['GET', 'POST'])
organization.add_url_rule('/<git>/', view_func=view, methods=['GET', ])
organization.add_url_rule('/<git>/public', view_func=public, methods=['GET', ])
organization.add_url_rule('/<git>/teams', view_func=teams, methods=['GET', ])
organization.add_url_rule('/<git>/invite', view_func=invite, methods=['GET', 'POST'])
organization.add_url_rule('/<git>/create', view_func=create_team, methods=['GET', 'POST'])
organization.add_url_rule('/<git>/setting', view_func=setting, methods=['GET', 'POST'])
organization.add_url_rule('/<git>/<tname>/', view_func=view_team, methods=['GET', ])
organization.add_url_rule('/<git>/<tname>/add', view_func=add_member, methods=['GET', 'POST'])
organization.add_url_rule('/<git>/<tname>/join', view_func=join_team, methods=['POST', ])
organization.add_url_rule('/<git>/<tname>/quit', view_func=quit_team, methods=['POST', ])
organization.add_url_rule('/<git>/<tname>/setting', view_func=set_team, methods=['GET', 'POST'])

