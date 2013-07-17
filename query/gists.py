#!/usr/local/bin/python2.7
#coding:utf-8

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

@cache('gists:user:{oid}:{uid}', 8640000)
def get_user_gist(oid, uid):
    return UserGists.query.filter_by(oid=oid, uid=uid).first()

# clear

def clear_gist_cache(gist, organization=None, need=True):
    keys = [
        'gists:{gid}'.format(gid=gist.id), \
    ]
    if organization and need:
        clear_organization_cache(organization)
    backend.delete_many(*keys)

def clear_watcher_cache(user, gist, organization):
    pass

def clear_user_gist_cache(user, organization):
    keys = [
        'gists:user:{oid}:{uid}'.format(oid=organization.id, uid=user.id), \
    ]
    backend.delete_many(*keys)

# create
def create_gist(data, organization, user, summary, parent=0, private=None):
    try:
        gist = Gists(summary, organization.id, user.id, parent=0, private=private)
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

# update
def update_gist(user, gist, data, summary):
    try:
        if summary != gist.summary:
            gist.summary = summary
            db.session.add(gist)
            db.commit()
            clear_gist_cache(gist)
        if data:
            jagare = get_jagare(gist.id, gist.parent)
            error, ret = jagare.update_file(gist.get_real_path(), data, user)
            if error:
                db.session.rollback()
                return None, error
            logger.info(ret)
        return gist, None
    except Exception, e:
        db.session.rollback()
        logger.exception(e)
        return None, code.UNHANDLE_EXCEPTION

