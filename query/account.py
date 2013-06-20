#!/usr/local/bin/python2.7
#coding:utf-8

import config
import logging
import sqlalchemy.exc
from utils import code
from datetime import datetime

from flask import g
from sheep.api.cache import backend, cache
from utils.validators import check_username

from models import db
from models.account import User, Forget, \
        Keys, Alias

logger = logging.getLogger(__name__)

@cache('account:{uid}', 86400)
def get_user(uid):
    try:
        uid = int(uid)
    except ValueError:
        if not check_username(uid):
            return None
        return get_user_by_name(name=uid)
    else:
        return User.query.get(uid)

@cache('account:{name}', 86400)
def get_user_by_name(name):
    return get_user_by(name=name).limit(1).first()

@cache('account:{email}', 86400)
def get_user_by_email(email):
    return get_user_by(email=email).limit(1).first()

@cache('account:forget:{stub}', 300)
def get_forget_by_stub(stub):
    forget = Forget.query.filter_by(stub=stub).first()
    if not forget:
        return None, code.ACCOUNT_FORGET_STUB_INVAILD
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

@cache('account:key:{kid}', 864000)
def get_key_by_id(kid):
    return Keys.query.get(kid)

@cache('account:key:{finger}', 864000)
def get_keys_by_finger(finger):
    return Keys.query.filter_by(finger=finger).limit(1).first()

@cache('account:alias:user:{uid}', 864000)
def get_alias_by_uid(uid):
    return Alias.query.filter_by(uid=uid).all()

@cache('account:alias:{aid}', 864000)
def get_alias_by_id(aid):
    return Alias.query.get(aid)

@cache('account:alias:{email}', 864000)
def get_alias_by_email(email):
    return Alias.query.filter_by(email=email).limit(1).first()

def get_user_by(**kw):
    return User.query.filter_by(**kw)

def get_current_user():
    if not g.session or not g.session.get('user_id') or not g.session.get('user_token'):
        return None
    user = get_user(g.session['user_id'])
    if not user:
        return None
    if g.session['user_token'] != user.token:
        return None
    return user

# Clear

def clear_user_cache(user):
    keys = ['account:%s' % key for key in [str(user.id), user.name, user.email]]
    backend.delete_many(*keys)

def clear_forget(forget, delete=True):
    if not forget:
        return
    if delete:
        forget.delete()
    backend.delete('account:forget:%s' % forget.stub)
    backend.delete('account:forget:{uid}'.format(uid=forget.uid))

def clear_alias_cache(user, email, aid=None):
    keys = [
        'account:alias:{email}'.format(email=email),
        'account:alias:user:{uid}'.format(uid=user.id),
    ]
    if aid:
        keys.append('account:alias:{aid}'.format(aid=aid))
    backend.delete_many(*keys)


def clear_key_cache(key, user=None):
    keys = [
        'account.key.{kid}'.format(kid=key.id), \
        'account.key.{finger}'.format(finger=key.finger), \
    ]
    if user:
        keys.append('account:keys:{uid}'.format(uid=user.id))
    backend.delete_many(*keys)

# Create

def create_key(user, usage, key, finger):
    try:
        key = Keys(user.id, usage, key, finger)
        db.session.add(key)
        db.session.commit()
        clear_key_cache(key, user)
        return key, None
    except sqlalchemy.exc.IntegrityError, e:
        db.session.rollback()
        if 'Duplicate entry' in e.message:
            return None, code.ACCOUNT_KEY_EXISTS
        logger.exception(e)
        return None, code.UNHANDLE_EXCEPTION

def create_forget(uid, stub):
    import pdb
    pdb.set_trace()
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

def create_user(name, password, email):
    try:
        user = User(name, password, email)
        db.session.add(user)
        db.session.flush()
        alias = Alias(user.id, email)
        db.session.add(alias)
        db.session.commit()
        clear_user_cache(user)
        return user, None
    except sqlalchemy.exc.IntegrityError, e:
        db.session.rollback()
        if 'Duplicate entry' in e.message and 'email' in e.message:
            return None, code.ACCOUNT_EMAIL_EXISTS
        if 'Duplicate entry' in e.message and 'name' in e.message:
            return None, code.ACCOUNT_USERNAME_EXISTS
        logger.exception(e)
        return None, code.UNHANDLE_EXCEPTION

def create_alias(user, email):
    try:
        alias = Alias(user.id, email)
        db.session.add(alias)
        db.session.commit()
        clear_alias_cache(user, email)
        return alias, None
    except sqlalchemy.exc.IntegrityError, e:
        db.session.rollback()
        if 'Duplicate entry' in e.message:
            return None, code.ACCOUNT_EMAIL_EXISTS
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
    except Exception, e:
        db.session.rollback()
        logger.exception(e)
        return None, code.UNHANDLE_EXCEPTION

