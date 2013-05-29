#!/usr/local/bin/python2.7
#coding:utf-8

from sheep.api.cache import cache
from models.organization import Organization, Members, Team

@cache('organization:{oid}', 86400)
def get_organization(oid):
    return Organization.query.get(oid)

@cache('organization:member:{oid}:{uid}', 86400)
def get_member(oid, uid):
    return Members.query.filter_by(oid=oid, uid=uid).limit(1).first()

def get_org_by(**kw):
    return Organization.query.filter_by(**kw)

create_organization = Organization.create
create_members = Members.create

