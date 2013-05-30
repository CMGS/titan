#!/usr/local/bin/python2.7
#coding:utf-8

from sheep.api.cache import cache, backend
from models.organization import Organization, Team, Verify, \
        Members, TeamMembers

@cache('organization:{oid}', 86400)
def get_organization(oid):
    return Organization.query.get(oid)

@cache('organization:member:{oid}:{uid}', 86400)
def get_member(oid, uid):
    return Members.query.filter_by(oid=oid, uid=uid).limit(1).first()

@cache('organization:{git}', 86400)
def get_organization_by_git(git):
    return get_organization_by(git=git).limit(1).first()

@cache('organization:verify:{stub}', 300)
def get_verify_by_stub(stub):
    return Verify.query.filter_by(stub=stub).limit(1).first()

def clear_organization_cache(organization, user=None):
    keys = ['organization:%s' % key for key in [str(organization.id), organization.token]]
    if user:
        keys.append('organization:member:{oid}:{uid}'.format(oid=organization.id, uid=user.id))
    backend.delete_many(*keys)

def clear_verify_stub(verify):
    if not verify:
        return
    verify.delete()
    backend.delete('organization:verify:%s' % verify.stub)

def get_organization_by(**kw):
    return Organization.query.filter_by(**kw)

def create_organization(user, name, git, members=0, admin=0):
    organization = create_organization(name, git, members=1)
    create_members(organization.id, user.id, admin=1)
    clear_organization_cache(organization, user)
    return organization

create_organization = Organization.create
create_members = Members.create
create_verify = Verify.create

