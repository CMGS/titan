#!/usr/local/bin/python2.7
#coding:utf-8

import time
import base64
import logging
from flask import abort
from libs.code import render_code, render_diff

logger = logging.getLogger(__name__)

def format_time(ts):
    try:
        ts = float(ts)
        now = time.time()
        dur = now - ts
        if dur < 60:
            return '%d seconds ago' % dur
        elif dur < 60 * 60:
            return '%d minutes ago' % (dur / 60)
        elif dur < 60 * 60 * 24:
            return '%d hours ago' % (dur / 3600)
        elif dur < 86400 * 30:
            return '%d days ago' % (dur / 86400)
        elif dur < 31536000:
            return '%d months ago' % (dur / 2592000)
        else:
            return '%d years ago' % (dur / 31536000)
    except Exception, e:
        logger.exception(e)
        return '0'

def format_branch(branch):
    if branch.startswith('refs/heads/'):
        return branch.split('refs/heads/')[1]
    return branch

def format_diff(jagare, repo, from_sha, to_sha=None, empty=None, render=True):
    error, res = jagare.diff(repo.get_real_path(), from_sha, to_sha, empty)
    if error:
        raise abort(error)
    def _():
        c = res.content
        if not isinstance(c, unicode):
            c = c.decode('utf8')
        if render:
            c = render_diff(c)
        return c
    content = _
    return content

def format_content(jagare, repo, path, version='master', render=True):
    error, res = jagare.cat_file(repo.get_real_path(), path, version=version)
    if error:
        raise abort(error)

    content_type = res.headers.get('content-type', 'application/octet-stream')
    content_length = float(res.headers.get('content-length', 0.0)) / 1024

    if 'image' in content_type:
        content_type = 'image'
        content = lambda: base64.b64encode(res.content)
    elif 'text' in content_type:
        content_type = 'file'
        def _():
            c = res.content
            if not isinstance(c, unicode):
                c = c.decode('utf8')
            if render:
                c = render_code(path, c)
            return c
        content = _
    else:
        content_type = 'binary'
        content = lambda: res.content
    return content, content_type, content_length

