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

def check_name(name, n=16):
    if not name:
        return False
    if not isinstance(name, unicode):
        name = unicode(name, 'utf-8')
    if not re.search(ur'^[\u4e00-\u9fa5\w]{1,%d}$' % n, name, re.I):
        return False
    return True

check_display = check_name
check_key_usage = lambda usage: check_name(usage, 20)
check_team_name = check_organization_name = lambda name: check_name(name, 30)

def check_unique(u, n=4, m=10):
    if not u:
        return False
    if not re.search(r'^[a-zA-Z0-9_-]{%d,%d}$' % (n, m), u, re.I):
        return False
    return True

check_reponame = lambda name: check_unique(name, 1, 30)
check_username = lambda name: check_unique(name, 2, 25)

# FOR Organization

def check_git(git):
    '''Team and organization git name checker'''
    if not check_unique(git, n=3):
        return False
    if git in BLACK_LIST:
        return False
    return True

def check_organization_plan(organization, incr=0):
    # TODO 计算有多少人了
    if organization.members + incr > config.PACKAGE_PLAN[organization.plan]:
        return False
    return True

# TODO split to db
BLACK_LIST = [
    'register', 'team', 'account', \
    'login', 'logout', 'forget', 'reset', \
    'setting', 'invite', 'organization', \
    'keys', 'alias', 'repos', 'add', 'create', \
    'join', 'quit', \
]
