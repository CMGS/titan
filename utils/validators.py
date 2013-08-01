#!/usr/local/bin/python2.7
#coding:utf-8

# TODO refactor
import re
import config
from utils import code

def check_password(password):
    if not password:
        return False
    if not re.search(r'[\S]{6,}', password, re.I):
        return False
    return True

def check_email(email):
    if not email:
        return False
    if not re.search(r'^.+@[^.].*\.[a-z]{2,10}$', email, re.I):
        return False
    return True

def check_register_info(username, email, password):
    '''
    username a-zA-Z0-9_-, >4 <20
    email a-zA-Z0-9_-@a-zA-Z0-9.a-zA-Z0-9
    password a-zA-Z0-9_-!@#$%^&*
    '''
    if not check_username(username):
        return False, code.ACCOUNT_USERNAME_INVAILD
    if not check_email(email):
        return False, code.ACCOUNT_EMAIL_INVAILD
    if not check_password(password):
        return False, code.ACCOUNT_PASSWORD_INVAILD
    return True, None

def check_login_info(email, password):
    if not check_email(email):
        return False, code.ACCOUNT_EMAIL_INVAILD
    if not check_password(password):
        return False, code.ACCOUNT_PASSWORD_INVAILD
    return True, None

# FOR Others

def check_unicode_name(name, n=1, m=16):
    if not name:
        return False
    if not isinstance(name, unicode):
        name = unicode(name, 'utf-8')
    if not re.search(ur'^[\u4e00-\u9fa5\w]{%d,%d}$' % (n, m), name, re.I):
        return False
    return True

check_display = check_unicode_name
check_key_usage = lambda usage: check_unicode_name(usage, m=30)
check_team_name = check_organization_name = lambda name: check_unicode_name(name, m=30)

def check_name(name, n=4, m=15):
    if not name:
        return False
    if not re.search(r'^[a-zA-Z0-9_-]{%d,%d}$' % (n, m), name, re.I):
        return False
    return True

check_username = lambda name: check_name(name, 2, 25)

# FOR Repos

def check_reponame(name):
    if name in BLACK_LIST:
        return False
    return check_name(name, 1, 30)

# FOR Organization

def check_git(git):
    '''Team and organization git name checker'''
    if git in BLACK_LIST:
        return False
    return check_name(git, n=3)

def check_members_limit(organization, incr=0):
    # TODO 计算有多少人了
    limit = config.MEMBERS_LIMIT[organization.plan]
    if limit == 999:
        return True
    if organization.members + incr > limit:
        return False
    return True

def check_repos_limit(organization, incr=0):
    # TODO 计算有多少仓库了
    limit = config.REPOS_LIMIT[organization.plan]
    if limit == 999:
        return True
    if organization.members + incr > limit:
        return False
    return True

# TODO split to db
BLACK_LIST = [
    'login', 'logout', 'forget', 'reset', 'register', 'setting', \
    'keys', 'alias', 'verify', 'delete', 'explore', 'settings', \
    'create', 'invite', 'add', 'join', 'quit', 'new', 'watchers', \
    'watch', 'unwatch', 'blob', 'list', 'remove', 'git', 'activities', \
    'teams', 'team', 'public', 'private', 'gist', 'edit', 'raw', 'tree', \
    'activity', 'hidden', 'logs', 'commits', 'commit', 'log', 'file', \
    'revisions', 'revision', 'rev', 'fork', 'forks', 'networks', 'network', \
]
