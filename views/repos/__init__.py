#!/usr/local/bin/python2.7
#coding:utf-8

from flask import Blueprint
from utils.helper import make_view

MODULE_NAME = 'repos'
view_func = make_view(MODULE_NAME)

repos = Blueprint(MODULE_NAME, __name__)
