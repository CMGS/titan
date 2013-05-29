#!/usr/local/bin/python2.7
#coding:utf-8

from flask import Blueprint
from flaskext.csrf import csrf_exempt

organization = Blueprint('organization', __name__)


