#!/usr/local/bin/python2.7
#coding:utf-8

DEBUG = False

DATABASE_URI = 'mysql://'

SESSION_KEY = 'tid'
SESSION_ENVIRON_KEY = 'titan.session'
SESSION_COOKIE_DOMAIN = '127.0.0.1'
MAX_CONTENT_LENGTH = 512 * 1024

TOKEN_LENGTH = 6

SMTP_SERVER = 'smtp.qq.com'
SMTP_USER = 'service@xiaomen.co'
SMTP_PASSWORD = 'xiaomenkou!@#$%^'

FORGET_STUB_EXPIRE = 30*60
FORGET_EMAIL_TITLE = '取回密码'

try:
    from local_config import *
except:
    pass

