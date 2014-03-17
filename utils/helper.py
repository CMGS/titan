#!/usr/local/bin/python2.7
#coding:utf-8

import hashlib
import threading
from flask import render_template
from flask.views import MethodView as _

class MethodView(_):
    def __init__(self, module, tmpl):
        super(MethodView, self).__init__()
        self.filename = '%s.%s.html' % (module, tmpl)

    def render_template(self, **kwargs):
        return render_template(self.filename, **kwargs)

    @classmethod
    def as_view(cls, name, *class_args, **class_kwargs):
        def view(*args, **kwargs):
            return view.instance.dispatch_request(*args, **kwargs)

        if cls.decorators:
            view.__name__ = name
            view.__module__ = cls.__module__
            for decorator in cls.decorators:
                view = decorator(view)

        view.instance = cls(*class_args, **class_kwargs)
        view.__name__ = name
        view.__doc__ = cls.__doc__
        view.__module__ = cls.__module__
        view.methods = cls.methods
        return view

def make_view(module_name):
    def generate_view_func(cls, **kwargs):
        module = kwargs.get('module', None) or module_name
        name = kwargs.get('name', None) or cls.__name__.lower()
        tmpl = kwargs.get('tmpl', None) or name
        as_view = getattr(cls, 'as_view')
        view = as_view(name, module, tmpl)
        return view
    return generate_view_func

class Obj(object):pass

def get_hash(content, t='md5'):
    m = hashlib.new(t)
    if isinstance(content, unicode):
        content = content.encode('utf8')
    m.update(content)
    return m.hexdigest()

def generate_list_page(count, has_prev, has_next, page, pages):
    list_page = Obj()
    list_page.count = count
    list_page.has_prev = has_prev
    list_page.has_next = has_next
    list_page.page = page
    list_page.pages = pages
    list_page.iter_pages = xrange(1, pages + 1)
    return list_page

local = None
def get_local():
    global local
    if local is None:
        local = threading.local()
    return local

def set_environ(environ):
    get_local().environ = environ

def get_environ():
    return getattr(get_local(), 'environ', {})

