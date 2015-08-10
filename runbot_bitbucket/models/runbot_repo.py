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


def bitbucket(func):
    """Decorator for functions which should be overwritten only if
    this repo is bitbucket-.
    """
    def bitbucket(self, *args, **kwargs):
        if self.hosting == 'bitbucket':
            return func(self, *args, **kwargs)
        else:
            regular_func = getattr(super(RunbotRepo, self), func.func_name)
            return regular_func(*args, **kwargs)
    return bitbucket


class RunbotRepo(models.Model):
    _inherit = "runbot.repo"

    @api.model
    def _get_hosting(self):
        result = super(RunbotRepo, self)._get_hosting()

        result.append(('bitbucket', 'Bitbucket'))

    @bitbucket
    def get_pull_request(self, pull_number):
        match = re.search('([^/]+)/([^/]+)/([^/.]+(.git)?)', self.base)

        if match:
            owner = match.group(2)
            repository = match.group(3)

            hosting = BitBucketHosting((self.username, self.password))

            return hosting.get_pull_request(owner, repository, pull_number)


    @bitbucket
    @api.one
    def get_hosting_instance(self):
        return BitBucketHosting
