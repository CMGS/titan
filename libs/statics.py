#!/usr/bin/python
#coding:utf-8

static_files = lambda path: path

def upload_files(path):
    p = '/uploadfiles'
    if path and not path.startswith('/'):
        path = '/' + path
    elif not path:
        path = '/default.png'
    return p + path

