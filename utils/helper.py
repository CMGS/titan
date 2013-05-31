#!/usr/local/bin/python2.7
#coding:utf-8

from flask import render_template
from flask.views import MethodView as _

class MethodView(_):
    def __init__(self, module_name, view_name):
        super(MethodView, self).__init__()
        self.filename = '%s.%s.html' % (module_name, view_name)

    def render_template(self, **kwargs):
        return render_template(self.filename, **kwargs)

def make_view(module_name):
    def generate_view_func(cls, submodule_name=None):
        module = module_name
        if submodule_name:
            module = submodule_name
        name = cls.__name__.lower()
        as_view = getattr(cls, 'as_view')
        view = as_view(name, module, name)
        return view
    return generate_view_func

