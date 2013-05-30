#!/usr/local/bin/python2.7
#coding:utf-8

DEBUG = False
SECRET_KEY = 'sheep!@$titan!#$%^'

DATABASE_URI = 'mysql://'

SESSION_KEY = 'tid'
SESSION_ENVIRON_KEY = 'titan.session'
SESSION_COOKIE_DOMAIN = '127.0.0.1'
MAX_CONTENT_LENGTH = 512 * 1024

TOKEN_LENGTH = 6

SMTP_SERVER = 'smtp.qq.com'
SMTP_USER = 'service@xiaomen.co'
SMTP_PASSWORD = 'xiaomenkou!@#$%^'

VERIFY_STUB_EXPIRE = 30*60
FORGET_STUB_EXPIRE = 30*60

GRAVATAR_BASE_URL = 'http://www.gravatar.com/avatar/'
GRAVATAR_EXTRA = ''

PLAN = {
    1: 3,
    2: 20,
    3: 50,
    4: 100,
    5: 150,
    6: 200,
    7: 999
}

try:
    from local_config import *
except:
    pass

