#!/usr/local/bin/python2.7
#coding:utf-8

import os
from datetime import datetime
from models import db

class Gists(db.Model):
    __tablename__ = 'gists'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    summary = db.Column(db.String(200))
    oid = db.Column(db.Integer, nullable=False, index=True)
    uid = db.Column(db.Integer, nullable=False, index=True)
    watchers = db.Column(db.Integer, nullable=False, default=0)
    parent = db.Column(db.Integer, nullable=False, default=0)
    forks = db.Column(db.Integer, nullable=False, default=0)
    private = db.Column(db.String(20), nullable=True)
    create = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, summary, oid, uid, parent=0, watchers=0, private=''):
        self.oid = oid
        self.uid = uid
        self.watchers = watchers
        self.summary = summary
        self.parent = parent
        self.private = private

    def get_real_path(self):
        if not getattr(self, '_real_path', None):
            real_path = os.path.join(
                            str(self.oid), \
                            'gist', \
                            '%d.git' % self.id,
                        )
            setattr(self, '_real_path', real_path)
        return getattr(self, '_real_path')

    def set_args(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)
        db.session.add(self)
        db.session.commit()

