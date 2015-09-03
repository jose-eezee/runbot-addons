import datetime
import fcntl
import glob
import hashlib
import itertools
import logging
import operator
import os
import re
import resource
import shutil
import signal
import simplejson
import socket
import subprocess
import sys
import time
from collections import OrderedDict
import dateutil.parser
import logging


from openerp.models import Model
from openerp.api import api
from openerp.fields import Char



_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


class RunbotRepo(Model):
    _inherit = "runbot.repo"

    stickies = Char(string="Stickies")


    # Overwrite function in file: /runbot/runbot.py#L260
    # Only load the repositories in the stickies field.
    def update_git(self, cr, uid, repo, context=None):
        _logger.debug('repo %s updating branches', repo.name)

        Build = self.pool['runbot.build']
        Branch = self.pool['runbot.branch']

        if not os.path.isdir(os.path.join(repo.path)):
            os.makedirs(repo.path)
        if not os.path.isdir(os.path.join(repo.path, 'refs')):
            run(['git', 'clone', '--bare', repo.name, repo.path])
        else:
            repo.git(['gc', '--auto', '--prune=all'])
            repo.git(['fetch', '-p', 'origin', '+refs/heads/*:refs/heads/*'])
            repo.git(['fetch', '-p', 'origin', '+refs/pull/*/head:refs/pull/*'])

        fields = ['refname','objectname','committerdate:iso8601','authorname','authoremail','subject','committername','committeremail']
        fmt = "%00".join(["%("+field+")" for field in fields])
        git_refs = repo.git(['for-each-ref', '--format', fmt, '--sort=-committerdate', 'refs/heads', 'refs/pull'])
        git_refs = git_refs.strip()

        refs = [[decode_utf(field) for field in line.split('\x00')] for line in git_refs.split('\n')]

        for name, sha, date, author, author_email, subject, committer, committer_email in refs:
            # create or get branch
            branch_ids = Branch.search(cr, uid, [('repo_id', '=', repo.id), ('name', '=', name)])
            if branch_ids:
                branch_id = branch_ids[0]
            else:
                _logger.debug('repo %s found new branch %s', repo.name, name)
                if name in eval(repo.stikies):
                    branch_id = Branch.create(cr, uid, {'repo_id': repo.id, 'name': name})
                    branch = Branch.browse(cr, uid, [branch_id], context=context)[0]
            # skip build for old branches
            if dateutil.parser.parse(date[:19]) + datetime.timedelta(30) < datetime.datetime.now():
                continue
            # create build (and mark previous builds as skipped) if not found
            build_ids = Build.search(cr, uid, [('branch_id', '=', branch.id), ('name', '=', sha)])
            if not build_ids:
                _logger.debug('repo %s branch %s new build found revno %s', branch.repo_id.name, branch.name, sha)
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