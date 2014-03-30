#!/usr/bin/python
#coding:utf-8

import logging
import config
from time import time
from random import random
try:
    from hashlib import sha1
except ImportError:
    from sha import new as sha1

from redis import Redis
from werkzeug.contrib import sessions
from werkzeug.contrib.sessions import SessionStore
from werkzeug.wsgi import ClosingIterator
from werkzeug.utils import dump_cookie, parse_cookie

logger = logging.getLogger(__name__)

class SessionMiddleware(sessions.SessionMiddleware):
    def __init__(self, app, store, **kwargs):
        sessions.SessionMiddleware.__init__(self, app, store, **kwargs)

    def __call__(self, environ, start_response):
        cookie = parse_cookie(environ.get('HTTP_COOKIE', ''))
        sid = cookie.get(self.cookie_name, None)
        if sid is None or len(sid) != 40:
            session = self.store.new()
        else:
            session = self.store.get(sid)
        environ[self.environ_key] = session

        def injecting_start_response(status, headers, exc_info=None):
            if session.should_save:
                age = session.get('_titan_permstore', self.cookie_age)
                try:
                    age = int(age)
                except:
                    age = self.cookie_age
                self.store.save(session)
                headers.append(('Set-Cookie', dump_cookie(self.cookie_name,
                                session.sid, age,
                                self.cookie_expires, self.cookie_path,
                                self.cookie_domain, self.cookie_secure,
                                self.cookie_httponly)))
            return start_response(status, headers, exc_info)
        return ClosingIterator(self.app(environ, injecting_start_response),
                               lambda: self.store.save_if_modified(session))

def error_catch(method_name):
    def _(f):
        def middleware(*arg, **kwargs):
            try:
                return f(*arg, **kwargs)
            except Exception:
                logger.exception('%s operation error' % method_name)
                return None
        return middleware
    return _

class RedisSessionStore(SessionStore):
    """
    SessionStore that saves session to redis
    """
    def __init__(self, key_template=config.SESSION_KEY, expire=config.SESSION_EXPIRE, \
            salt=config.SESSION_SALT, pool=None):
        SessionStore.__init__(self)
        self.redis = Redis(connection_pool=pool)
        self.key_template = key_template
        self.expire = expire
        self.salt = salt

    def generate_key(self, salt):
        return sha1('%s%s%s' % (salt, time(), random())).hexdigest()

    def new(self):
        """Generate a new session."""
        return self.session_class({}, self.generate_key(self.salt), True)

    def get_session_key(self, sid):
        if isinstance(sid, unicode):
            sid = sid.encode('utf-8')
        return self.key_template % sid

    @error_catch('save')
    def save(self, session):
        key = self.get_session_key(session.sid)
        value = dict(session)
        if not value:
            return self.delete(session)
        if self.redis.hmset(key, value):
            return self.redis.expire(key, self.expire)

    @error_catch('delete')
    def delete(self, session):
        key = self.get_session_key(session.sid)
        return self.redis.delete(key)

    @error_catch('get')
    def get(self, sid):
        if not self.is_valid_key(sid):
            return self.new()

        key = self.get_session_key(sid)
        saved = self.redis.hgetall(key)
        return self.session_class(saved, sid, False)

    @error_catch('list')
    def list(self):
        """
        Lists all sessions in the store.
        """
        session_keys = self.redis.keys(self.key_template[:-2] + '*')
        return [s[len(self.key_template)-2:] for s in session_keys]

