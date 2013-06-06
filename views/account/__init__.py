#!/usr/local/bin/python2.7
#coding:utf-8

from flask import Blueprint
from flaskext.csrf import csrf_exempt

from utils.helper import make_view
from views.account.setting import Setting
from views.account.forget import Forget, Reset
from views.account.account import Register, Login, Logout

MODULE_NAME = 'account'

view_func = make_view(MODULE_NAME)
account = Blueprint(MODULE_NAME, __name__)

reset = view_func(Reset)
setting = view_func(Setting)
register = view_func(Register)
login = csrf_exempt(view_func(Login))
forget = csrf_exempt(view_func(Forget))
logout = csrf_exempt(view_func(Logout))

account.add_url_rule('/login', view_func=login, methods=['GET', 'POST'])
account.add_url_rule('/logout', view_func=logout, methods=['GET'])
account.add_url_rule('/forget', view_func=forget, methods=['GET', 'POST'])
account.add_url_rule('/setting', view_func=setting, methods=['GET', 'POST'])
account.add_url_rule('/reset/<stub>', view_func=reset, methods=['GET', 'POST'])
account.add_url_rule('/register/<stub>', view_func=register, methods=['GET', 'POST'])

