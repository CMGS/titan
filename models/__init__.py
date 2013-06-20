#!/usr/bin/python
# encoding: UTF-8

from flask.ext.sqlalchemy import SQLAlchemy
db = SQLAlchemy()

def init_db(app):
    db.init_app(app)
    db.app = app
    db.create_all()

