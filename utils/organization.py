#!/usr/local/bin/python2.7
#coding:utf-8

import logging
from PIL import Image
from functools import wraps
from cStringIO import StringIO
from flask import g, render_template, url_for, \
        abort, redirect

from utils import code
from config import ALLOWED_EXTENSIONS
from utils.mail import async_send_mail
from query.organization import get_organization_member, get_organization_by_git, \
        get_team_by_name, get_team_member

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
            git = kwargs.pop('git', None)
            if not git:
                raise abort(404)
            organization = get_organization_by_git(git)
            if not organization:
                raise abort(404)
            member = get_organization_member(organization.id, g.current_user.id)
            if not member:
                raise abort(403)
            if admin and not member.admin:
                raise abort(403)
            return f(organization, member,  *args, **kwargs)
        return _
    return _member_required

def team_member_required(need=True):
    def _team_member_required(f):
        @wraps(f)
        def _(organization, member, *args, **kwargs):
            team_name = kwargs.pop('tname', None)
            if not team_name:
                raise abort(404)
            team = get_team_by_name(organization.id, team_name)
            if not team:
                raise abort(404)
            team_member = get_team_member(team.id, g.current_user.id)
            if need and not team_member:
                return redirect(url_for('organization.viewteam', git=organization.git, tname=team.name))
            return f(organization, member, team, team_member, *args, **kwargs)
        return _
    return _team_member_required

def process_file(team, upload_file):
    if not allowed_file(upload_file.filename):
        return None, None, 'invalid %s' % upload_file.filename
    suffix = upload_file.filename.rsplit('.', 1)[1]
    filename = 't%d.jpg' % team.id
    stream = upload_file.stream
    error = None
    if suffix == 'png' or suffix == 'gif':
        try:
            stream = StringIO()
            image = Image.open(upload_file.stream)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            image.save(stream, 'jpeg')
            stream.getvalue()
            stream.seek(0)
        except Exception, e:
            logger.exception('convert error')
            error = str(e)
    return filename, stream, error

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

