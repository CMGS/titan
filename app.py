#!/usr/local/bin/python2.7
#coding:utf-8

import os
import logging

import config
config.init_config('config.yaml', 'local_config.yaml')

from models import init_db
from views import init_views
from query.account import get_current_user
from query.organization import get_organizations_by_uid, \
        get_organization

from libs.statics import static_files, \
        upload_files
from libs.sessions import SessionMiddleware, \
    RedisSessionStore
from libs.colorlog import ColorizingStreamHandler

from werkzeug.wsgi import SharedDataMiddleware

from flaskext.csrf import csrf
from flask import Flask, request, g, render_template

from redis import ConnectionPool

app = Flask(__name__, \
        static_url_path='/static')
app.debug = config.DEBUG
app.secret_key = config.SECRET_KEY
app.jinja_env.filters['s_files'] = static_files
app.jinja_env.filters['u_files'] = upload_files

config.init_config

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

logging.StreamHandler = ColorizingStreamHandler
logging.BASIC_FORMAT = "%(asctime)s [%(name)s] %(message)s"
logging.basicConfig(level=logging.DEBUG if config.DEBUG else logging.INFO)

pool = ConnectionPool(
        host=config.REDIS_HOST, port=config.REDIS_PORT, \
        db=config.REDIS_DB, password=config.REDIS_PASSWORD, \
        max_connections=config.REDIS_POOL_SIZE)

store = RedisSessionStore(key_template=config.SESSION_KEY_TEMPLE, \
        expire=config.SESSION_EXPIRE, \
        salt=config.SESSION_SALT, pool=pool)

app.wsgi_app = SessionMiddleware(app.wsgi_app, \
        store,
        cookie_name=config.SESSION_KEY, \
        cookie_age=config.COOKIE_MAX_AGE, \
        cookie_path='/', \
        cookie_expires=None, \
        cookie_secure=None, \
        cookie_httponly=False, \
        cookie_domain=config.COOKIE_DOMAIN, \
        environ_key=config.SESSION_ENVIRON_KEY)

app.wsgi_app = SharedDataMiddleware(app.wsgi_app, \
        {'/static': os.path.join(os.path.dirname(__file__), 'static')})


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

