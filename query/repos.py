#!/usr/local/bin/python2.7
#coding:utf-8

import logging
import sqlalchemy.exc
from sheep.api.cache import cache, backend

from models import db
from models.repos import Repos, Commiters
from models.organization import Organization, Team

from utils import code
from utils.jagare import get_jagare
from utils.validators import check_repos_limit
from query.organization import clear_organization_cache, clear_team_cache

logger = logging.getLogger(__name__)

@cache('repos:explore:{oid}', 8640000)
def get_organization_repos(oid):
    return Repos.query.filter_by(oid=oid).all()

@cache('repos:explore:team:{oid}:{tid}', 8640000)
def get_team_repos(oid, tid):
    return Repos.query.filter_by(oid=oid, tid=tid).all()

@cache('repos:{oid}:{path}', 864000)
def get_repo_by_path(oid, path):
    return Repos.query.filter_by(path=path, oid=oid).limit(1).first()

@cache('repos:commiter:{uid}:{rid}', 864000)
def get_repo_commiter(uid, rid):
    return Commiters.query.filter_by(uid=uid, rid=rid).limit(1).first()

@cache('repos:commiters:{rid}', 8640000)
def get_repo_commiters(rid):
    return Commiters.query.filter_by(rid=rid).all()

# clear

def clear_commiter_cache(user, repo):
    keys = [
        'repos:commiters:{rid}'.format(rid=repo.id), \
        'repos:commiter:{uid}:{rid}'.format(uid=user.id, rid=repo.id)
    ]
    backend.delete_many(*keys)

def clear_repo_cache(repo, organization, team=None, old_path=None):
    keys = [
        'repos:{oid}:{path}'.format(oid=organization.id, path=old_path or repo.path),
    ]
    clear_organization_cache(organization)
    if team:
        clear_team_cache(organization, team)
    backend.delete_many(*keys)

def clear_explore_cache(organization, team=None):
    keys = [
        'repos:explore:{oid}'.format(oid=organization.id),
    ]
    if team:
        keys.append('repos:explore:team:{oid}:{tid}'.format(oid=organization.id, tid=team.id))
    backend.delete_many(*keys)

# create

def create_repo(name, path, user, organization, team=None, summary='', parent=0):
    try:
        tid = team.id if team else 0
        oid = organization.id
        uid = user.id
        repo = Repos(name, path, oid, uid, tid, summary, parent, commiters=1)
        db.session.add(repo)
        organization.repos = Organization.repos + 1
        db.session.add(organization)
        if team:
            team.repos = Team.repos + 1
            db.session.add(team)
        db.session.flush()
        if not check_repos_limit(organization):
            db.session.rollback()
            return None, code.ORGANIZATION_REPOS_LIMIT
        commiter = Commiters(user.id, repo.id)
        db.session.add(commiter)
        jagare = get_jagare(repo.id, parent)
        ret, error = jagare.init(repo.get_real_path())
        if not ret:
            db.session.rollback()
            return None, error
        db.session.commit()
        clear_repo_cache(repo, organization, team)
        clear_explore_cache(organization, team)
        clear_commiter_cache(user, repo)
        return repo, None
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

def create_commiter(user, repo):
    try:
        commiter = Commiters(user.id, repo.id)
        repo.commiters = Repos.commiters + 1
        db.session.add(commiter)
        db.session.add(repo)
        db.session.commit()
        clear_commiter_cache(user, repo)
        return commiter, None
    except sqlalchemy.exc.IntegrityError, e:
        db.session.rollback()
        if 'Duplicate entry' in e.message:
            return None, code.REPOS_COMMITER_EXISTS
        logger.exception(e)
        return None, code.UNHANDLE_EXCEPTION
    except Exception, e:
        db.session.rollback()
        logger.exception(e)
        return None, code.UNHANDLE_EXCEPTION

# update

def update_repo(organization, repo, name, team=None):
    try:
        old_path = repo.path
        repo.name = name
        repo.path = '%s.git' % name if not team else '%s/%s.git' % (team.name, name)
        db.session.add(repo)
        db.session.commit()
        clear_repo_cache(repo, organization, old_path=old_path)
        return None
    except sqlalchemy.exc.IntegrityError, e:
        db.session.rollback()
        if 'Duplicate entry' in e.message:
            return code.REPOS_PATH_EXISTS
        logger.exception(e)
        return code.UNHANDLE_EXCEPTION
    except Exception, e:
        db.session.rollback()
        logger.exception(e)
        return code.UNHANDLE_EXCEPTION

def transport_repo(organization, user, repo, team=None):
    try:
        repo.uid = user.id
        db.session.add(repo)
        is_commiter = get_repo_commiter(user.id, repo.id)
        if not is_commiter:
            _, error = create_commiter(user, repo)
            if error:
                raise Exception(error)
        db.session.commit()
        clear_repo_cache(repo, organization, team)
        return None
    except Exception, e:
        db.session.rollback()
        logger.exception(e)
        return code.UNHANDLE_EXCEPTION

# delete

def delete_commiter(user, commiter, repo):
    try:
        db.session.delete(commiter)
        repo.commiters = Repos.commiters - 1
        db.session.add(repo)
        db.session.commit()
        clear_commiter_cache(user, repo)
        return None
    except Exception, e:
        db.session.rollback()
        logger.exception(e)
        return code.UNHANDLE_EXCEPTION

def delete_repo(organization, repo, team=None):
    try:
        keys = []
        db.session.delete(repo)
        organization.repos = Organization.repos - 1
        db.session.add(organization)
        if team:
            team.repos = Team.repos - 1
            db.session.add(team)
        commiters = get_repo_commiters(repo.id)
        for commiter in commiters:
            db.session.delete(commiter)
            keys.append('repos:commiters:{rid}'.format(rid=repo.id))
            keys.append('repos:commiter:{uid}:{rid}'.format(uid=commiter.uid, rid=repo.id))
        db.session.commit()
        clear_repo_cache(repo, organization, team)
        clear_explore_cache(organization, team)
        backend.delete_many(*keys)
        return None
    except Exception, e:
        db.session.rollback()
        logger.exception(e)
        return code.UNHANDLE_EXCEPTION

