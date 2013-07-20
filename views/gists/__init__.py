#!/usr/local/bin/python2.7
#coding:utf-8

from flask import Blueprint
from utils.helper import make_view
from views.gists.view import View, Raw
from views.gists.explore import Explore
from views.gists.revisions import Revisions
from views.gists.gists import Create, Edit, Delete
from views.gists.watchers import Watchers, RemoveWatchers

MODULE_NAME = 'gists'
view_func = make_view(MODULE_NAME)

gists = Blueprint(MODULE_NAME, __name__)

raw = view_func(Raw)
edit = view_func(Edit)
view = view_func(View)
delete = view_func(Delete)
create = view_func(Create)

explore = view_func(Explore)
revisions = view_func(Revisions)

watch = view_func(Watchers, name='watch')
unwatch = view_func(RemoveWatchers, name='unwatch')

gists.add_url_rule('/<git>/gist/create', view_func=create, methods=['GET', 'POST'])
gists.add_url_rule('/<git>/gist/explore', view_func=explore, methods=['GET'])
gists.add_url_rule('/<git>/gist/<private>', view_func=view, methods=['GET', 'POST'])
gists.add_url_rule('/<git>/gist/<int:gid>', view_func=view, methods=['GET', 'POST'])

gists.add_url_rule('/<git>/gist/<private>/edit', view_func=edit, methods=['GET', 'POST'])
gists.add_url_rule('/<git>/gist/<int:gid>/edit', view_func=edit, methods=['GET', 'POST'])

gists.add_url_rule('/<git>/gist/<private>/revisions', view_func=revisions, methods=['GET'])
gists.add_url_rule('/<git>/gist/<int:gid>/revisions', view_func=revisions, methods=['GET'])

gists.add_url_rule('/<git>/gist/<private>/raw/<path:path>', view_func=raw, methods=['GET'])
gists.add_url_rule('/<git>/gist/<int:gid>/raw/<path:path>', view_func=raw, methods=['GET'])

gists.add_url_rule('/<git>/gist/<private>/delete', view_func=delete, methods=['GET'])
gists.add_url_rule('/<git>/gist/<int:gid>/delete', view_func=delete, methods=['GET'])

gists.add_url_rule('/<git>/gist/<private>/watch', view_func=watch, methods=['GET'])
gists.add_url_rule('/<git>/gist/<int:gid>/watch', view_func=watch, methods=['GET'])
gists.add_url_rule('/<git>/gist/<private>/unwatch', view_func=unwatch, methods=['GET'])
gists.add_url_rule('/<git>/gist/<int:gid>/unwatch', view_func=unwatch, methods=['GET'])

