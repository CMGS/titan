#!/usr/bin/python
# encoding: UTF-8

from views.account import account

def init_views(app):
    app.register_blueprint(account, url_prefix='/account')

