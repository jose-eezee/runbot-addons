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


def is_pull_request(branch):
    return re.match('^\d+$', branch) is not None


class RunbotBranch(models.Model):
    _inherit = "runbot.branch"

    @api.multi
    def _get_branch_url(self, field_name, arg):
        r = {}

        for branch in self:
            owner, repository = branch.repo_id.base.split('/')[1:]

            if is_pull_request(branch.branch_name):
                # The API one return
                r[branch.id] = branch.get_pull_request_url(owner, repository, branch.branch_name)
            else:
                r[branch.id] = branch.get_branch_url(owner, repository, branch.branch_name)

        return r

    @api.multi
    def _get_pull_info(self):
        raise NotImplementedError("Should have implemented this")

    @api.multi
    def get_pull_request_url(self, owner, repository, branch):
        raise NotImplementedError("Should have implemented this")

    @api.multi
    def get_branch_url(self, owner, repository, pull_number):
        raise NotImplementedError("Should have implemented this")