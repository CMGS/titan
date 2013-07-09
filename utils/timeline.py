#!/usr/local/bin/python2.7
#coding:utf-8

import time
import gevent
from utils.redistore import rdb
from utils.jagare import get_jagare

from query.account import get_alias_by_email, \
        get_user

TIMELINE_EXPRIE = 60 * 60 * 24 * 30

MAX_ACTIVITES_NUM = 50

REPO_ACTIVITES_KEY = 'activites:git:{oid}:{rid}'
HEAD_COMMIT_KEY = 'activites:git:{oid}:{rid}:{start}:head'
LAST_COMMIT_KEY = 'activites:git:{oid}:{rid}:{start}:last'

def get_user_from_alias(email):
    alias = get_alias_by_email(email)
    if not alias:
        return None
    return get_user(alias.uid)

class Activities(object):
    @staticmethod
    def after_push_async(repo, start='refs/heads/master'):
        gevent.spawn(Activities.after_push, repo, start)

    @staticmethod
    def after_push(repo, start='refs/heads/master'):
        start_time = time.time()
        deadline = start_time - TIMELINE_EXPRIE

        activites_key = REPO_ACTIVITES_KEY.format(oid=repo.oid, rid=repo.id)
        head_key = HEAD_COMMIT_KEY.format(oid=repo.oid, rid=repo.id, start=start)
        last_key = LAST_COMMIT_KEY.format(oid=repo.oid, rid=repo.id, start=start)

        head = rdb.get(head_key)
        head, head_time = head.split(':') if head else None, None
        last = rdb.get(last_key)
        last, last_time = last.split(':') if last else None, None

        # Get new commits from last commit
        jagare = get_jagare(repo.id, repo.parent)
        logs = jagare.get_log(repo.get_real_path(), start, head)
        if not logs:
            logs = jagare.get_log(repo.get_real_path(), start, last)
            if logs:
                delete_activites = [a for a in rdb.zrangebyscore(activites_key, last_time, head_time, start=1, num=MAX_ACTIVITES_NUM) if a.startswith('push:')]
                rdb.zrem(delete_activites)
            else:
                delete_activites = [a for a in rdb.zrangebyscore(activites_key, last_time, head_time) if a.startswith('push:')]
                rdb.zrem(delete_activites)
                logs = jagare.get_log(repo.get_real_path(), start, None)

        count = 0
        commits = []
        for log in logs:
            action_time = log['committer_time']
            if count > MAX_ACTIVITES_NUM or action_time < deadline:
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
            rdb.zadd(activites_key, *commits)
            rdb.zremrangebyscore(activites_key, 0, deadline)
            rdb.zremrangebyrank(activites_key, 0, -1 * (MAX_ACTIVITES_NUM + 1))

            rdb.set(head_key, '%s:%d' % (logs[0]['sha'], logs[0]['committer_time']))
            rdb.set(last_key, '%s:%d' % (logs[-1]['sha'], logs[-1]['committer_time']))

    @classmethod
    def after_add_commiter(repo, user):
        pass

