#!/usr/local/bin/python2.7
#coding:utf-8

import os
import logging
import sqlalchemy.exc
from sheep.api.cache import cache, backend

from models import db
from models.organization import Organization
from models.gists import Gists, GistWatchers, UserGists

from utils import code
from utils.jagare import get_jagare

from query.organization import clear_organization_cache

logger = logging.getLogger(__name__)

@cache('gists:{gid}', 8640000)
def get_gist(gid):
    return Gists.query.get(gid)

@cache('gists:hidden:{private}', 8640000)
def get_gist_by_private(private):
    return Gists.query.filter_by(private=private).first()

@cache('gists:path:{path}', 8640000)
def get_gist_by_path(path):
    return Gists.query.filter_by(path=path).first()

@cache('gists:user:{oid}:{uid}', 8640000)
def get_user_gist(oid, uid):
    return UserGists.query.filter_by(oid=oid, uid=uid).first()

@cache('gists:watchers:{gid}', 8640000)
def get_gist_watchers(gid):
    return GistWatchers.query.filter_by(gid=gid).all()

@cache('gists:watcher:{uid}:{gid}', 864000)
def get_gist_watcher(uid, gid):
    return GistWatchers.query.filter_by(uid=uid, gid=gid).limit(1).first()

@cache('gists:explore:{oid}', 8640000)
def get_organization_gists(oid):
    return Gists.query.filter(Gists.oid==oid).filter(Gists.private==None).all()

@cache('gists:explore:user:{oid}:{uid}', 8640000)
def get_user_organization_gists(oid, uid):
    return Gists.query.filter((Gists.oid==oid) & (Gists.uid==uid)).all()

@cache('user:watch:gists:{uid}:{oid}', 8640000)
def get_user_watch_gists(uid, oid):
    watches = GistWatchers.query.filter_by(uid=uid, oid=oid).all()
    query = Gists.query.filter(Gists.oid==oid)
    s = None
    for w in watches:
        if s is None:
            s = (Gists.id == w.gid)
        else:
            s = s | (Gists.id == w.gid)
    return query.filter(s).all()

# clear

def clear_explore_cache(gist, user, organization):
    keys = [
        'gists:explore:user:{oid}:{uid}'.format(uid=user.id, oid=organization.id), \
    ]
    if not gist.private:
        keys.append('gists:explore:{oid}'.format(oid=organization.id))
    backend.delete_many(*keys)

def clear_gist_cache(gist, organization=None, need=True):
    keys = [
        'gists:{gid}'.format(gid=gist.id), \
        'gists:path:{path}'.format(path=gist.path), \
    ]
    if gist.private:
        keys.append('gists:hidden:{private}'.format(private=gist.private))
    if organization and need:
        clear_organization_cache(organization)
    backend.delete_many(*keys)

def clear_watcher_cache(user, gist, organization):
    keys = [
        'gists:watchers:{gid}'.format(gid=gist.id), \
        'gists:watcher:{uid}:{gid}'.format(uid=user.id, gid=gist.id), \
        'user:watch:gists:{uid}:{oid}'.format(uid=user.id, oid=organization.id), \
    ]
    backend.delete_many(*keys)

def clear_user_gist_cache(user, organization):
    keys = [
        'gists:user:{oid}:{uid}'.format(oid=organization.id, uid=user.id), \
    ]
    backend.delete_many(*keys)

# create

def create_gist(data, organization, user, summary, parent=0, private=None, watchers=0):
    try:
        gist = Gists(summary, organization.id, user.id, parent=0, private=private, watchers=watchers)
        db.session.add(gist)
        organization.gists = Organization.gists + 1
        db.session.add(organization)
        user_gist = get_user_gist(organization.id, user.id)
        if not user_gist:
            user_gist = UserGists(organization.id, user.id, 1)
        else:
            user_gist.count = UserGists.count + 1
        db.session.add(user_gist)
        db.session.flush()
        gist.path = os.path.join('gist', '%s.git' % (private or gist.id))
        watcher = GistWatchers(user.id, gist.id, organization.id)
        db.session.add(watcher)
        jagare = get_jagare(gist.id, parent)
        ret, error = jagare.init(gist.get_real_path())
        if not ret:
            db.session.rollback()
            return None, error
        error, ret = jagare.update_file(gist.get_real_path(), data, user)
        if error:
            db.session.rollback()
            return None, error
        db.session.commit()
        clear_gist_cache(gist, organization)
        clear_user_gist_cache(user, organization)
        clear_explore_cache(gist, user, organization)
        clear_watcher_cache(user, gist, organization)
        return gist, None
    except sqlalchemy.exc.IntegrityError, e:
        db.session.rollback()
        if 'Duplicate entry' in e.message:
            return None, code.REPOS_PATH_EXISTS
        logger.exception(e)
        return None, code.UNHANDLE_EXCEPTION
    except Exception, e:
        db.session.rollback()
        logger.exception(e)
        return None, code.UNHANDLE_EXCEPTION

def create_watcher(user, gist, organization):
    try:
        watcher = GistWatchers(user.id, gist.id, organization.id)
        gist.watchers = Gists.watchers + 1
        db.session.add(watcher)
        db.session.add(gist)
        db.session.commit()
        clear_watcher_cache(user, gist, organization)
        clear_gist_cache(gist)
        if user.id != gist.uid:
            from actions.gists import after_add_watcher
            after_add_watcher(user, organization, gist)
        return watcher, None
    except sqlalchemy.exc.IntegrityError, e:
        db.session.rollback()
        if 'Duplicate entry' in e.message:
            return None, code.REPOS_WATCHER_EXISTS
        logger.exception(e)
        return None, code.UNHANDLE_EXCEPTION
    except Exception, e:
        db.session.rollback()
        logger.exception(e)
        return None, code.UNHANDLE_EXCEPTION

# update

def update_gist(user, gist, data, summary):
    try:
        if summary != gist.summary:
            gist.summary = summary
            db.session.add(gist)
            db.session.commit()
            clear_gist_cache(gist)
        if data:
            jagare = get_jagare(gist.id, gist.parent)
            error, ret = jagare.update_file(gist.get_real_path(), data, user)
            if error:
                db.session.rollback()
                return None, error
            logger.info(ret)
            from actions.gists import after_update_gist
            after_update_gist(user, gist, asynchronous=True)
        return gist, None
    except Exception, e:
        db.session.rollback()
        logger.exception(e)
        return None, code.UNHANDLE_EXCEPTION

# delete

def delete_watcher(user, watcher, gist, organization):
    try:
        db.session.delete(watcher)
        gist.watchers = gist.watchers - 1
        db.session.add(gist)
        db.session.commit()
        clear_watcher_cache(user, gist, organization)
        clear_gist_cache(gist)
        if user.id != gist.uid:
            from actions.gists import after_delete_watcher
            after_delete_watcher(user, organization, gist)
        return None
    except Exception, e:
        db.session.rollback()
        logger.exception(e)
        return code.UNHANDLE_EXCEPTION

def delete_gist(user, gist, organization):
    try:
        keys = []
        db.session.delete(gist)
        organization.gists = Organization.gists - 1
        db.session.add(organization)
        user_gist = get_user_gist(organization.id, user.id)
        user_gist.count = UserGists.count - 1
        db.session.add(user_gist)
        watchers = get_gist_watchers(gist.id)
        keys.append('gists:watchers:{gid}'.format(gid=gist.id))
        for watcher in watchers:
            db.session.delete(watcher)
            keys.append('gists:watcher:{uid}:{gid}'.format(uid=watcher.uid, gid=gist.id))
            keys.append('user:watch:gists:{uid}:{oid}'.format(uid=watcher.uid, oid=organization.id))
        jagare = get_jagare(gist.id, gist.parent)
        ret, error = jagare.delete(gist.get_real_path())
        if not ret:
            db.session.rollback()
            return error
        db.session.commit()
        clear_gist_cache(gist, organization)
        clear_explore_cache(gist, user, organization)
        from actions.gists import after_delete_gist
        after_delete_gist(gist, asynchronous=True)
        backend.delete_many(*keys)
        return None
    except Exception, e:
        db.session.rollback()
        logger.exception(e)
        return code.UNHANDLE_EXCEPTION

