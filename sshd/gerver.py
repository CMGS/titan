#!/usr/local/bin/python2.7
#coding:utf-8

import os
import re
import select
import logging
import paramiko
import subprocess

from maria import utils
from maria.gerver import Gerver as _
from maria.config import config as _config

from config import MARIA_STORE_PATH

from utils.repos import check_permits
from query.repos import get_repo_by_path
from utils.timeline import after_push_repo
from query.account import get_key_by_finger, get_user
from query.organization import get_organization_by_git, \
        get_organization_member, get_team, get_team_member

logger = logging.getLogger(__name__)

SEARCH_PUSH_PATTERN = r'.*?(refs/heads/.*?)\n'

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
        if not self.check_command(command[0]):
            channel.sendall_stderr('Error: Wrong command.\n')
        elif not self.check_repo_exisit(path):
            channel.sendall_stderr('Error: Repository not found.\n')
        elif not self.check_user_permits(command[0]):
            channel.sendall_stderr('Error: Permission denied.\n')
        else:
            # 5 get true path
            command[-1] = self.get_store_path()
            self.command = command
        self.event.set()
        return True

    def get_store_path(self):
        return os.path.join(MARIA_STORE_PATH, self.repo.get_real_path())

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

    def check_repo_exisit(self, path):
        repo = get_repo_by_path(self.organization.id, path)
        if not repo:
            return False
        self.repo = repo
        return True

    def check_user_permits(self, command):
        # 4 check permits, organization admin can visit every repos
        # users can visit their own repos
        team = get_team(self.repo.tid) if self.repo.tid != 0 else None
        team_member = get_team_member(self.repo.tid, self.user.id) if self.repo.tid !=0 else None
        read, write = check_permits(self.user, self.repo, self.member, team, team_member)
        if not read and command == 'git-upload-pack':
            return False
        if not write and command == 'git-receive-pack':
            return False
        return True

    def after_execute(self, output, err):
        if 'git-receive-pack' in self.command and output:
            m = re.compile(SEARCH_PUSH_PATTERN, re.DOTALL)
            for start in m.findall(output):
                after_push_repo(self.user, self.repo, start, True)

    def main_loop(self, channel):
        if not self.command:
            return
        p = subprocess.Popen(self.command, \
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)

        ofd = p.stdout.fileno()
        efd = p.stderr.fileno()

        while True:
            r_ready, w_ready, x_ready = select.select(
                    [channel, ofd, efd], [], [], _config.select_timeout)

            if channel in r_ready:
                data = channel.recv(16384)
                if not data and (channel.closed or channel.eof_received):
                    break
                p.stdin.write(data)

            if ofd in r_ready:
                data = os.read(ofd, 16384)
                if not data:
                    break
                channel.sendall(data)

            if efd in r_ready:
                data = os.read(efd, 16384)
                channel.sendall(data)
                break

        output, err = p.communicate()
        if output:
            channel.sendall(output)
        if err:
            channel.sendall_stderr(err)
        channel.send_exit_status(p.returncode)
        channel.shutdown(2)
        channel.close()
        logger.info('Command execute finished')
        self.after_execute(output, err)

