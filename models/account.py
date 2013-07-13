#!/usr/bin/python
# encoding: UTF-8

__all__ = ['User', 'Forget']

import hashlib
from models import db
from datetime import datetime
from utils.helper import get_avatar
from utils.token import create_token

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.CHAR(25), nullable=False, unique=True)
    passwd = db.Column(db.CHAR(50), nullable=False)
    display = db.Column(db.String(16), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)
    token = db.Column(db.CHAR(16))
    city = db.Column(db.String(150))
    title = db.Column(db.String(150))
    join = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, name, password, email):
        self.name = name
        self.passwd = User.create_password(password)
        self.email = email.lower()
        self.display = name
        self.token = create_token(16)

    @staticmethod
    def create_password(raw):
        salt = create_token(8)
        hsh = hashlib.sha1(salt + raw).hexdigest()
        return "%s$%s" % (salt, hsh)

    def check_password(self, raw):
        if '$' not in self.passwd:
            return False
        salt, hsh = self.passwd.split('$')
        verify = hashlib.sha1(salt + raw).hexdigest()
        return verify == hsh

    def change_password(self, password):
        self.token = create_token(16)
        self.passwd = User.create_password(password)

    def set_args(self, key, value):
        setattr(self, key, value)
        db.session.add(self)
        db.session.commit()

    def avatar(self, size=48):
        return get_avatar(self.email, size)

class Forget(db.Model):
    __tablename__ = 'forget'
    uid = db.Column('uid', db.Integer, primary_key=True)
    stub = db.Column('stub', db.CHAR(20), primary_key=True)
    created = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, uid, stub):
        self.uid = uid
        self.stub = stub

    def delete(self):
        db.session.delete(self)
        db.session.commit()

class Keys(db.Model):
    __tablename__ = 'keys'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    uid = db.Column(db.Integer, index=True, nullable=False)
    key = db.Column(db.Text, nullable=False)
    finger = db.Column(db.CHAR(32), unique=True, nullable=False)
    usage = db.Column(db.CHAR(30), nullable=False)

    def __init__(self, uid, usage, key, finger):
        self.uid = uid
        self.usage = usage
        self.key = key
        self.finger = finger

    def delete(self):
        db.session.delete(self)
        db.session.commit()

class Alias(db.Model):
    __tablename__ = 'alias'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    uid = db.Column(db.Integer, index=True, nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)

    def __init__(self, uid, email):
        self.uid = uid
        self.email = email

    def delete(self):
        db.session.delete(self)
        db.session.commit()

