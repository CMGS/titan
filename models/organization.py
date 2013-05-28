#!/usr/local/bin/python2.7
#coding:utf-8

from datetime import datetime
from utils.token import create_token
from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()
def init_organization_db(app):
    db.init_app(app)
    db.app = app
    db.create_all()

class Organization(db.Model):
    __tablename__ = 'organization'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.CHAR(30), nullable=False)
    repos = db.Column(db.Integer, nullable=False, default=0)
    location = db.Column(db.String(200))
    plan = db.Column(db.Integer, default=0, nullable=False)
    balance = db.Column(db.Float, default=0.0, nullable=False)
    token = db.Column(db.CHAR(8), unique=True, nullable=False)
    create = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, name):
        self.name = name
        self.token = create_token(8)

    @staticmethod
    def create(name):
        organization = Organization(name)
        db.session.add(organization)
        db.session.commit()
        return organization

    def set_args(self, key, value):
        setattr(self, key, value)
        db.session.add(self)
        db.session.commit()

    def add_balance(self, balance):
        self.balance = self.balance + balance
        db.session.add(self)
        db.session.commit()

    def update_repos(self, num):
        self.repos = self.repos + num
        db.session.add(self)
        db.session.commit()

class Team(db.Model):
    __tablename__ = 'team'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.CHAR(30), nullable=False)
    oid = db.Column(db.Integer, index=True, nullable=False)
    pic = db.Column(db.String(255), default='default.png')
    repos = db.Column(db.Integer, default=0)

    def __init__(self, oid, name):
        self.oid = oid
        self.name = name

    @staticmethod
    def create(oid, name):
        team = Team(oid, name)
        db.session.add(team)
        db.session.commit()
        return team

    def set_args(self, key, value):
        setattr(self, key, value)
        db.session.add(self)
        db.session.commit()

    def update_repos(self, num):
        self.repos = self.repos + num
        db.session.add(self)
        db.session.commit()

