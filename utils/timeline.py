#!/usr/local/bin/python2.7
#coding:utf-8

import gevent
from utils.redistore import rdb
from utils.jagare import get_jagare

from query.repos import get_repo_watchers
from query.organization import get_organization, get_team

TIMELINE_EXPRIE = 60 * 60 * 24 * 30
MAX_ACTIVITES_NUM = 1009

HEAD_COMMIT_KEY = 'activites:git:{oid}:{rid}:{start}:head'
LAST_COMMIT_KEY = 'activites:git:{oid}:{rid}:{start}:last'

# Create Pull Request/Push/Merge/Add or Edit a File
REPO_ACTIVITES_KEY = 'activites:git:{oid}:{rid}'
# Repos Activities
USER_ACTIVITES_KEY = 'activites:user:{oid}:{uid}'
# Join/Quit + Repos Activities
TEAM_ACTIVITES_KEY = 'activites:team:{oid}:{tid}'
# Public Team Activities
ORGANIZATION_ACTIVITES_KEY = 'activites:organization:{oid}'

class Activities(object):
    def __init__(self, activites_key):
        self.activites_key = activites_key

    @classmethod
    def get(cls, activites_key):
        return cls(activites_key)

    def add(self, activites):
        rdb.zadd(self.activites_key, *activites)
        rdb.zremrangebyrank(self.activites_key, 0, -1 * (MAX_ACTIVITES_NUM + 1))

    def get_activities(self, start=0, stop=MAX_ACTIVITES_NUM):
        data = rdb.zrevrange(self.activites_key, start, stop)
        return data

    def get_actions_by_timestamp(self, max='+inf', min='-inf'):
        data = rdb.zrevrangebyscore(self.activites, max, min)
        return data

def get_repo_activities(repo):
    return Activities.get(activites_key = REPO_ACTIVITES_KEY.format(oid=repo.oid, rid=repo.id))

def get_organization_activities(organization):
    return Activities.get(activites_key = ORGANIZATION_ACTIVITES_KEY.format(oid=organization.id))

def get_team_activities(organization, team):
    return Activities.get(activites_key = TEAM_ACTIVITES_KEY.format(oid=organization.id, tid=team.id))

def get_user_activities(organization, uid):
    return Activities.get(activites_key = USER_ACTIVITES_KEY.format(oid=organization.id, uid=uid))

def get_activites(organization=None, team=None, repo=None, **kwargs):
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

def after_push(repo, start='refs/heads/master', asynchronous=False):
    head_key = HEAD_COMMIT_KEY.format(oid=repo.oid, rid=repo.id, start=start)
    last_key = LAST_COMMIT_KEY.format(oid=repo.oid, rid=repo.id, start=start)

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
        message = log['message']
        sha = log['sha'][:10]
        action = 'push:{email}|{sha}|{message}'.format(
                    email=email, sha=sha, message=message
                )
        commits.append(action)
        commits.append(action_time)

    if commits:
        rdb.set(head_key, logs[0]['sha'])
        rdb.set(last_key, logs[-1]['sha'])
        for activites in get_activites(repo=repo, start=start):
            if not asynchronous:
                activites.add(commits)
                continue
            gevent.spawn(activites.add, commits)

