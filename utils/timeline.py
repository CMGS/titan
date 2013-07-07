#!/usr/local/bin/python2.7
#coding:utf-8

import time
import gevent
from utils.redistore import rdb
from utils.jagare import get_jagare

from query.account import get_alias_by_email, \
        get_user

TIMELINE_EXPRIE = 60 * 60 * 24 * 30
TIMELINE_KEY = 'timeline:git:{path}'
LAST_COMMIT_KEY = 'timeline:git:{path}:{start}:last'

def get_user_from_alias(email):
    alias = get_alias_by_email(email)
    if not alias:
        return None
    return get_user(alias.uid)

class Timeline(object):
    @staticmethod
    def after_push_async(repo, start='refs/heads/master'):
        gevent.spawn(Timeline.after_push, repo, start)

    @staticmethod
    def after_push(repo, start='refs/heads/master'):
        deadline = time.time() - TIMELINE_EXPRIE
        last_key = LAST_COMMIT_KEY.format(path=repo.get_real_path(), start=start)
        end = rdb.get(last_key)
        jagare = get_jagare(repo.id, repo.parent)
        logs = jagare.get_log(repo.get_real_path(), start, end)
        if logs:
            commits = []
            for log in logs:
                action_time = float(log['committer_time'])
                if action_time < deadline:
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
                key = TIMELINE_KEY.format(path=repo.get_real_path())
                rdb.zadd(key, *commits)
                rdb.zremrangebyscore(key, 0, deadline)
            rdb.set(last_key, logs[0]['sha'])

    @classmethod
    def after_add_commiter(repo, user):
        pass

