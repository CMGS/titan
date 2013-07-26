#!/usr/local/bin/python2.7
#coding:utf-8

from flask import Blueprint
from utils.helper import make_view
from views.repos.explore import Explore
from views.repos.view import View, Blob, Raw, Activities
from views.repos.watchers import Watch, Unwatch, Watchers
from views.repos.commiters import Commiters, RemoveCommiter
from views.repos.repos import Create, Transport, Delete, Setting

MODULE_NAME = 'repos'
view_func = make_view(MODULE_NAME)

repos = Blueprint(MODULE_NAME, __name__)

create = view_func(Create)
setting = view_func(Setting)
transport = view_func(Transport)
delete = view_func(Delete)
explore = view_func(Explore)
activities = view_func(Activities)

commiters = view_func(Commiters)
remove_commiter = view_func(RemoveCommiter, name='remove_commiter')
watch = view_func(Watch)
unwatch = view_func(Unwatch)
watchers = view_func(Watchers)

raw = view_func(Raw)
view = view_func(View)
blob = view_func(Blob)

repos.add_url_rule('/<git>/new', view_func=create, methods=['GET', 'POST'])

repos.add_url_rule('/<git>/<rname>/settings', view_func=setting, methods=['GET', 'POST'])
repos.add_url_rule('/<git>/<tname>/<rname>/settings', view_func=setting, methods=['GET', 'POST'])

repos.add_url_rule('/<git>/<rname>/commiters', view_func=commiters, methods=['GET', 'POST'])
repos.add_url_rule('/<git>/<tname>/<rname>/commiters', view_func=commiters, methods=['GET', 'POST'])

repos.add_url_rule('/<git>/<rname>/commiters/remove', view_func=remove_commiter, methods=['POST'])
repos.add_url_rule('/<git>/<tname>/<rname>/commiters/remove', view_func=remove_commiter, methods=['POST'])

repos.add_url_rule('/<git>/<rname>/transport', view_func=transport, methods=['GET', 'POST'])
repos.add_url_rule('/<git>/<tname>/<rname>/transport', view_func=transport, methods=['GET', 'POST'])

repos.add_url_rule('/<git>/<rname>/delete', view_func=delete, methods=['GET'])
repos.add_url_rule('/<git>/<tname>/<rname>/delete', view_func=delete, methods=['GET'])

repos.add_url_rule('/<git>/explore', view_func=explore, methods=['GET'])
repos.add_url_rule('/<git>/<tname>/explore', view_func=explore, methods=['GET'])

repos.add_url_rule('/<git>/<rname>/activity', view_func=activities, methods=['GET'])
repos.add_url_rule('/<git>/<tname>/<rname>/activity', view_func=activities, methods=['GET'])

repos.add_url_rule('/<git>/<rname>/watch', view_func=watch, methods=['GET'])
repos.add_url_rule('/<git>/<tname>/<rname>/watch', view_func=watch, methods=['GET'])

repos.add_url_rule('/<git>/<rname>/unwatch', view_func=unwatch, methods=['GET'])
repos.add_url_rule('/<git>/<tname>/<rname>/unwatch', view_func=unwatch, methods=['GET'])

repos.add_url_rule('/<git>/<rname>/watchers', view_func=watchers, methods=['GET'])
repos.add_url_rule('/<git>/<tname>/<rname>/watchers', view_func=watchers, methods=['GET'])

repos.add_url_rule('/<git>/<rname>', view_func=view, methods=['GET'])
repos.add_url_rule('/<git>/<tname>/<rname>', view_func=view, methods=['GET'])

repos.add_url_rule('/<git>/<rname>/tree/', view_func=view, methods=['GET'])
repos.add_url_rule('/<git>/<tname>/<rname>/tree/', view_func=view, methods=['GET'])

repos.add_url_rule('/<git>/<rname>/tree/<version>/', view_func=view, methods=['GET'])
repos.add_url_rule('/<git>/<tname>/<rname>/tree/<version>/', view_func=view, methods=['GET'])

repos.add_url_rule('/<git>/<rname>/tree/<version>/<path:path>', view_func=view, methods=['GET'])
repos.add_url_rule('/<git>/<tname>/<rname>/tree/<version>/<path:path>', view_func=view, methods=['GET'])

repos.add_url_rule('/<git>/<rname>/blob/<version>/<path:path>', view_func=blob, methods=['GET'])
repos.add_url_rule('/<git>/<tname>/<rname>/blob/<version>/<path:path>', view_func=blob, methods=['GET'])

repos.add_url_rule('/<git>/<rname>/raw/<version>/<path:path>', view_func=raw, methods=['GET'])
repos.add_url_rule('/<git>/<tname>/<rname>/raw/<version>/<path:path>', view_func=raw, methods=['GET'])

