#!/usr/local/bin/python2.7
#coding:utf-8

from flask import Blueprint
from flaskext.csrf import csrf_exempt

from utils.helper import make_view
from views.account.setting import Setting
from views.account.keys import Keys, DelKey
from views.account.forget import Forget, Reset
from views.account.account import Register, Login, Logout
from views.account.alias import Alias, VerifyAlias, DelAlias

MODULE_NAME = 'account'

view_func = make_view(MODULE_NAME)
account = Blueprint(MODULE_NAME, __name__)

reset = view_func(Reset)
setting = view_func(Setting)
register = view_func(Register)
login = csrf_exempt(view_func(Login))
forget = csrf_exempt(view_func(Forget))
logout = csrf_exempt(view_func(Logout))

keys = view_func(Keys, module='keys', tmpl='index')
delete_key = view_func(DelKey, module='keys', tmpl='delete')

alias = view_func(Alias, module='alias', tmpl='index')
verify_alias = view_func(VerifyAlias, module='alias', tmpl='verify')
delete_alias = view_func(DelAlias, module='alias', tmpl='delete')

account.add_url_rule('/login', view_func=login, methods=['GET', 'POST'])
account.add_url_rule('/logout', view_func=logout, methods=['GET'])
account.add_url_rule('/forget', view_func=forget, methods=['GET', 'POST'])
account.add_url_rule('/reset/<stub>', view_func=reset, methods=['GET', 'POST'])
account.add_url_rule('/register/<stub>', view_func=register, methods=['GET', 'POST'])

account.add_url_rule('/settings', view_func=setting, methods=['GET', 'POST'])
account.add_url_rule('/settings/keys', view_func=keys, methods=['GET', 'POST'])
account.add_url_rule('/settings/keys/delete/<int:kid>', view_func=delete_key, methods=['POST'])
account.add_url_rule('/settings/alias', view_func=alias, methods=['GET', 'POST'])
account.add_url_rule('/settings/alias/verify/<stub>', view_func=verify_alias, methods=['GET'])
account.add_url_rule('/settings/alias/delete/<int:aid>', view_func=delete_alias, methods=['POST'])

