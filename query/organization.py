#!/usr/local/bin/python2.7
#coding:utf-8

from sheep.api.cache import cache, backend
from models.organization import Organization, Members, Team

@cache('organization:{oid}', 86400)
def get_organization(oid):
    return Organization.query.get(oid)

@cache('organization:member:{oid}:{uid}', 86400)
def get_member(oid, uid):
    return Members.query.filter_by(oid=oid, uid=uid).limit(1).first()

@cache('organization:{token}', 300)
def get_org_by_token(token):
    return get_org_by(token=token).limit(1).first()

def clear_organization_cache(organization, user=None):
    keys = ['organization:%s' % key for key in [str(organization.id), organization.token]]
    if user:
        keys.append('organization:member:{oid}:{uid}'.format(oid=organization.id, uid=user.id))
    backend.delete_many(*keys)

def get_org_by(**kw):
    return Organization.query.filter_by(**kw)

create_organization = Organization.create
create_members = Members.create

