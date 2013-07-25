#!/usr/local/bin/python2.7
#coding:utf-8

from flask import Blueprint
from utils.helper import make_view
from views.gists.explore import Explore
from views.gists.revisions import Revisions
from views.gists.view import View, Raw, Forks
from views.gists.gists import Create, Edit, Delete, Fork
from views.gists.watchers import Watch, Unwatch, Watchers

MODULE_NAME = 'gists'
view_func = make_view(MODULE_NAME)

gists = Blueprint(MODULE_NAME, __name__)

raw = view_func(Raw)
edit = view_func(Edit)
view = view_func(View)
forks = view_func(Forks)
delete = view_func(Delete)
create = view_func(Create)
fork = view_func(Fork)

explore = view_func(Explore)
revisions = view_func(Revisions)

watch = view_func(Watch)
unwatch = view_func(Unwatch)
watchers = view_func(Watchers)

gists.add_url_rule('/<git>/gist/create', view_func=create, methods=['GET', 'POST'])
gists.add_url_rule('/<git>/gist/explore', view_func=explore, methods=['GET'])

gists.add_url_rule('/<git>/gist/<private>', view_func=view, methods=['GET', 'POST'])
gists.add_url_rule('/<git>/gist/<int:gid>', view_func=view, methods=['GET', 'POST'])
gists.add_url_rule('/<git>/gist/<private>/<version>', view_func=view, methods=['GET', 'POST'])
gists.add_url_rule('/<git>/gist/<int:gid>/<version>', view_func=view, methods=['GET', 'POST'])

gists.add_url_rule('/<git>/gist/<private>/edit', view_func=edit, methods=['GET', 'POST'])
gists.add_url_rule('/<git>/gist/<int:gid>/edit', view_func=edit, methods=['GET', 'POST'])

gists.add_url_rule('/<git>/gist/<private>/revisions', view_func=revisions, methods=['GET'])
gists.add_url_rule('/<git>/gist/<int:gid>/revisions', view_func=revisions, methods=['GET'])

gists.add_url_rule('/<git>/gist/<private>/raw/<path:path>', view_func=raw, methods=['GET'])
gists.add_url_rule('/<git>/gist/<int:gid>/raw/<path:path>', view_func=raw, methods=['GET'])

gists.add_url_rule('/<git>/gist/<private>/delete', view_func=delete, methods=['GET'])
gists.add_url_rule('/<git>/gist/<int:gid>/delete', view_func=delete, methods=['GET'])

gists.add_url_rule('/<git>/gist/<private>/fork', view_func=fork, methods=['GET'])
gists.add_url_rule('/<git>/gist/<int:gid>/fork', view_func=fork, methods=['GET'])

gists.add_url_rule('/<git>/gist/<private>/forks', view_func=forks, methods=['GET'])
gists.add_url_rule('/<git>/gist/<int:gid>/forks', view_func=forks, methods=['GET'])

gists.add_url_rule('/<git>/gist/<private>/watch', view_func=watch, methods=['GET'])
gists.add_url_rule('/<git>/gist/<int:gid>/watch', view_func=watch, methods=['GET'])
gists.add_url_rule('/<git>/gist/<private>/unwatch', view_func=unwatch, methods=['GET'])
gists.add_url_rule('/<git>/gist/<int:gid>/unwatch', view_func=unwatch, methods=['GET'])
gists.add_url_rule('/<git>/gist/<private>/watchers', view_func=watchers, methods=['GET'])
gists.add_url_rule('/<git>/gist/<int:gid>/watchers', view_func=watchers, methods=['GET'])

