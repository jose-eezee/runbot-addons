# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2010-2015 Eezee-It (<http://www.eezee-it.com>).
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
import logging
from openerp import http
from openerp.http import request
from openerp import SUPERUSER_ID
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


class WebHookListener(http.Controller):

    @http.route('/webhook/receive_signal', type='json', auth="none")
    def receive_signal(self, req):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        json_dict = req.jsonrequest
        print json_dict
        _logger.debug("Create new PR from %s", json_dict['pullrequest']['source']['branch']['name'])
        _logger.debug("In repository %s", json_dict['pullrequest']['source']['repository']['full_name'])
        _logger.debug("For commit %s", json_dict['pullrequest']['source']['commit']['hash'])
        _logger.debug("git@bitbucket.org:%s.git", json_dict['pullrequest']['source']['repository']['full_name'])
        resp = request.env['runbot.repo'].sudo().search([('name', '=', 'git@bitbucket.org:%s.git' % json_dict['pullrequest']['source']['repository']['full_name'])])
        print resp
        context.update({'prbranch':json_dict['pullrequest']['source']['branch']['name']})
        pool.get('runbot.repo').cron(cr, SUPERUSER_ID, [resp.id], context=context)
        return {}
