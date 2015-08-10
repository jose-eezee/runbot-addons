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
import requests
import re
import os
import urlparse

from openerp import models, api, fields

import logging

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


def bitbucket(func):
    """Decorator for functions which should be overwritten only if
    this repo is bitbucket-.
    """
    def bitbucket(self, *args, **kwargs):
        if self.repo_id.hosting == 'bitbucket':
            return func(self, *args, **kwargs)
        else:
            regular_func = getattr(super(RunbotBranch, self), func.func_name)
            return regular_func(*args, **kwargs)
    return bitbucket


class RunbotBranch(models.Model):
    _inherit = "runbot.branch"

    @api.bitbucket
    @api.multi
    def _get_pull_info(self):
        self.ensure_one()
        repo = self.repo_id
        if repo.username and repo.password and self.name.startswith('refs/pull/'):
            pull_number = self.name[len('refs/pull/'):]
            return repo.get_pull_request(pull_number) or {}
        return {}

    @api.one
    def get_pull_request_url(self, owner, repository, branch):
        raise NotImplementedError("Should have implemented this")

    @api.one
    def get_branch_url(self, owner, repository, pull_number):
        raise NotImplementedError("Should have implemented this")