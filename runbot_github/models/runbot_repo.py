# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    This module copyright (C) 2010 - 2014 Savoir-faire Linux
#    (<http://www.savoirfairelinux.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import re

from openerp import models, api

from openerp.addons.runbot_multiple_hosting import runbot_repo

import logging

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


class GithubHosting(runbot_repo.Hosting):
    API_URL = 'https://api.github.com'
    URL = 'https://github.com'

    def __init__(self, credentials):
        token = (credentials, 'x-oauth-basic')
        super(GithubHosting, self).__init__(token)

        self.session.headers.update({'Accept': 'application/vnd.github.she-hulk-preview+json'})

    def get_pull_request(self, owner, repository, pull_number):
        url = self.get_api_url('/repos/%s/%s/pulls/%s' % (owner, repository, pull_number))
        response = self.session.get(url)
        return response.json()

    def get_pull_request_branch(self, owner, repository, pull_number):
        pr = self.get_pull_request(owner, repository, pull_number)
        return pr['base']['ref']

    def update_status_on_commit(self, owner, repository, commit_hash, status):
        url = self.get_api_url('/repos/%s/%s/statuses/%s' % (owner, repository, commit_hash))
        self.session.post(url, status)

    @classmethod
    def get_branch_url(cls, owner, repository, branch):
        return cls.get_url('/%s/%s/tree/%s', owner, repository, branch)

    @classmethod
    def get_pull_request_url(cls, owner, repository, pull_number):
        return cls.get_url('/%s/%s/pull/%s', owner, repository, pull_number)


class RunbotRepo(models.Model):
    _inherit = "runbot.repo"

    @api.model
    def _get_hosting(self):
        result = super(RunbotRepo, self)._get_hosting()

        result.append(('github', 'GitHub'))

    @api.multi
    def get_pull_request_branch(self, pull_number):
        for repo in self:
            match = re.search('([^/]+)/([^/]+)/([^/.]+(.git)?)', repo.base)

            if match:
                owner = match.group(2)
                repository = match.group(3)

                if repo.hosting == 'bitbucket':
                    hosting = GithubHosting((repo.username, repo.password))
                else:
                    return super(RunbotRepo, self).get_pull_request_branch(pull_number)

                return hosting.get_pull_request_branch(owner, repository, pull_number)

    @api.mutli
    def update_status_on_commit(self, commit_hash, status):
        for repo in self:

            match = re.search('([^/]+)/([^/]+)/([^/.]+(.git)?)', repo.base)

            if not match:
                return

            owner = match.group(2)
            repository = match.group(3)

            if repo.hosting == 'github':
                hosting = GithubHosting(repo.token)
                return hosting.update_status_on_commit(owner, repository, commit_hash, status)
            else:
                return super(RunbotRepo, self).update_status_on_commit(commit_hash, status)