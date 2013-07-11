#!/usr/local/bin/python2.7
#coding:utf-8

import gevent
from utils.helper import Obj
from utils.redistore import rdb
from utils.jagare import get_jagare

from query.repos import get_repo_watchers
from query.organization import get_organization, get_team

TIMELINE_EXPRIE = 60 * 60 * 24 * 30
MAX_ACTIVITES_NUM = 1009

REFS_KEYS = 'repo:refs:{rid}'
HEAD_COMMIT_KEY = 'repo:commits:{rid}:{start}:head'
LAST_COMMIT_KEY = 'repo:commits:{rid}:{start}:last'

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

    def add(self, activities):
        rdb.zadd(self.activities_key, *activities)
        rdb.zremrangebyrank(self.activities_key, 0, -1 * (MAX_ACTIVITES_NUM + 1))

    def get_activities(self, start=0, stop=MAX_ACTIVITES_NUM, withscores=False):
        data = rdb.zrevrange(self.activities_key, start, stop, withscores=withscores)
        for action in data:
            d = Obj()
            if withscores:
                d.timestamp = action[1]
                action = action[0]
            d.orgin = action
            d.type, d.raw = action.split(':', 1)
            yield d

    def get_actions_by_timestamp(self, max='+inf', min='-inf'):
        data = rdb.zrevrangebyscore(self.activities_key, max, min)
        return data

    def delete(self, activities):
        rdb.zrem(self.activities_key, *activities)

    def dispose(self):
        rdb.delete(self.activities_key)

def get_repo_activities(repo):
    return Activities.get(activities_key = REPO_ACTIVITES_KEY.format(oid=repo.oid, rid=repo.id))

def get_organization_activities(organization):
    return Activities.get(activities_key = ORGANIZATION_ACTIVITES_KEY.format(oid=organization.id))

def get_team_activities(organization, team):
    return Activities.get(activities_key = TEAM_ACTIVITES_KEY.format(oid=organization.id, tid=team.id))

def get_user_activities(organization, uid):
    return Activities.get(activities_key = USER_ACTIVITES_KEY.format(oid=organization.id, uid=uid))

def get_activities(organization=None, team=None, repo=None, **kwargs):
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
    if organization and (not team or not team.private):
        yield get_organization_activities(organization)

def after_delete(repo, asynchronous=False):
    refs_keys = REFS_KEYS.format(rid=repo.id)
    for key in rdb.smembers(refs_keys):
        rdb.delete(key)
    rdb.delete(refs_keys)
    repo_activites = get_repo_activities(repo)
    data = [d.orgin for d in repo_activites.get_activities()]
    for activities in get_activities(repo=repo):
        if not asynchronous:
            activities.delete(data)
        gevent.spawn(activities.delete, data)
    # redis py will delete empty sorted set
    # repo_activites.dispose()

def after_push(repo, start='refs/heads/master', asynchronous=False):
    refs_keys = REFS_KEYS.format(rid=repo.id)
    head_key = HEAD_COMMIT_KEY.format(rid=repo.id, start=start)
    last_key = LAST_COMMIT_KEY.format(rid=repo.id, start=start)

    head = rdb.get(head_key)
    last = rdb.get(last_key)

    # Get new commits from last commit
    jagare = get_jagare(repo.id, repo.parent)
    logs = jagare.get_log(repo.get_real_path(), start, head) or \
            jagare.get_log(repo.get_real_path(), start, last) or \
            jagare.get_log(repo.get_real_path(), start, None)

    commits = []
    for log in logs:
        action_time = float(log['committer_time'])
        if len(commits) > MAX_ACTIVITES_NUM:
            break
        email = log['author_email']
        message = log['message'].strip()
        sha = log['sha'][:10]
        action = 'push:{email}|{sha}|{message}'.format(
                    email=email, sha=sha, message=message
                )
        commits.append(action)
        commits.append(action_time)

    if commits:
        rdb.set(head_key, logs[0]['sha'])
        rdb.set(last_key, logs[-1]['sha'])
        rdb.sadd(refs_keys, head_key)
        rdb.sadd(refs_keys, last_key)
        for activities in get_activities(repo=repo):
            if not asynchronous:
                activities.add(commits)
                continue
            gevent.spawn(activities.add, commits)

