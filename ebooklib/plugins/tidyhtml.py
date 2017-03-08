# This file is part of EbookLib.
# Copyright (c) 2013 Aleksandar Erkalovic <aerkalov@gmail.com>
#
# EbookLib is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# EbookLib is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with EbookLib.  If not, see <http://www.gnu.org/licenses/>.

import six
import subprocess

from ebooklib.plugins.base import BasePlugin
from ebooklib.utils import parse_html_string

# Recommend usage of
# - https://github.com/w3c/tidy-html5

def tidy_cleanup(content, **extra):
    cmd = []

    for k, v in six.iteritems(extra):

        if v:
            cmd.append('--%s' % k)
            cmd.append(v)
        else:
            cmd.append('-%s' % k)

    # must parse all other extra arguments
    try:
        p = subprocess.Popen(['tidy']+cmd, shell=False, 
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE, close_fds=True)
    except OSError:
        return (3, None)

    p.stdin.write(content)

    (cont, p_err) = p.communicate()

    # 0 - all ok
    # 1 - there were warnings
    # 2 - there were errors
    # 3 - exception

    return (p.returncode, cont)


class TidyPlugin(BasePlugin):
    NAME = 'Tidy HTML'
    OPTIONS = {'char-encoding': 'utf8',
               'tidy-mark': 'no'
              }

    def __init__(self, extra = {}):
        self.options = dict(self.OPTIONS)
        self.options.update(extra)

    def html_before_write(self, book, chapter):
        if not chapter.content:
            return None

        (_, chapter.content) = tidy_cleanup(chapter.content, **self.options)

        return chapter.content

    def html_after_read(self, book, chapter):
        if not chapter.content:
            return None

        (_, chapter.content) = tidy_cleanup(chapter.content, **self.options)

        return chapter.content

