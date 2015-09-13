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

import datetime
import os
import dateutil.parser
import logging

# Importing helper functions
from .runbot_helpers import run
from .runbot_helpers import decode_utf

from openerp.models import Model, api
from openerp.fields import Char, Boolean

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)

class RunbotRepo(Model):
    _inherit = "runbot.repo"

    # Stickies field for specify the branch to download
    stickies = Char(string="Stickies", required=True, default='master',
        help="Comma-separated list of branch to pull.")
    auto = Boolean(string="Auto", default=True)

    # Overwrite function in file: /runbot/runbot.py#L256
    # Adds context variable propagation
    def update(self, cr, uid, ids, context=None):
        for repo in self.browse(cr, uid, ids, context=context):
            self.update_git(cr, uid, repo, context=context)

    # Overwrite function in file: /runbot/runbot.py#L260
    # Only load the repositories in the stickies field.
    def update_git(self, cr, uid, repo, context=None):
        '''
        This function update and create new branch and repositories
        :param cr: Database cursor
        :param uid: User ID
        :param repo: A browse record of runbot.repo
        :param context: Odoo context dictionary
        :return: Nothing
        '''
        _logger.info('repo %s updating branches', repo.name)

        Build = self.pool['runbot.build']
        Branch = self.pool['runbot.branch']

        #Creating a list object for the stickies values
        stickies_list = repo.stickies.split(',')

        #This variable arrive from the webhook
        #See file: /runbot/controllers/runbot_webhook.py#L61
        if context.get('pr_branch'):
            stickies_list.append(context['pr_branch'])

        #Format the list with the correct structure
        stickies_format_list = ['refs/heads/'+x for x in stickies_list]

        _logger.debug("Repo path %s", repo.path)

        if not os.path.isdir(os.path.join(repo.path)):
            os.makedirs(repo.path)
        if not os.path.isdir(os.path.join(repo.path, 'refs')):
            run(['git', 'clone', '--bare', repo.name, repo.path])
        else:
            repo.git(['gc', '--auto', '--prune=all'])

        #For each element in the stickies list do a fecht
        for x in stickies_list:
            repo.git(['fetch', '-p', 'origin', '+refs/heads/%s:refs/heads/%s' % (x, x)])
            repo.git(['fetch', '-p', 'origin', '+refs/pull/*/head:refs/pull/*'])

        fields = ['refname','objectname','committerdate:iso8601','authorname','authoremail','subject','committername','committeremail']
        fmt = "%00".join(["%("+field+")" for field in fields])
        git_refs = repo.git(['for-each-ref', '--format', fmt, '--sort=-committerdate', 'refs/heads', 'refs/pull'])
        git_refs = git_refs.strip()

        refs = [[decode_utf(field) for field in line.split('\x00')] for line in git_refs.split('\n')]

        for name, sha, date, author, author_email, subject, committer, committer_email in refs:
            # create or get branch
            branch_id = None
            branch_ids = Branch.search(cr, uid, [('repo_id', '=', repo.id), ('name', '=', name)])
            _logger.info("Branch Name: %s", name)
            _logger.info('Branch ids %s founds', branch_ids)
            if branch_ids:
                branch_id = branch_ids[0]
            else:
                _logger.info('repo %s found new branch %s', repo.name, name)
                if name in stickies_format_list:
                    _logger.info("Creating branch %s", name)
                    branch_id = Branch.create(cr, uid, {'repo_id': repo.id, 'name': name})
                    _logger.info("Branch %s created succefull", name)

            if branch_id is not None:
                branch = Branch.browse(cr, uid, [branch_id], context=context)[0]
                # skip build for old branches
                if dateutil.parser.parse(date[:19]) + datetime.timedelta(30) < datetime.datetime.now():
                    continue
                # create build (and mark previous builds as skipped) if not found
                build_ids = Build.search(cr, uid, [('branch_id', '=', branch.id), ('name', '=', sha)])

                # create the build if name exist into the stickies list
                if not build_ids and name in stickies_format_list:
                    _logger.info('repo %s branch %s new build found revno %s', branch.repo_id.name, branch.name, sha)
                    build_info = {
                        'branch_id': branch.id,
                        'name': sha,
                        'author': author,
                        'author_email': author_email,
                        'committer': committer,
                        'committer_email': committer_email,
                        'subject': subject,
                        'date': dateutil.parser.parse(date[:19]),
                    }

                    if not branch.sticky:
                        skipped_build_sequences = Build.search_read(cr, uid, [('branch_id', '=', branch.id), ('state', '=', 'pending')],
                                                                    fields=['sequence'], order='sequence asc', context=context)
                        if skipped_build_sequences:
                            to_be_skipped_ids = [build['id'] for build in skipped_build_sequences]
                            Build.skip(cr, uid, to_be_skipped_ids, context=context)
                            # new order keeps lowest skipped sequence
                            build_info['sequence'] = skipped_build_sequences[0]['sequence']
                    Build.create(cr, uid, build_info)

        # skip old builds (if their sequence number is too low, they will not ever be built)
        skippable_domain = [('repo_id', '=', repo.id), ('state', '=', 'pending')]
        icp = self.pool['ir.config_parameter']
        running_max = int(icp.get_param(cr, uid, 'runbot.running_max', default=75))
        to_be_skipped_ids = Build.search(cr, uid, skippable_domain, order='sequence desc', offset=running_max)
        Build.skip(cr, uid, to_be_skipped_ids)

    # Overwrite function in file: /runbot/runbot.py#L401
    # Adds context variable propagation
    def cron(self, cr, uid, ids=None, context=None):
        if ids is None:
            ids = self.search(cr, uid, [('auto', '=', True)], context=context)
        self.update(cr, uid, ids, context=context)
        self.scheduler(cr, uid, ids, context=context)
        self.reload_nginx(cr, uid, context=context)