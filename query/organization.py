#!/usr/local/bin/python2.7
#coding:utf-8

import config
import logging
import sqlalchemy.exc
from utils import code
from datetime import datetime
from sheep.api.cache import cache, backend
from utils.validators import check_members_limit

from models import db
from models.organization import Organization, Team, Verify, \
        Members, TeamMembers

logger = logging.getLogger(__name__)

@cache('organization:{oid}', 86400)
def get_organization(oid):
    return Organization.query.get(oid)

@cache('organization:member:{oid}:{uid}', 86400)
def get_organization_member(oid, uid):
    return Members.query.filter_by(uid=uid, oid=oid).limit(1).first()

@cache('organization:member:{uid}', 86400)
def get_organizations_by_uid(uid):
    return Members.query.filter_by(uid=uid).all()

@cache('organization:git:{git}', 86400)
def get_organization_by_git(git):
    return get_organization_by(git=git).limit(1).first()

@cache('organization:team:team:{tid}', 864000)
def get_team(tid):
    return Team.query.get(tid)

@cache('organization:team:{oid}', 86400)
def get_teams_by_ogranization(oid):
    return Team.query.filter_by(oid=oid).all()

@cache('organization:team:{oid}:{name}', 86400)
def get_team_by_name(oid, name):
    return Team.query.filter_by(oid=oid, name=name).limit(1).first()

@cache('organization:team:member:{tid}:{uid}', 86400)
def get_team_member(tid, uid):
    return TeamMembers.query.filter_by(tid=tid, uid=uid).limit(1).first()

@cache('organization:team:members:{tid}', 86400)
def get_team_members(tid):
    return TeamMembers.query.filter_by(tid=tid).all()

@cache('organization:verify:{stub}', 300)
def get_verify_by_stub(stub):
    verify = Verify.query.filter_by(stub=stub).limit(1).first()
    if not verify:
        return None, code.ORGANIZATION_VERIFY_STUB_EXPIRED
    if verify and (datetime.now()  - verify.created).total_seconds() > config.VERIFY_STUB_EXPIRE:
        clear_verify(verify)
        return None, code.ORGANIZATION_VERIFY_STUB_EXPIRED
    return verify, None

@cache('Organization:verify:{git}:{email}', 300)
def get_unique_verify(git, email):
    return Verify.query.filter_by(git=git, email=email).limit(1).first()

def get_organization_by(**kw):
    return Organization.query.filter_by(**kw)

# Clear

def clear_organization_cache(organization, user=None, old_git=''):
    keys = [
        'organization:{oid}'.format(oid=organization.id),
        'organization:git:{git}'.format(git=old_git or organization.git),
    ]
    if user:
        keys.append('organization:member:{oid}:{uid}'.format(oid=organization.id, uid=user.id))
        keys.append('organization:member:{uid}'.format(uid=user.id))
    backend.delete_many(*keys)

def clear_team_cache(organization, team, user=None):
    keys = [
        'organization:team:team:{tid}'.format(tid=team.id), \
        'organization:team:members:{tid}'.format(tid=team.id), \
        'organization:team:{oid}'.format(oid=organization.id), \
        'organization:team:{oid}:{name}'.format(oid=organization.id, name=team.name),
    ]

    if user:
        keys.append('organization:team:member:{tid}:{uid}'.format(tid=team.id, uid=user.id))
    backend.delete_many(*keys)

def clear_verify(verify, delete=True):
    if not verify:
        return
    if delete:
        verify.delete()
    backend.delete('organization:verify:%s' % verify.stub)
    backend.delete('organization:verify:%s:%s' % (verify.git, verify.email))

# Create

def create_organization(user, name, git, members=0, admin=0, verify=None):
    try:
        organization = Organization(name, git, members=1)
        db.session.add(organization)
        db.session.flush()
        members = Members(organization.id, user.id, admin=1)
        db.session.add(members)
        if verify:
            db.session.delete(verify)
        db.session.commit()
        clear_organization_cache(organization, user=user)
        return organization, None
    except sqlalchemy.exc.IntegrityError, e:
        db.session.rollback()
        if 'Duplicate entry' in e.message:
            return None, code.ORGANIZATION_GITNAME_EXISTS
        logger.exception(e)
        return None, code.UNHANDLE_EXCEPTION

def create_members(organization, user, verify):
    try:
        member = Members(organization.id, user.id, verify.admin)
        organization.members = Organization.members + 1
        db.session.add(member)
        db.session.add(organization)
        db.session.delete(verify)
        db.session.flush()
        if not check_members_limit(organization):
            db.session.rollback()
            return None, code.ORGANIZATION_MEMBERS_LIMIT
        db.session.commit()
        clear_verify(verify, delete=False)
        clear_organization_cache(organization, user=user)
        return member, None
    except sqlalchemy.exc.IntegrityError, e:
        db.session.rollback()
        if 'Duplicate entry' in e.message:
            return None, code.ORGANIZATION_MEMBER_EXISTS
        logger.exception(e)
        return None, code.UNHANDLE_EXCEPTION

def create_team(name, display, user, organization, private=0, members=0):
    try:
        team = Team(organization.id, name, display, private, members)
        db.session.add(team)
        db.session.flush()
        team_member = TeamMembers(team.id, user.id, admin=1)
        organization.teams = Organization.teams + 1
        db.session.add(team_member)
        db.session.add(organization)
        db.session.commit()
        clear_organization_cache(organization)
        clear_team_cache(organization, team, user)
        return team, None
    except sqlalchemy.exc.IntegrityError, e:
        db.session.rollback()
        if 'Duplicate entry' in e.message:
            return None, code.ORGANIZATION_TEAM_EXISTS
        logger.exception(e)
        return None, code.UNHANDLE_EXCEPTION

def create_team_members(organization, team, user, admin=0):
    try:
        team_member = TeamMembers(team.id, user.id, admin=admin)
        team.members = Team.members + 1
        db.session.add(team_member)
        db.session.add(team)
        db.session.commit()
        clear_team_cache(organization, team, user)
        return team_member, None
    except sqlalchemy.exc.IntegrityError, e:
        db.session.rollback()
        if 'Duplicate entry' in e.message:
            return None, code.ORGANIZATION_TEAM_MEMBER_EXISTS
        logger.exception(e)
        return None, code.UNHANDLE_EXCEPTION

def create_verify(stub, email, name, git, admin=0):
    verify = get_unique_verify(git, email)
    if verify and (datetime.now()  - verify.created).total_seconds() > config.VERIFY_STUB_EXPIRE:
        clear_verify(verify)
    elif verify:
        return verify, None
    try:
        verify = Verify(stub, email, name, git, admin)
        db.session.add(verify)
        db.session.commit()
        return verify, None
    except sqlalchemy.exc.IntegrityError, e:
        db.session.rollback()
        if 'Duplicate entry' in e.message:
            return None, code.VERIFY_ALREAD_EXISTS
        logger.exception(e)
        return None, code.UNHANDLE_EXCEPTION

# Update

def quit_team(organization, team, team_member, user):
    team.members = Team.members - 1
    db.session.delete(team_member)
    db.session.add(team)
    db.session.commit()
    clear_team_cache(organization, team, user)

def update_team(organization, team, **attr):
    try:
        for k, v in attr.iteritems():
            setattr(team, k, v)
        db.session.add(team)
        db.session.commit()
        clear_team_cache(organization, team)
        return team, None
    except sqlalchemy.exc.IntegrityError, e:
        db.session.rollback()
        if 'Duplicate entry' in e.message:
            return None, code.ORGANIZATION_TEAM_EXISTS
        logger.exception(e)
        return None, code.UNHANDLE_EXCEPTION

def update_organization(organization, name, git, location, allow):
    try:
        old_git = ''
        if name:
            organization.name = name
        if git:
            old_git = organization.git
            organization.git = git
        if location:
            organization.location = location
        organization.allow = allow
        db.session.add(organization)
        db.session.commit()
        # Ugly 如果修改了Git，需要清理的是老GitName的数据，而非新的
        clear_organization_cache(organization, old_git=old_git)
        return organization, None
    except sqlalchemy.exc.IntegrityError, e:
        db.session.rollback()
        if 'Duplicate entry' in e.message:
            return None, code.ORGANIZATION_GITNAME_EXISTS
        logger.exception(e)
        return None, code.UNHANDLE_EXCEPTION

