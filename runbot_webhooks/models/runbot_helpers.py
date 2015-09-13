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

import fcntl
import itertools
import os
import re
import signal
import socket
import time
from collections import OrderedDict
import logging
import openerp

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)

#----------------------------------------------------------
# RunBot helpers
#----------------------------------------------------------

def log(*l, **kw):
    out = [i if isinstance(i, basestring) else repr(i) for i in l] + \
          ["%s=%r" % (k, v) for k, v in kw.items()]
    _logger.debug(' '.join(out))

def dashes(string):
    """Sanitize the input string"""
    for i in '~":\'':
        string = string.replace(i, "")
    for i in '/_. ':
        string = string.replace(i, "-")
    return string

def mkdirs(dirs):
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d)

def grep(filename, string):
    if os.path.isfile(filename):
        return open(filename).read().find(string) != -1
    return False

def rfind(filename, pattern):
    """Determine in something in filename matches the pattern"""
    if os.path.isfile(filename):
        regexp = re.compile(pattern, re.M)
        with open(filename, 'r') as f:
            if regexp.findall(f.read()):
                return True
    return False

def lock(filename):
    fd = os.open(filename, os.O_CREAT | os.O_RDWR, 0600)
    fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

def locked(filename):
    result = False
    try:
        fd = os.open(filename, os.O_CREAT | os.O_RDWR, 0600)
        try:
            fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            result = True
        os.close(fd)
    except OSError:
        result = False
    return result

def nowait():
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)

def run(l, env=None):
    """Run a command described by l in environment env"""
    log("run", l)
    env = dict(os.environ, **env) if env else None
    if isinstance(l, list):
        if env:
            rc = os.spawnvpe(os.P_WAIT, l[0], l, env)
        else:
            rc = os.spawnvp(os.P_WAIT, l[0], l)
    elif isinstance(l, str):
        tmp = ['sh', '-c', l]
        if env:
            rc = os.spawnvpe(os.P_WAIT, tmp[0], tmp, env)
        else:
            rc = os.spawnvp(os.P_WAIT, tmp[0], tmp)
    log("run", rc=rc)
    return rc

def now():
    return time.strftime(openerp.tools.DEFAULT_SERVER_DATETIME_FORMAT)

def dt2time(datetime):
    """Convert datetime to time"""
    return time.mktime(time.strptime(datetime, openerp.tools.DEFAULT_SERVER_DATETIME_FORMAT))

def s2human(time):
    """Convert a time in second into an human readable string"""
    for delay, desc in [(86400,'d'),(3600,'h'),(60,'m')]:
        if time >= delay:
            return str(int(time / delay)) + desc
    return str(int(time)) + "s"

def flatten(list_of_lists):
    return list(itertools.chain.from_iterable(list_of_lists))

def decode_utf(field):
    try:
        return field.decode('utf-8')
    except UnicodeDecodeError:
        return ''

def uniq_list(l):
    return OrderedDict.fromkeys(l).keys()

def fqdn():
    return socket.getfqdn()