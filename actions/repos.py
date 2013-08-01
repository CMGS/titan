#!/usr/local/bin/python2.7
#coding:utf-8

import time
import msgpack
import logging
import threading

from utils.redistore import rdb
from utils.jagare import get_jagare
from utils.timeline import get_repo_activities, get_user_activities, \
        get_activities

REFS_KEYS = 'repo:refs:{rid}'
HEAD_COMMIT_KEY = 'repo:commits:{rid}:{start}:head'
LAST_COMMIT_KEY = 'repo:commits:{rid}:{start}:last'

PUSH_COMMITS_LIMIT = 5

logger = logging.getLogger(__name__)

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
    err, logs = jagare.get_log(repo.get_real_path(), start, head, shortstat=1) or \
                jagare.get_log(repo.get_real_path(), start, last, shortstat=1) or \
                jagare.get_log(repo.get_real_path(), start, None, shortstat=1)
    if err:
        logger.exception(err)
        return
    if not logs:
        return

    commit_time = time.mktime(repo.update.timetuple())
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

