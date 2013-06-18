#!/usr/bin/python
# encoding: UTF-8

from views.repos import repos
from views.account import account
from views.organization import organization

def init_views(app):
    app.register_blueprint(repos)
    app.register_blueprint(account)
    app.register_blueprint(organization)

