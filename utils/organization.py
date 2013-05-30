#!/usr/local/bin/python2.7
#coding:utf-8

import logging
from functools import wraps
from flask import g, render_template, url_for, abort, redirect

from utils import code
from utils.mail import async_send_mail
from query.organization import get_member, get_organization_by_git

logger = logging.getLogger(__name__)

def send_verify_mail(verify):
    url = url_for('account.register', stub=verify.stub, _external=True)
    content = render_template('email.invite.html', info=verify, url=url)
    async_send_mail(verify.email, code.EMAIL_INVITE_TITLE, content)

# USE login_required first
def member_required(admin=False):
    def _member_required(f):
        @wraps(f)
        def _(*args, **kwargs):
            if not g.current_user:
                return redirect(url_for('account.login'))
            git = kwargs.get('git', None)
            if not git:
                raise abort(404)
            organization = get_organization_by_git(git)
            if not organization:
                raise abort(404)
            member = get_member(organization.id, g.current_user.id)
            if not member:
                raise abort(403)
            if admin and not member.admin:
                raise abort(403)
            return f(*args, **kwargs)
        return _
    return _member_required

