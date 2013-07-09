#!/usr/local/bin/python2.7
#coding:utf-8

import gevent
from utils.redistore import rdb
from utils.jagare import get_jagare

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
    @staticmethod
    def after_push_async(repo, start='refs/heads/master'):
        gevent.spawn(Activities.after_push, repo, start)

    @staticmethod
    def after_push(repo, start='refs/heads/master'):
        activites_key = REPO_ACTIVITES_KEY.format(oid=repo.oid, rid=repo.id)
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
            Activities.add(activites_key, commits)
            rdb.set(head_key, logs[0]['sha'])
            rdb.set(last_key, logs[-1]['sha'])

    @staticmethod
    def add(activites_key, activites):
        rdb.zadd(activites_key, *activites)
        rdb.zremrangebyrank(activites_key, 0, -1 * (MAX_ACTIVITES_NUM + 1))

