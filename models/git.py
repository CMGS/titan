#!/usr/local/bin/python2.7
#coding:utf-8

from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()
def init_git_db(app):
    db.init_app(app)
    db.app = app
    db.create_all()

class Keys(db.Model):
    __tablename__ = 'keys'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    uid = db.Column(db.Integer, index=True, nullable=False)
    usage = db.Column(db.CHAR(30), unique=True, nullable=False)
    key = db.Column(db.Text , nullable=False)

    def __init__(self, uid, name, key):
        self.uid = uid
        self.name = name
        self.key = key

class Alias(db.Model):
    __tablename__ = 'alias'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    uid = db.Column(db.Integer, index=True, nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)

    def __init__(self, uid, email):
        self.uid = uid
        self.email = email

