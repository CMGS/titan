#!/usr/local/bin/python2.7
#coding:utf-8

import logging

from flask import url_for, request, redirect, g

from utils import code
from utils.helper import MethodView
from utils.token import create_token
from utils.account import login_required
from utils.organization import member_required

from query.gists import create_gist

logger = logging.getLogger(__name__)

class Create(MethodView):
    decorators = [member_required(admin=False), login_required('account.login')]
    def get(self, organization, member):
        return self.render_template(
                    organization=organization, \
                    member=member, \
                )

    def post(self, organization, member):
        summary = request.form.get('summary')
        filenames = request.form.getlist('filename')
        codes = request.form.getlist('code')
        private = create_token(20) if request.form.get('private') else None
        length = len(filenames)
        data = {}
        for i in xrange(0, length):
            filename = filenames[i]
            if not filename:
                return self.render_template(
                            organization=organization, \
                            member=member, \
                            error=code.GIST_WITHOUT_FILENAME, \
                            filenames=filenames, \
                            codes=codes, \
                        )
            if data.get(filename):
                return self.render_template(
                            organization=organization, \
                            member=member, \
                            error=code.GIST_FILENAME_EXISTS, \
                            filenames=filenames, \
                            codes=codes, \
                        )
            data[filename] = codes[i]
        gist, err = create_gist(organization, g.current_user, summary, private=private)
        if err:
            return self.render_template(
                        organization=organization, \
                        member=member, \
                        error=code.GIST_WITHOUT_FILENAME, \
                        filenames=filenames, \
                        codes=codes, \
                    )
        return redirect(url_for('gists.view', git=organization.git, gid=gist.id))

class View(MethodView):
    decorators = [member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, gid):
        return 'Hello World'

