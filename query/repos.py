#!/usr/local/bin/python2.7
#coding:utf-8

import logging
import sqlalchemy.exc
from utils import code
from sheep.api.cache import cache, backend

from query.organization import clear_organization_cache, clear_team_cache
from models.repos import Repos, db
from models.organization import Organization, Team


logger = logging.getLogger(__name__)

# clear

def clear_repo_cache(organization, team=None):
    clear_organization_cache(organization)
    if team:
        clear_team_cache(organization, team)

# create

def create_repo(name, path, user, organization, team=None, summary='', parent=0):
    try:
        tid = team.id if team else 0
        oid = organization.id
        uid = user.id
        repo = Repos(name, path, oid, uid, tid, summary, parent)
        db.session.add(repo)
        organization.repos = Organization.repos + 1
        db.session.add(organization)
        if team:
            team.repos = Team.repos + 1
            db.session.add(team)
        db.session.commit()
        clear_repo_cache(organization, team)
        return repo, None
    except sqlalchemy.exc.IntegrityError, e:
        db.session.rollback()
        if 'Duplicate entry' in e.message:
            return None, code.REPOS_PATH_EXISTS
        logger.exception(e)
        return None, code.UNHANDLE_EXCEPTION

