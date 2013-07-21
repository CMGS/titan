#!/usr/local/bin/python2.7
#coding:utf-8

import time
import msgpack
import logging
import threading

from utils.redistore import rdb
from utils.jagare import get_jagare
from utils.timeline import get_gist_activities, get_user_activities, \
        get_activities

REFS_KEYS = 'gist:refs:{gid}'
HEAD_COMMIT_KEY = 'gist:commits:{gid}:head'
LAST_COMMIT_KEY = 'gist:commits:{gid}:last'

logger = logging.getLogger(__name__)

def after_delete_gist(gist, asynchronous=False):
    head_key = HEAD_COMMIT_KEY.format(gid=gist.id)
    last_key = LAST_COMMIT_KEY.format(gid=gist.id)
    rdb.delete(head_key, last_key)
    gist_activities = get_gist_activities(gist)
    data = [original for action, original, _ in gist_activities.get_activities()]
    for activities in get_activities(gist=gist):
        if not asynchronous:
            activities.delete(*data)
            continue
        t = threading.Thread(target=activities.delete, args=data)
        t.start()

def after_add_watcher(user, organization, gist, asynchronous=False):
    gist_activities = get_gist_activities(gist)
    user_activities = get_user_activities(organization, user.id)
    data = []
    for action, original, timestamp in gist_activities.get_activities(withscores=True):
        data.append(original)
        data.append(timestamp)
    if not asynchronous:
        user_activities.add(*data)
        return
    t = threading.Thread(target=user_activities.add, args=data)
    t.start()

def after_delete_watcher(user, organization, gist, asynchronous=False):
    gist_activities = get_gist_activities(gist)
    data = [original for action, original, _ in gist_activities.get_activities()]
    user_activities = get_user_activities(organization, user.id)
    if not asynchronous:
        user_activities.delete(*data)
        return
    t = threading.Thread(target=user_activities.delete, args=data)
    t.start()

def after_update_gist(user, gist, asynchronous=False):
    head_key = HEAD_COMMIT_KEY.format(gid=gist.id)
    last_key = LAST_COMMIT_KEY.format(gid=gist.id)

    head = rdb.get(head_key)
    last = rdb.get(last_key)

    # Get new commits from last commit
    jagare = get_jagare(gist.id, gist.parent)
    err, logs = jagare.get_log(gist.get_real_path(), head, shortstat=1) or \
                jagare.get_log(gist.get_real_path(), last, shortstat=1) or \
                jagare.get_log(gist.get_real_path(), None, shortstat=1)
    if err:
        logger.exception(err)
        return

    commit_time = time.time()
    data = {
        'type':'gist', \
        'gist_id': gist.id, \
        'committer_id': user.id, \
        'commits_num': len(logs), \
        'commit_time': commit_time, \
    }
    rdb.set(head_key, logs[0]['sha'])
    rdb.set(last_key, logs[-1]['sha'])
    data['data'] = logs
    data = msgpack.dumps(data)
    for activities in get_activities(gist=gist):
        if not asynchronous:
            activities.add(data, commit_time)
            continue
        t = threading.Thread(target=activities.add, args=(data, commit_time))
        t.start()

