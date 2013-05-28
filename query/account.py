#!/usr/local/bin/python2.7
#coding:utf-8

from flask import g
from models.account import User, Forget
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

@cache('account:{stub}', 300)
def get_forget_by_stub(stub):
    return Forget.query.filter_by(stub=stub).first()

def get_user_by(**kw):
    return User.query.filter_by(**kw)

def get_current_user():
    if not g.session or not g.session.get('user_id') or not g.session.get('user_token'):
        return None
    user = get_user(g.session['user_id'])
    if g.session['user_token'] != user.token:
        return None
    return user

def clear_user_cache(user):
    keys = ['account:%s' % key for key in [str(user.id), user.domain, user.email]]
    backend.delete_many(*keys)

create_forget = Forget.create
create_user = User.create
