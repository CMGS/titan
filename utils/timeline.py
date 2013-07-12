#!/usr/local/bin/python2.7
#coding:utf-8

import time
import msgpack
import threading
from utils.helper import Obj
from utils.redistore import rdb
from utils.jagare import get_jagare

from query.repos import get_repo_watchers
from query.organization import get_organization, get_team

TIMELINE_EXPRIE = 60 * 60 * 24 * 30
PUSH_COMMITS_LIMIT = 5
MAX_ACTIVITIES_NUM = 1009
ACTIVITIES_PER_PAGE = 20

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

def after_delete_repo(repo, asynchronous=False):
    refs_keys = REFS_KEYS.format(rid=repo.id)
    for key in rdb.smembers(refs_keys):
        rdb.delete(key)
    rdb.delete(refs_keys)
    repo_activities = get_repo_activities(repo)
    data = [original for action, original, _ in repo_activities.get_activities()]
    for activities in get_activities(repo=repo):
        if not asynchronous:
            activities.delete(*data)
            continue
        t = threading.Thread(target=activities.delete, args=data)
        t.start()
    # redis py will delete empty sorted set
    # repo_activities.dispose()

def after_add_watcher(user, organization, repo, asynchronous=False):
    repo_activities = get_repo_activities(repo)
    user_activities = get_user_activities(organization, user.id)
    data = []
    for action, original, timestamp in repo_activities.get_activities(withscores=True):
        data.append(original)
        data.append(timestamp)
    if not asynchronous:
        user_activities.add(*data)
        return
    t = threading.Thread(target=user_activities.add, args=data)
    t.start()

def after_delete_watcher(user, organization, repo, asynchronous=False):
    repo_activities = get_repo_activities(repo)
    data = [original for action, original, _ in repo_activities.get_activities()]
    user_activities = get_user_activities(organization, user.id)
    if not asynchronous:
        user_activities.delete(*data)
        return
    t = threading.Thread(target=user_activities.delete, args=data)
    t.start()

def after_push_repo(user, repo, start='refs/heads/master', asynchronous=False):
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

    commit_time = time.time()
    data = {
        'type':'push', \
        'repo_id': repo.id, \
        'committer_id': user.id, \
        'commits_num': len(logs), \
        'commit_time': commit_time, \
        'branch': start, \
    }
    data['data'] = logs[:PUSH_COMMITS_LIMIT]
    rdb.set(head_key, logs[0]['sha'])
    rdb.set(last_key, logs[-1]['sha'])
    rdb.sadd(refs_keys, head_key)
    rdb.sadd(refs_keys, last_key)
    data = msgpack.dumps(data)
    for activities in get_activities(repo=repo):
        if not asynchronous:
            activities.add(data, commit_time)
            continue
        t = threading.Thread(target=activities.add, args=(data, commit_time))
        t.start()

def render_activities_page(page, t='repo', **kwargs):
    if t == 'repo':
        repo = kwargs['repo']
        activities = get_repo_activities(repo)
    elif t == 'organization':
        organization = kwargs['organization']
        activities = get_organization_activities(organization)
    elif t == 'team':
        team = kwargs['team']
        organization = kwargs['organization']
        activities = get_team_activities(organization, team)
    elif t == 'user':
        organization = kwargs['organization']
        uid = kwargs['uid']
        activities = get_user_activities(organization, uid)
    else:
        raise Exception('Not Implement %s Yet' % t)
    data = activities.get_activities(
                start=(page-1)*ACTIVITIES_PER_PAGE, \
                stop=page*ACTIVITIES_PER_PAGE-1, \
                withscores=True,
            )
    list_page = _get_list_page(activities, page)
    return data, list_page

def _get_list_page(activities, page=1):
    list_page = Obj()
    list_page.count = activities.count()
    list_page.has_prev = True if page > 1 else False
    list_page.has_next = True if page * ACTIVITIES_PER_PAGE < list_page.count else False
    list_page.page = page
    list_page.pages = (list_page.count / ACTIVITIES_PER_PAGE) + 1
    list_page.iter_pages = xrange(1, list_page.pages + 1)
    return list_page
