#!/usr/local/bin/python2.7
#coding:utf-8

import config
import sqlalchemy.exc
from utils import code
from datetime import datetime
from flask import g
from models.account import User, Forget, db
from utils.validators import check_domain
from sheep.api.cache import backend, cache

@cache('account:{uid}', 86400)
def get_user(uid):
    try:
        uid = int(uid)
    except ValueError:
        if check_domain(uid):
            return None
        return get_user_by_domain(domain=uid)
    else:
        return User.query.get(uid)

@cache('account:{domain}', 86400)
def get_user_by_domain(domain):
    return get_user_by(domain=domain).limit(1).first()

@cache('account:{email}', 86400)
def get_user_by_email(email):
    return get_user_by(email=email).limit(1).first()

@cache('account:forget:{stub}', 300)
def get_forget_by_stub(stub):
    forget = Forget.query.filter_by(stub=stub).first()
    if (datetime.now()  - forget.created).total_seconds() > config.FORGET_STUB_EXPIRE:
        clear_forget(forget)
        return None, code.ACCOUNT_FORGET_STUB_EXPIRED
    return forget, None

@cache('account:forget:{uid}', 300)
def get_unique_forget(uid):
    return Forget.query.filter_by(uid=uid).first()

def get_user_by(**kw):
    return User.query.filter_by(**kw)

def get_current_user():
    if not g.session or not g.session.get('user_id') or not g.session.get('user_token'):
        return None
    user = get_user(g.session['user_id'])
    if g.session['user_token'] != user.token:
        return None
    return user

# Clear

def clear_user_cache(user):
    keys = ['account:%s' % key for key in [str(user.id), user.domain, user.email]]
    backend.delete_many(*keys)

def clear_forget(forget):
    if not forget:
        return
    forget.delete()
    backend.delete('account:forget:%s' % forget.stub)
    backend.delete('account:forget:{uid}'.format(uid=forget.uid))

# Create

def create_forget(uid, stub):
    forget = get_unique_forget(uid)
    if forget and (datetime.now()  - forget.created).total_seconds() > config.VERIFY_STUB_EXPIRE:
        clear_forget(forget)
    elif forget:
        return forget, None
    try:
        forget = Forget(uid, stub)
        db.session.add(forget)
        db.session.commit()
        return forget, None
    except sqlalchemy.exc.IntegrityError, e:
        if 'Duplicate entry' in e.message:
            return None, code.FORGET_ALREAD_EXISTS

# Update

create_user = User.create
