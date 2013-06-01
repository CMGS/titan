#!/usr/local/bin/python2.7
#coding:utf-8

from flask import render_template
from flask.views import MethodView as _

class MethodView(_):
    def __init__(self, module, tmpl):
        super(MethodView, self).__init__()
        self.filename = '%s.%s.html' % (module, tmpl)

    def render_template(self, **kwargs):
        return render_template(self.filename, **kwargs)

def make_view(module_name):
    def generate_view_func(cls, **kwargs):
        module = kwargs.get('module', None) or module_name
        name = kwargs.get('name', None) or cls.__name__.lower()
        tmpl = kwargs.get('tmpl', None) or name
        as_view = getattr(cls, 'as_view')
        view = as_view(name, module, tmpl)
        return view
    return generate_view_func

