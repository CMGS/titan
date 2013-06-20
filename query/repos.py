#!/usr/local/bin/python2.7
#coding:utf-8

import os
import logging
import sqlalchemy.exc
from utils import code
from utils.repos import get_jagare
from sheep.api.cache import cache, backend

from models import db
from models.repos import Repos
from models.organization import Organization, Team

from utils.validators import check_repos_limit
from query.organization import clear_organization_cache, clear_team_cache

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
        db.session.flush()
        if not check_repos_limit(organization):
            db.session.rollback()
            return None, code.ORGANIZATION_REPOS_LIMIT
        jagare = get_jagare(repo.id, parent)
        ret, error = jagare.init(os.path.join(str(organization.id), repo.path))
        if not ret:
            db.session.rollback()
            return None, error
        db.session.commit()
        clear_repo_cache(organization, team)
        return repo, None
    except sqlalchemy.exc.IntegrityError, e:
        db.session.rollback()
        if 'Duplicate entry' in e.message:
            return None, code.REPOS_PATH_EXISTS
        logger.exception(e)
        return None, code.UNHANDLE_EXCEPTION

