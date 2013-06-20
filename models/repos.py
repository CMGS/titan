#!/usr/local/bin/python2.7
#coding:utf-8

from datetime import datetime
from models import db

class Repos(db.Model):
    __tablename__ = 'repos'
    __table_args__ = (db.UniqueConstraint('oid', 'path', name='uix_oid_path'), )
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.CHAR(30), nullable=False)
    oid = db.Column(db.Integer, nullable=False, index=True)
    tid = db.Column(db.Integer, nullable=False, index=True, default=0)
    uid = db.Column(db.Integer, nullable=False, index=True)
    summary = db.Column(db.String(200))
    path = db.Column(db.String(150), index=True, nullable=False)
    parent = db.Column(db.Integer, nullable=False, default=0)
    forks = db.Column(db.Integer, nullable=False, default=0)
    create = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, name, path, oid, uid, tid=0, summary='', parent=0):
        self.name = name
        self.path = path
        self.oid = oid
        self.uid = uid
        self.tid = tid
        self.summary = summary
        self.parent = parent

    def set_args(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)
        db.session.add(self)
        db.session.commit()

