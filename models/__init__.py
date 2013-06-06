#!/usr/bin/python
# encoding: UTF-8

from .git import init_git_db
from .account import init_account_db
from .organization import init_organization_db

def init_db(app):
    init_git_db(app)
    init_account_db(app)
    init_organization_db(app)

