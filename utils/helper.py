#!/usr/local/bin/python2.7
#coding:utf-8

from flask import render_template
from flask.views import MethodView

class TitanMethodView(MethodView):
    def __init__(self, module_name, view_name):
        super(MethodView, self).__init__()
        self.filename = '%s.%s.html' % (module_name, view_name)

    def render_template(self, **kwargs):
        return render_template(self.filename, **kwargs)

def generate_view_func(cls, name, module_name):
    as_view = getattr(cls, 'as_view')
    view = as_view(name, module_name, name)
    return view

