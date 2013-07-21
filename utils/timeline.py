#!/usr/local/bin/python2.7
#coding:utf-8

import msgpack
from utils.redistore import rdb

from query.repos import get_repo_watchers
from query.gists import get_gist_watchers
from query.organization import get_organization, get_team

TIMELINE_EXPRIE = 60 * 60 * 24 * 30
MAX_ACTIVITIES_NUM = 1009

# Updata/Delete
GIST_ACTIVITES_KEY = 'activities:gist:{oid}:{gid}'
# Create Pull Request/Push/Merge/Add or Edit a File
REPO_ACTIVITES_KEY = 'activities:repo:{oid}:{rid}'
# Repos Activities
USER_ACTIVITES_KEY = 'activities:user:{oid}:{uid}'
# Join/Quit + Repos Activities
TEAM_ACTIVITES_KEY = 'activities:team:{oid}:{tid}'
# Public Team Activities
ORGANIZATION_ACTIVITES_KEY = 'activities:organization:{oid}'

class Activities(object):
    def __init__(self, activities_key):
        self.activities_key = activities_key

    @classmethod
    def get(cls, activities_key):
        return cls(activities_key)

    def add(self, *activities):
        rdb.zadd(self.activities_key, *activities)
        rdb.zremrangebyrank(self.activities_key, 0, -1 * (MAX_ACTIVITIES_NUM + 1))

    def get_activities(self, start=0, stop=MAX_ACTIVITIES_NUM, withscores=False):
        data = rdb.zrevrange(self.activities_key, start, stop, withscores=withscores)
        for action in data:
            if withscores:
                timestamp = action[1]
                original = action[0]
                action = msgpack.loads(action[0])
            else:
                timestamp = -1
                original = action
                action = msgpack.loads(action)
            yield action, original, timestamp

    def get_actions_by_timestamp(self, max='+inf', min='-inf'):
        data = rdb.zrevrangebyscore(self.activities_key, max, min)
        return data

    def delete(self, *activities):
        return rdb.zrem(self.activities_key, *activities)

    def dispose(self):
        return rdb.delete(self.activities_key)

    def count(self):
        return rdb.zcard(self.activities_key)

def get_gist_activities(gist):
    return Activities.get(activities_key = GIST_ACTIVITES_KEY.format(oid=gist.oid, gid=gist.id))

def get_repo_activities(repo):
    return Activities.get(activities_key = REPO_ACTIVITES_KEY.format(oid=repo.oid, rid=repo.id))

def get_organization_activities(organization):
    return Activities.get(activities_key = ORGANIZATION_ACTIVITES_KEY.format(oid=organization.id))

def get_team_activities(organization, team):
    return Activities.get(activities_key = TEAM_ACTIVITES_KEY.format(oid=organization.id, tid=team.id))

def get_user_activities(organization, uid):
    return Activities.get(activities_key = USER_ACTIVITES_KEY.format(oid=organization.id, uid=uid))

def get_activities(organization=None, team=None, repo=None, gist=None):
    if gist:
        organization = get_organization(gist.oid)
        yield get_gist_activities(gist)
        yield get_user_activities(organization, gist.uid)
        for watcher in get_gist_watchers(gist.id):
            if watcher.uid == gist.uid:
                continue
            yield get_user_activities(organization, watcher.uid)
    if repo:
        organization = get_organization(repo.oid)
        team = get_team(repo.tid) if repo.tid else team
        yield get_repo_activities(repo)
        yield get_user_activities(organization, repo.uid)
        for watcher in get_repo_watchers(repo.id):
            if watcher.uid == repo.uid:
                continue
            yield get_user_activities(organization, watcher.uid)
    if team:
        yield get_team_activities(organization, team)
    if organization and (
            (gist and not gist.private) or
            (repo and (not team or not team.private))
        ):
        yield get_organization_activities(organization)

