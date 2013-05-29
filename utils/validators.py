#!/usr/local/bin/python2.7
#coding:utf-8

# TODO refactor
import re

def check_password(password):
    if not password:
        return False, 'need password'
    if not re.search(r'[\S]{6,}', password, re.I):
        return False, 'password invaild'

def check_domain(domain):
    if not domain:
        return False, 'need domain'
    if not re.search(r'^[a-zA-Z0-9_-]{4,10}$', domain, re.I):
        return False, 'domain invail'

def check_username(username):
    if not username:
        return False, 'need username'
    if not isinstance(username, unicode):
        username = unicode(username, 'utf-8')
    if not re.search(ur'^[\u4e00-\u9fa5\w]{1,20}$', username, re.I):
        return False, 'username invail'

def check_email(email):
    if not email:
        return False, 'need email'
    if not re.search(r'^.+@[^.].*\.[a-z]{2,10}$', email, re.I):
        return False, 'email invaild'

def check_email_exists(email):
    if not email:
        return False, 'need email'
    from query.account import get_user_by_email
    user = get_user_by_email(email)
    if user:
        return False, 'email exists'

def check_domain_exists(domain):
    if not domain:
        return False, 'need domain'
    from query.account import get_user_by_domain
    user = get_user_by_domain(domain)
    if user:
        return False, 'domain exists'

def check_update_info(username):
    status = check_username(username),
    if status:
        return status
    return True, None

def check_register_info(username, email, password):
    '''
    username a-zA-Z0-9_-, >4 <20
    email a-zA-Z0-9_-@a-zA-Z0-9.a-zA-Z0-9
    password a-zA-Z0-9_-!@#$%^&*
    '''
    check_list = [
        check_username(username),
        check_email(email),
        check_email_exists(email),
        check_password(password),
    ]
    for status in check_list:
        if not status:
            continue
        return status
    return True, None

def check_login_info(email, password):
    check_list = [
        check_password(password),
        check_email(email),
    ]
    for status in check_list:
        if not status:
            continue
        return status
    return True, None

def check_name(name):
    if not name:
        return False, 'need name'
    if not isinstance(name, unicode):
        name = unicode(name, 'utf-8')
    if not re.search(ur'^[\u4e00-\u9fa5\w]{1,30}$', name, re.I):
        return False, 'name invail'

