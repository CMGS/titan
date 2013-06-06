#!/usr/local/bin/python2.7
#coding:utf-8

import config
import logging
import sqlalchemy.exc
from utils import code
from datetime import datetime
from flask import g
from models.account import User, Forget, \
        Keys, Alias, db
from utils.validators import check_domain
from sheep.api.cache import backend, cache

logger = logging.getLogger(__name__)

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

@cache('account:keys:{uid}', 864000)
def get_keys_by_uid(uid):
    return Keys.query.filter_by(uid=uid).all()

@cache('account:keys:{s}', 864000)
def get_keys_by_hex(key_hex):
    return Keys.query.filter_by(key_hex=key_hex).limit(1).first()

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

def clear_forget(forget, delete=True):
    if not forget:
        return
    if delete:
        forget.delete()
    backend.delete('account:forget:%s' % forget.stub)
    backend.delete('account:forget:{uid}'.format(uid=forget.uid))

# Create

def create_key(user, usage, key, key_hex):
    try:
        keys = Keys(user.id, usage, key, key_hex)
        db.session.add(keys)
        db.session.commit(keys)
        return keys, None
    except sqlalchemy.exc.IntegrityError, e:
        db.session.rollback()
        if 'Duplicate entry' in e.message:
            return None, code.ACCOUNT_KEY_EXISTS
        logger.exception(e)
        return None, code.UNHANDLE_EXCEPTION

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
        db.session.rollback()
        if 'Duplicate entry' in e.message:
            return None, code.FORGET_ALREAD_EXISTS
        logger.exception(e)
        return None, code.UNHANDLE_EXCEPTION

# Update

def update_account(user, **kwargs):
    try:
        forget = kwargs.pop('_forget', None)
        for k, v in kwargs.iteritems():
            if k == 'password':
                user.change_password(v)
                continue
            setattr(user, k, v)
        db.session.add(user)
        if forget:
            db.session.delete(forget)
        db.session.commit()
        if forget:
            clear_forget(forget, delete=False)
        clear_user_cache(user)
        return user, None
    except sqlalchemy.exc.IntegrityError, e:
        db.session.rollback()
        if 'Duplicate entry' in e.message:
            return None, code.ACCOUNT_DOMIAN_EXISTS
        logger.exception(e)
        return None, code.UNHANDLE_EXCEPTION

def create_user(username, password, email):
    try:
        user = User(username, password, email)
        db.session.add(user)
        db.session.commit()
        clear_user_cache(user)
        return user, None
    except sqlalchemy.exc.IntegrityError, e:
        db.session.rollback()
        if 'Duplicate entry' in e.message:
            return None, code.ACCOUNT_EMAIL_EXISTS
        logger.exception(e)
        return None, code.UNHANDLE_EXCEPTION


