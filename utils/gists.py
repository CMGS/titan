#!/usr/local/bin/python2.7
#coding:utf-8

import logging
from functools import wraps
from flask import abort, g, url_for
from utils.local import reqcache

import config
from utils.jagare import get_jagare
from utils.repos import get_tree_with_content
from utils.helper import Obj, generate_list_page

from query.gists import get_gist, get_gist_by_private

logger = logging.getLogger(__name__)

def gist_require(owner=False):
    def _gist_require(f):
        @wraps(f)
        def _(organization, member, *args, **kwargs):
            gid = kwargs.pop('gid', None)
            private = kwargs.pop('private', None)
            if not gid and not private:
                raise abort(404)
            gist = get_gist(gid) if gid else get_gist_by_private(private)
            if not gist:
                raise abort(404)
            if gist.private and not private:
                raise abort(403)
            if owner and g.current_user.id != gist.uid and not member.admin:
                raise abort(403)
            set_gist_meta(organization, gist)
            return f(organization, member, gist, *args, **kwargs)
        return _
    return _gist_require

def set_gist_meta(organization, gist):
    meta = Obj()
    meta.watch = get_url(organization, gist, 'gists.watch')
    meta.unwatch = get_url(organization, gist, 'gists.unwatch')
    meta.watchers = get_url(organization, gist, 'gists.watchers')
    meta.view = get_url(organization, gist, 'gists.view')
    meta.edit = get_url(organization, gist, 'gists.edit')
    meta.fork = get_url(organization, gist, 'gists.fork')
    meta.forks = get_url(organization, gist, 'gists.forks')
    meta.delete = get_url(organization, gist, 'gists.delete')
    meta.revisions = get_url(organization, gist, 'gists.revisions')
    if gist.parent:
        meta.parent = set_gist_meta(organization, get_gist(gist.parent))
    @reqcache('gist:revisions:count:{gid}')
    def count_revisions(gid):
        jagare = get_jagare(gist.id, gist.parent)
        error, ret = jagare.get_log(gist.get_real_path(), total=1)
        count = 0 if error else ret['total']
        return count
    meta.count_revisions = lambda: count_revisions(gist.id)
    setattr(gist, 'meta', meta)

def get_url(organization, gist, view='gists.view', **kwargs):
    if gist.private:
        url = url_for(view, git=organization.git, private=gist.private, **kwargs)
    else:
        url = url_for(view, git=organization.git, gid=gist.id, **kwargs)
    return url

def render_tree(jagare, tree, gist, organization, render=True, version='master'):
    ret = get_tree_with_content(jagare, tree, gist, organization, render, version)
    for r in ret:
        r.download = get_url(organization, gist, view='gists.raw', path=r.path)
    return ret

def render_revisions_page(gist, page=1):
    count = gist.meta.count_revisions()
    has_prev = True if page > 1 else False
    has_next = True if page * config.REVISIONS_PER_PAGE < count else False
    pages = count / config.REVISIONS_PER_PAGE
    pages += 1 if count % config.REVISIONS_PER_PAGE else 0
    list_page = generate_list_page(count, has_prev, has_next, page, pages)
    return list_page

