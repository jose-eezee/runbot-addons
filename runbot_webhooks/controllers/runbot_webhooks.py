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

import logging
from openerp import http
from openerp.http import request
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


class WebHookListener(http.Controller):

    @http.route('/webhook/receive_signal', type='json', auth="none")
    def receive_signal(self, req):
        '''This function receive the webhook signal form bitbucket and
        create the necessaries variables for search and run the cron.
        :param req: The jsonrequest from bitbucket webhook.
        :return: a empty dict
        '''

        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        #Get the jsonsignal
        json_dict = req.jsonrequest
        #Pull request's branch
        branch = json_dict['pullrequest']['source']['branch']['name']
        #Pull request's repository
        repository = json_dict['pullrequest']['source']['repository']['full_name']
        #Pull request's commmit
        commit = json_dict['pullrequest']['source']['commit']['hash']
        #Information log
        _logger.info("Create new PR from %s", branch)
        _logger.info("In repository %s", repository)
        _logger.info("For commit %s", commit)
        _logger.info("git@bitbucket.org:%s.git", repository)

        domain = [('name', '=', 'git@bitbucket.org:%s.git' % repository)]
        resp = request.env['runbot.repo'].sudo().search(domain)
        #Context variable used by the cron for create the branch and build the new instance
        context.update({'pr_branch': branch})
        #Running the cron
        pool.get('runbot.repo').cron(cr, SUPERUSER_ID, [resp.id], context=context)

        return {}
