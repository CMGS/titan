#!/usr/local/bin/python2.7
#coding:utf-8

import json
import logging
import requests

from utils import code

logger = logging.getLogger(__name__)

class Jagare(object):
    def __init__(self, node):
        self.node = node

    def init(self, path):
        try:
            r = requests.post('%s/%s/init' % (self.node, path))
            result = self.get_result(r)
            if not result or result['error']:
                return False, code.REPOS_INIT_FAILED
            return True, None
        except Exception, e:
            logger.exception(e)
            return False, code.UNHANDLE_EXCEPTION

    def clone(self, path, target_path):
        try:
            r = requests.post('%s/%s/clone/%s' % (self.node, path, target_path))
            result = self.get_result(r)
            if not result or result['error']:
                return False, code.REPOS_CLONE_FAILED
            return True, None
        except Exception, e:
            logger.exception(e)
            return False, code.UNHANDLE_EXCEPTION

    def delete(self, path):
        try:
            r = requests.get('%s/%s/delete' % (self.node, path))
            result = self.get_result(r)
            if not result or result['error']:
                return False, code.REPOS_DELETE_FAILED
            return True, None
        except Exception, e:
            logger.exception(e)
            return False, code.UNHANDLE_EXCEPTION

    def diff(self, repo_path, from_sha, to_sha=None, empty=None):
        try:
            url = '%s/%s/diff/%s' % (self.node, repo_path, from_sha)
            if to_sha:
                url = '%s/%s' % (url, to_sha)
            params = {'empty': empty}
            r = requests.get(url, params=params, stream = True)
            if not r.ok:
                return r.status_code, None
            return None, r
        except Exception, e:
            logger.exception(e)
            return 400, None

    def ls_tree(self, repo_path, path='', version='master'):
        try:
            url = '%s/%s/ls-tree/%s' % (self.node, repo_path, version)
            params = {'with_commit': 1}
            params['path'] = path if path else None
            r = requests.get(url, params=params)
            result = self.get_result(r)
            if not result:
                return code.REPOS_LS_TREE_FAILED, None
            if result['error']:
                return result['message'], None
            if not result['data']:
                return code.REPOS_PATH_NOT_FOUND, None
            return None, result['data']
        except Exception, e:
            logger.exception(e)
            return code.UNHANDLE_EXCEPTION, None

    def cat_file(self, repo_path, path, version='master'):
        try:
            r = requests.get(
                    '%s/%s/cat/path/%s' % (self.node, repo_path, version), \
                    params = {'path':path}, \
                    stream = True,
                )
            if not r.ok:
                return r.status_code, None
            return None, r
        except Exception, e:
            logger.exception(e)
            return 404, None

    def get_branches(self, repo_path):
        try:
            r = requests.get(
                    '%s/%s/list/branches' % (self.node, repo_path)
                )
            result = self.get_result(r)
            if not r.ok:
                return None
            return result['data']
        except Exception, e:
            logger.exception(e)
            return None

    def get_branches_names(self, repo_path):
        branches = self.get_branches(repo_path)
        if not branches:
            return []
        return [d['name'] for d in branches]

    def get_log(self, repo_path, start=None, \
            end=None, no_merges=None, size=None, \
            page=None, total=None, shortstat=None, \
            path=None,
        ):
        try:
            params = {
                'reference': start, \
                'from_ref': end, \
                'no_merges': no_merges, \
                'size': size, \
                'total': total, \
                'page': page, \
                'path': path,
                'shortstat': shortstat, \
            }
            r = requests.get(
                '%s/%s/log' % (self.node, repo_path), \
                params = params, \
            )
            result = self.get_result(r)
            if not r.ok or result['error']:
                return code.REPOS_GET_LOG_FAILED, None
            return None, result['data']
        except Exception, e:
            logger.exception(e)
            return code.UNHANDLE_EXCEPTION, None

    def set_default_branch(self, repo_path, branch='master'):
        try:
            r = requests.put(
                    '%s/%s/update-ref/HEAD' % (self.node, repo_path), \
                    data = {"newvalue" : "refs/heads/%s" % branch}
                )

            result = self.get_result(r)
            return result['error'], result['message']
        except Exception, e:
            logger.exception(e)
            return code.UNHANDLE_EXCEPTION, None

    def update_file(self, repo_path, data, user):
        try:
            r = requests.put(
                    '%s/%s/update-file/' % (self.node, repo_path), \
                    files = data, \
                    data = {
                        "author_name": user.name, \
                        "author_email": user.email, \
                        "message": code.GIST_UPDATE_COMMIT, \
                    }
                )
            result = self.get_result(r)
            if not r.ok or result['error']:
                return code.GIST_UPDATE_FAILED, None
            return None, result['data']
        except Exception, e:
            logger.exception(e)
            return code.UNHANDLE_EXCEPTION, None

    def get_result(self, r):
        return json.loads(r.text)

