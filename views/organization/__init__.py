#!/usr/local/bin/python2.7
#coding:utf-8

from flask import Blueprint
from utils.helper import make_view
from views.organization.team import CreateTeam, JoinTeam, \
        QuitTeam, ViewTeam, SetTeam
from views.organization.organization import Register, Invite, View, Setting

MODULE_NAME = 'organization'
view_func = make_view(MODULE_NAME)

organization = Blueprint(MODULE_NAME, __name__)

view = view_func(View)
invite = view_func(Invite)
setting = view_func(Setting)
register = view_func(Register)

set_team = view_func(SetTeam)
join_team = view_func(JoinTeam)
quit_team = view_func(QuitTeam)
view_team = view_func(ViewTeam)
create_team = view_func(CreateTeam)

organization.add_url_rule('/<git>/', view_func=view, methods=['GET', ])
organization.add_url_rule('/<git>/setting/', view_func=setting, methods=['GET', 'POST'])
organization.add_url_rule('/<git>/invite/', view_func=invite, methods=['GET', 'POST'])
organization.add_url_rule('/<git>/team/create/', view_func=create_team, methods=['GET', 'POST'])
organization.add_url_rule('/<git>/team/<int:tid>/', view_func=view_team, methods=['GET', ])
organization.add_url_rule('/<git>/team/join/<int:tid>/', view_func=join_team, methods=['POST', ])
organization.add_url_rule('/<git>/team/quit/<int:tid>/', view_func=quit_team, methods=['POST', ])
organization.add_url_rule('/<git>/team/setting/<int:tid>/', view_func=set_team, methods=['GET', 'POST'])
organization.add_url_rule('/register', view_func=register, methods=['GET', 'POST'])

