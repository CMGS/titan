#!/usr/local/bin/python2.7
#coding:utf-8

import os
import logging
import paramiko

from maria import utils
from maria.gerver import Gerver as _

from query.repos import get_repo_by_path
from query.account import get_key_by_finger, get_user
from query.organization import get_organization_by_git, \
        get_organization_member, get_team, get_team_member

logger = logging.getLogger(__name__)

#TODO 因为现在还在本地测试，所以直接用文件路径
STORE_PATH = '/Users/CMGS/Documents/Workplace/experiment/Jagare/permdir/'

class Gerver(_):
    def check_auth_publickey(self, username, key):
        hex_fingerprint = utils.hex_key(key)
        logger.info('Auth attempt with key: %s' % hex_fingerprint)

        # 0. check organization exists
        organization = get_organization_by_git(username)
        if not organization:
            return paramiko.AUTH_FAILED

        # 1. check user exists
        key = get_key_by_finger(hex_fingerprint)
        if not key:
            return paramiko.AUTH_FAILED
        user = get_user(key.uid)
        if not user:
            return paramiko.AUTH_FAILED

        # 2. check user in organization
        member = get_organization_member(organization.id, user.id)
        if not member:
            return paramiko.AUTH_FAILED

        self.organization = organization
        self.member = member
        self.user = user

        return paramiko.AUTH_SUCCESSFUL

    def check_channel_exec_request(self, channel, command):
        logger.info('Command %s received' % command)
        command, path = self.parser_command(command)
        if not self.check_permits(command[0], path):
            self.event.set()
            return False
        # 5 get true path
        command[-1] = self.get_store_path(command[-1])
        self.command = command
        self.event.set()
        return True

    def get_store_path(self, path):
        return os.path.join(STORE_PATH, str(self.organization.id), path)

    def parser_command(self, command):
        if not command:
            return None, None
        command = command.split(' ')
        # 3 get git path
        command[-1] = command[-1].strip("'")
        return command, command[-1]

    def check_command(self, command):
        if not command or not command in ('git-receive-pack', 'git-upload-pack'):
            return False
        return True

    def check_permits(self, command, path):
        if not command or not command in ('git-receive-pack', 'git-upload-pack'):
            return False
        repo = get_repo_by_path(path)
        if not repo:
            return False
        # 4 check permits, organization admin can visit every repos
        # users can visit their own repos
        if not self.member.admin or not repo.uid != self.user.id:
            if repo.tid == 0:
                if self.check_user_permits(command, repo):
                    return True
                return False
            team = get_team(repo.tid)
            if not team:
                return False
            team_member = get_team_member(repo.tid, self.user.id)
            if not team_member:
                return False
            if team_member.admin or self.check_user_permits(command, repo):
                return True
            return False
        return True

    def check_user_permits(command, repo):
        # TODO 这里需要考虑仓库本身权限
        return True

