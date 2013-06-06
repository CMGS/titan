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

def check_domain(domain):
    if not domain:
        return False
    if not re.search(r'^[a-zA-Z0-9_-]{4,10}$', domain, re.I):
        return False
    return True

def check_username(username):
    if not username:
        return False
    if not isinstance(username, unicode):
        username = unicode(username, 'utf-8')
    if not re.search(ur'^[\u4e00-\u9fa5\w]{1,20}$', username, re.I):
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

# FOR Organization

def check_organization_name(name):
    if not name:
        return False
    if not isinstance(name, unicode):
        name = unicode(name, 'utf-8')
    if not re.search(ur'^[\u4e00-\u9fa5\w]{1,30}$', name, re.I):
        return False
    return True

def check_git(git):
    '''Team and organization git name checker'''
    if not git:
        return False
    if not re.search(r'^[a-zA-Z0-9_-]{3,10}$', git, re.I):
        return False
    if git in BLACK_LIST:
        return False
    return True

def check_organization_plan(organization, incr=0):
    # TODO 计算有多少人了
    if organization.members + incr > config.PLAN[organization.plan]:
        return False
    return True

# TODO split to db
BLACK_LIST = [
    'register', 'team', 'account', \
    'login', 'logout', 'forget', 'reset', \
    'setting', 'invite', 'organization',
]
