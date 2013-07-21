#!/usr/local/bin/python2.7
#coding:utf-8

import logging
from functools import wraps
from flask import abort, g, url_for

from utils.repos import format_time
from utils.helper import Obj, generate_list_page
from utils.jagare import get_jagare, format_content
from query.gists import get_gist, get_gist_by_private

logger = logging.getLogger(__name__)

REVISIONS_PER_PAGE = 5

def gist_require(owner=False):
    def _gist_require(f):
        @wraps(f)
        def _(organization, member, *args, **kwargs):
            gid = kwargs.pop('gid', None)
            private = kwargs.get('private', None)
            if not gid and not private:
                raise abort(404)
            gist = get_gist(gid) if gid else get_gist_by_private(private)
            if not gist:
                raise abort(404)
            if owner and g.current_user.id != gist.uid and not member.admin:
                raise abort(403)
            set_gist_info(organization, gist)
            return f(organization, member, gist, *args, **kwargs)
        return _
    return _gist_require

def set_gist_info(organization, gist):
    meta = Obj()
    meta.watch = get_url(organization, gist, 'gists.watch')
    meta.unwatch = get_url(organization, gist, 'gists.unwatch')
    meta.view = get_url(organization, gist, 'gists.view')
    meta.edit = get_url(organization, gist, 'gists.edit')
    meta.delete = get_url(organization, gist, 'gists.delete')
    meta.revisions = get_url(organization, gist, 'gists.revisions')
    jagare = get_jagare(gist.id, gist.parent)
    error, ret = jagare.get_log(gist.get_real_path(), total=1)
    meta.revisions_count = 0 if error else ret['total']
    setattr(gist, 'meta', meta)

def get_url(organization, gist, view='gists.view', **kwargs):
    if gist.private:
        url = url_for(view, git=organization.git, private=gist.private, **kwargs)
    else:
        url = url_for(view, git=organization.git, gid=gist.id, **kwargs)
    return url

def render_tree(jagare, tree, gist, organization, render=True, version='master'):
    ret = []
    for d in tree:
        data = Obj()
        if d['type'] == 'blob':
            data.content, data.content_type, data.length = format_content(
                    jagare, gist, d['path'], render=render, version=version, \
            )
        else:
            continue
        data.download = get_url(organization, gist, view='gists.raw', path=d['path'])
        data.name = d['name']
        data.sha = d['sha']
        data.type = d['type']
        data.ago = format_time(d['commit']['committer']['ts'])
        data.message = d['commit']['message'][:150]
        data.commit = d['commit']['sha']
        data.path = d['path']
        ret.append(data)
    return ret

def render_revisions_page(gist, page=1):
    count = gist.meta.revisions_count
    has_prev = True if page > 1 else False
    has_next = True if page * REVISIONS_PER_PAGE < count else False
    pages = (count / REVISIONS_PER_PAGE) + 1
    list_page = generate_list_page(count, has_prev, has_next, page, pages)
    return list_page

