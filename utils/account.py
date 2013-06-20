#!/usr/local/bin/python2.7
#coding:utf-8

import base64
import hashlib
import logging
from functools import wraps
from flask import g, url_for, redirect, request, render_template

from utils import code
from utils.mail import async_send_mail

logger = logging.getLogger(__name__)

def login_required(next=None, need=True, *args, **kwargs):
    def _login_required(f):
        @wraps(f)
        def _(*args, **kwargs):
            if (need and not g.current_user) or \
                    (not need and g.current_user):
                if next:
                    if next != 'account.login':
                        url = url_for(next)
                    else:
                        url = url_for(next, redirect=request.url)
                    return redirect(url)
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return _
    return _login_required

def send_forget_mail(user, forget):
    content = render_template('email.forget.html', user=user, forget=forget)
    async_send_mail(user.email, code.EMAIL_FORGET_TITLE, content)

def send_verify_mail(email, url):
    content = render_template('email.verify.html', url=url)
    async_send_mail(email, code.EMAIL_VERIFY_TITLE, content)

def account_login(user):
    g.session['user_id'] = user.id
    g.session['user_token'] = user.token

def account_logout():
    g.session.clear()

def get_pubkey_finger(key):
    if not key:
        return None
    key = base64.b64decode(key)
    fp_plain = hashlib.md5(key).hexdigest()
    return fp_plain

def get_key(key):
    SIGN = 'AAAAB3NzaC1yc2EA'
    position = key.find(SIGN)
    if position == -1:
        return None
    return key[position:].split(' ', 1)[0]

def get_fingerprint(finger):
    return ':'.join((a+b for a,b in zip(finger[::2], finger[1::2])))

if __name__ == '__main__':
    b = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDJOtsej4dNSKTdMBnD8v6L0lZ1Tk+WTMlxsFf2+pvkdoAu3EB3RZ/frpyV6//bJNTDysyvwgOvANT/K8u5fzrOI2qDZqVU7dtDSwUedM3YSWcSjjuUiec7uNZeimqhEwzYGDcUSSXe7GNH9YsVZuoWEf1du6OLtuXi7iJY4HabU0N49zorXtxmlXcPeGPuJwCiEu8DG/uKQeruI2eQS9zMhy73Jx2O3ii3PMikZt3g/RvxzqIlst7a4fEotcYENtsJF1ZrEm7B3qOBZ+k5N8D3CkDiHPmHwXyMRYIQJnyZp2y03+1nXT16h75cer/7MZMm+AfWSATdp09/meBt6swD ilskdw@gmail.com'
    c = get_key(b)
    a = get_pubkey_finger(c)
    print a
    print c
    print get_fingerprint(a)
