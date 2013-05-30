#!/usr/local/bin/python2.7
#coding:utf-8

from datetime import datetime
from sqlalchemy.dialects.mysql import BIT
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
    git = db.Column(db.CHAR(10), unique=True, nullable=False)
    repos = db.Column(db.Integer, nullable=False, default=0)
    teams = db.Column(db.Integer, nullable=False, default=0)
    members = db.Column(db.Integer, nullable=False, default=0)
    plan = db.Column(db.Integer, default=1, nullable=False)
    balance = db.Column(db.Float, default=0.0, nullable=False)
    location = db.Column(db.String(200))
    create = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, name, git, members=0):
        self.name = name
        self.git = git
        self.members = members

    @staticmethod
    def create(name, git, members=0):
        organization = Organization(name, git, members)
        db.session.add(organization)
        db.session.commit()
        return organization

    def set_args(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)
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

    def update_members(self, num):
        self.members = self.members + num
        db.session.add(self)
        db.session.commit()

    def update_teams(self, num):
        self.teams = self.teams + num
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

class Members(db.Model):
    __tablename__ = 'members'
    __table_args__ = (db.UniqueConstraint('oid', 'uid', name='uix_oid_uid'), )
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    oid = db.Column(db.Integer, index=True, nullable=False)
    uid = db.Column(db.Integer, index=True, nullable=False)
    admin = db.Column(BIT(1), nullable=False, default=0)
    join = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, oid, uid, admin=0):
        self.oid = oid
        self.uid = uid
        self.admin = admin

    @staticmethod
    def create(oid, uid, admin=0):
        members = Members(oid, uid, admin)
        db.session.add(members)
        db.session.commit()
        return members

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def set_as_admin(self):
        self.admin = 1
        db.session.delete(self)
        db.session.commit()

class TeamMembers(db.Model):
    __tablename__ = 'team_members'
    __table_args__ = (db.UniqueConstraint('tid', 'uid', name='uix_tid_uid'), )
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    tid = db.Column(db.Integer, index=True, nullable=False)
    uid = db.Column(db.Integer, index=True, nullable=False)
    join = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, tid, uid):
        self.tid = tid
        self.uid = uid

    @staticmethod
    def create(tid, uid):
        team_members = TeamMembers(tid, uid)
        db.session.add(team_members)
        db.session.commit()
        return team_members

    def delete(self):
        db.session.delete(self)
        db.session.commit()

class Verify(db.Model):
    __tablename__ = 'verify'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    stub = db.Column('stub', db.CHAR(20), nullable=False, unique=True)
    email = db.Column(db.String(200), nullable=False)
    name = db.Column(db.CHAR(30), nullable=False)
    git = db.Column(db.CHAR(10), unique=True, nullable=False)
    admin = db.Column(BIT(1), nullable=False, default=0)
    created = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, stub, email, name, git, admin=0):
        self.stub = stub
        self.email = email
        self.name = name
        self.git = git
        self.admin = admin

    @staticmethod
    def create(stub, email, name, git, admin=0):
        verify = Verify(stub, email, name, git, admin)
        db.session.add(verify)
        db.session.commit()
        return verify

    def delete(self):
        db.session.delete(self)
        db.session.commit()

