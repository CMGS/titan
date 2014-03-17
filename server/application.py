#!/usr/bin/python
#coding:utf-8

import os
import time
import logging
import mimetypes

logger = logging.getLogger()
from gunicorn.app.base import Application

from gzipper import GzipMiddelware

class SHEEPApplication(Application):
    def __init__(self, usage=None, on_init=None):
        self.on_init = on_init
        super(SHEEPApplication, self).__init__(usage=usage)

    def init(self, parser, opts, args):
        if len(args) != 1:
            parser.error("No application root specified.")

        self.root_path = args[0]
        if callable(self.on_init):
            self.on_init(self)

    def load(self):
        app = WSGIApplication()
        app = GzipMiddelware(app)
        return app

class WSGIApplication(object):
    def __init__(self, appconf):
        self.appconf = appconf
        self.handlers = None

    def __call__(self, environ, start_response):
        path_info = environ['PATH_INFO'] or '/'
        if self.handlers is None:
            self.handlers = []
            for h in self.appconf['handlers']:
                app_handler = handler_factory(h)
                self.handlers.append(app_handler)

        for handler in self.handlers:
            m = handler.match(path_info)
            if m:
                environ['sheep.matched'] = m
                return handler(environ, start_response)

        start_response('404 Not Found', [])
        return ["404 Not Found"]

class StaticFilesApplication(object):
    def __new__(cls, path_template):
        def call(self, environ, start_response):
            from sheep.api.statics import static_files
            path = environ['PATH_INFO'] or '/'
            if not path.startswith('/'):
                path = '/' + path
            start_response('301 Moved Permanently', \
                        [('Location', static_files(path)), ])
            return ''
        if not is_sdk_env():
            cls.__call__ = call
        obj = object.__new__(StaticFilesApplication, path_template)
        return obj

    def __init__(self, path_template):
        self.path_template = path_template

    def __call__(self, environ, start_response):
        m = environ['sheep.matched']
        path = m.expand(self.path_template)
        return StaticFileApplication(path)(environ, start_response)

class StaticFileApplication(object):
    def __init__(self, path):
        self.path = path

    def _get_last_modified(self, path):
        return os.stat(path).st_mtime

    def _generate_last_modified_string(self, path):
        mtime = self._get_last_modified(path)
        return time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(mtime))

    def _if_modified_since(self, path, timestr):
        try:
            t = time.mktime(time.strptime(timestr, "%a, %d %b %Y %H:%M:%S GMT"))
        except ValueError:
            return True
        else:
            t -= time.timezone  # convert gmt to local time
            mtime = self._get_last_modified(path)
            return mtime > t

    def __call__(self, environ, start_response):
        path = os.path.join(os.environ['SHEEP_APPROOT'], self.path)
        if os.path.isfile(path):
            mimetype = mimetypes.guess_type(path)[0] or 'text/plain'
            last_modified = self._generate_last_modified_string(path)
            headers = [
                ('Content-type', mimetype),
                ('Last-Modified', last_modified),
            ]

            ims = environ.get('HTTP_IF_MODIFIED_SINCE')
            if ims and not self._if_modified_since(path, ims):
                start_response('304 Not Modified', headers)
                return ''

            start_response('200 OK', headers)
            return open(path)
        else:
            start_response('404 Not Found', [])
            return ['File not found']

