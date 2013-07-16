#!/usr/local/bin/python2.7
#coding:utf-8

import logging
import sqlalchemy.exc
from sheep.api.cache import cache, backend

from models import db
from models.gists import Gists, GistWatchers
from models.organization import Organization

from utils import code
from utils.jagare import get_jagare

from query.organization import clear_organization_cache

logger = logging.getLogger(__name__)

@cache('gists:{gid}', 8640000)
def get_gist(gid):
    return Gists.query.get(gid)

# clear

def clear_gist_cache(gist, organization, need=True):
    keys = [
        'gists:{gid}'.format(gid=gist.id), \
    ]
    if need:
        clear_organization_cache(organization)
    backend.delete_many(*keys)

def clear_watcher_cache(user, gist, organization):
    pass

# create
def create_gist(data, organization, user, summary, parent=0, private=None):
    try:
        gist = Gists(summary, organization.id, user.id, parent=0, private=private)
        db.session.add(gist)
        organization.gists = Organization.gists + 1
        db.session.add(organization)
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

