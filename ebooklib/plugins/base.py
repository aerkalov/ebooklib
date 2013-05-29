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


class BasePlugin(object):
    def before_write(self, book):
        "Processing before save"
        return True

    def after_write(self, book):
        "Processing after save"
        return True

    def before_read(self, book):
        "Processing before save"
        return True

    def after_read(self, book):
        "Processing after save"
        return True

    def item_after_read(self, book, item):
        "Process general item after read."
        return True

    def item_before_write(self, book, item):
        "Process general item before write."
        return True

    def html_after_read(self, book, chapter):
        "Processing HTML before read."
        return True

    def html_before_write(self, book, chapter):
        "Processing HTML before save."
        return True
