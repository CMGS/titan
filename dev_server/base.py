#!/usr/local/bin/python2.7
#coding:utf-8

import re
import logging

logger = logging.getLogger()

def handler_factory(config):
    from .web import WSGIAppHandler
    from .static import StaticFilesHandler
    mapping = [('wsgi_app', WSGIAppHandler),
               ('static_files', StaticFilesHandler),
              ]
    for handler_type, cls in mapping:
        if handler_type in config:
            return cls(config)

    raise InvalidAppConfigError("invalid handler type for %s" % config)

class BaseHandler(object):
    def __init__(self, config):
        self.config = config
        regex = self.make_url_regex(config)
        try:
            self.url_re = re.compile(regex)
        except re.error, e:
            raise InvalidAppConfigError('regex %s does not compile: %s' % (regex, e))

        self.app = self.make_app(config)

    def match(self, path_info):
        return self.url_re.match(path_info)

    def __call__(self, environ, start_response):
        return self.app(environ, start_response)

class WholeMatchMixIn(object):
    def make_url_regex(self, config):
        regex = config['url']
        if regex.startswith('^') or regex.endswith('$'):
            raise InvalidAppConfigError('regex starts with "^" or ends with "$"')
        return regex + '$'

class PrefixMatchMixIn(object):
    def make_url_regex(self, config):
        regex = config['url']
        if regex.startswith('^') or regex.endswith('$') or '(' in regex:
            raise InvalidAppConfigError('regex starts with "^" or ends with "$" or "(" in it')
        return regex + '.*'

class Error(Exception):
    """Base-class for exceptions in this module."""

class InvalidAppConfigError(Error):
    """This supplied application configuration file is invalid."""

