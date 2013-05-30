#!/usr/local/bin/python2.7
#coding:utf-8

from flask import Blueprint
from flaskext.csrf import csrf_exempt

from views.account.setting import Setting
from views.account.forget import Forget, Reset
from views.account.account import Register, Login, Logout

account = Blueprint('account', __name__)

reset = Reset.as_view('reset')
setting = Setting.as_view('setting')
forget = csrf_exempt(Forget.as_view('forget'))
login = csrf_exempt(Login.as_view('login'))
logout = csrf_exempt(Logout.as_view('logout'))
register = Register.as_view('register')

account.add_url_rule('/login/', view_func=login, methods=['GET', 'POST'])
account.add_url_rule('/register/<stub>/', view_func=register, methods=['GET', 'POST'])
account.add_url_rule('/logout/', view_func=logout, methods=['GET'])
account.add_url_rule('/forget/', view_func=forget, methods=['GET', 'POST'])
account.add_url_rule('/reset/<stub>/', view_func=reset, methods=['GET', 'POST'])
account.add_url_rule('/setting/', view_func=setting, methods=['GET', 'POST'])

