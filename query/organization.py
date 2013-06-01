#!/usr/local/bin/python2.7
#coding:utf-8

import config
import sqlalchemy.exc
from utils import code
from datetime import datetime
from sheep.api.cache import cache, backend
from models.organization import Organization, Team, Verify, \
        Members, TeamMembers, db

@cache('organization:{oid}', 86400)
def get_organization(oid):
    return Organization.query.get(oid)

@cache('organization:member:{oid}:{uid}', 86400)
def get_member(oid, uid):
    return Members.query.filter_by(oid=oid, uid=uid).limit(1).first()

@cache('organization:{git}', 86400)
def get_organization_by_git(git):
    return get_organization_by(git=git).limit(1).first()

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
    return Verify.query.filter_by(stub=stub).limit(1).first()

@cache('Organization:verify:{git}:{email}', 300)
def get_unique_verify(git, email):
    return Verify.query.filter_by(git=git, email=email).limit(1).first()

def get_organization_by(**kw):
    return Organization.query.filter_by(**kw)

# Clear

def clear_organization_cache(organization, user=None):
    keys = ['organization:%s' % key for key in [str(organization.id), organization.git]]
    if user:
        keys.append('organization:member:{oid}:{uid}'.format(oid=organization.id, uid=user.id))
    backend.delete_many(*keys)

def clear_team_cache(organization, team, user=None):
    keys = ['organization:team:members:{tid}'.format(tid=team.id), \
            'organization:team:{oid}:{name}'.format(oid=organization.id, name=team.name),]
    if user:
        keys.append('organization:team:member:{tid}:{uid}'.format(tid=team.id, uid=user.id))
    backend.delete_many(*keys)

def clear_verify(verify):
    if not verify:
        return
    verify.delete()
    backend.delete('organization:verify:%s' % verify.stub)
    backend.delete('organization:verify:%s:%s' % (verify.git, verify.email))

# Create

def create_organization(user, name, git, members=0, admin=0):
    try:
        organization = Organization(name, git, members=1)
        db.session.add(organization)
        db.session.flush()
        members = Members(organization.id, user.id, admin=1)
        db.session.add(members)
        db.session.commit()
        clear_organization_cache(organization, user)
        return organization, None
    except sqlalchemy.exc.IntegrityError, e:
        if 'Duplicate entry' in e.message:
            return None, code.ORGANIZATION_EXISTS

def create_members(organization, user, verify):
    try:
        member = Members(organization.id, user.id, verify.admin)
        organization.members = Organization.members + 1
        clear_organization_cache(organization, user)
        db.session.add(member)
        db.session.add(organization)
        db.session.commit()
        return member, None
    except sqlalchemy.exc.IntegrityError, e:
        if 'Duplicate entry' in e.message:
            return None, code.ORGANIZATION_MEMBER_EXISTS

def create_team(name, user, organization, members=0):
    try:
        team = Team(organization.id, name, members)
        db.session.add(team)
        db.session.flush()
        team_member = TeamMembers(team.id, user.id)
        organization.teams = Organization.teams + 1
        db.session.add(team_member)
        db.session.commit()
        clear_organization_cache(organization)
        clear_team_cache(organization, team, user)
        return team, None
    except sqlalchemy.exc.IntegrityError, e:
        if 'Duplicate entry' in e.message:
            return None, code.ORGANIZATION_TEAM_EXISTS

def create_team_members(organization, team, user):
    try:
        team_member = TeamMembers(team.id, user.id)
        team.members = Team.members + 1
        db.session.add(team_member)
        db.session.add(team)
        db.session.commit()
        clear_team_cache(organization, team, user)
        return team_member, None
    except sqlalchemy.exc.IntegrityError, e:
        if 'Duplicate entry' in e.message:
            return None, code.ORGANIZATION_TEAM_MEMBER_EXISTS

def create_verify(stub, email, name, git, admin=0):
    verify = get_unique_verify(git, email)
    if verify and (datetime.now()  - verify.created).total_seconds > config.VERIFY_STUB_EXPIRE:
        clear_verify(verify)
    elif verify:
        return verify, None
    try:
        verify = Verify(stub, email, name, git, admin)
        db.session.add(verify)
        db.session.commit()
        return verify, None
    except sqlalchemy.exc.IntegrityError, e:
        if 'Duplicate entry' in e.message:
            return None, code.VERIFY_ALREAD_EXISTS

# Update

def quit_team(organization, team, team_member, user):
    team.members = Team.members - 1
    db.session.delete(team_member)
    db.session.add(team)
    db.session.commit()
    clear_team_cache(organization, team, user)

def update_team(organization, old_team, team, name, pic):
    try:
        if name:
            team.name = name
        if pic:
            team.pic = pic
        db.session.add(team)
        db.session.commit()
        clear_team_cache(organization, old_team)
        return team, None
    except sqlalchemy.exc.IntegrityError, e:
        if 'Duplicate entry' in e.message:
            return None, code.ORGANIZATION_TEAM_EXISTS

