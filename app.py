#!/usr/local/bin/python2.7
#coding:utf-8

import config
import logging

from models import init_db
from views import init_views
from query.account import get_current_user
from query.organization import get_organizations_by_uid, \
        get_organization

from sheep.api.statics import static_files, \
        upload_files
from sheep.api.sessions import SessionMiddleware, \
    FilesystemSessionStore

from flaskext.csrf import csrf
from flask import Flask, request, g, render_template

app = Flask(__name__)
app.debug = config.DEBUG
app.secret_key = config.SECRET_KEY
app.jinja_env.filters['s_files'] = static_files
app.jinja_env.filters['u_files'] = upload_files

app.config.update(
    SQLALCHEMY_DATABASE_URI = config.DATABASE_URI,
    SQLALCHEMY_POOL_SIZE = 1000,
    SQLALCHEMY_POOL_TIMEOUT = 10,
    SQLALCHEMY_POOL_RECYCLE = 3600,
    SESSION_COOKIE_DOMAIN = config.SESSION_COOKIE_DOMAIN,
    MAX_CONTENT_LENGTH = config.MAX_CONTENT_LENGTH,
)

logger = logging.getLogger(__name__)
init_db(app)
init_views(app)
csrf(app)
app.wsgi_app = SessionMiddleware(app.wsgi_app, \
        FilesystemSessionStore(), \
        cookie_name=config.SESSION_KEY, cookie_path='/', \
        cookie_domain=config.SESSION_COOKIE_DOMAIN, 
        environ_key=config.SESSION_ENVIRON_KEY)

@app.route('/')
def index():
    organizations = []
    if g.current_user:
        organizations = (get_organization(m.oid) for m in get_organizations_by_uid(g.current_user.id))
    return render_template('index.html', organizations=organizations)

@app.before_request
def before_request():
    g.session = request.environ.get(config.SESSION_ENVIRON_KEY)
    g.current_user = get_current_user()

