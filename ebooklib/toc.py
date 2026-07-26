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

"""Table of contents and navigation elements."""


class Section:
    def __init__(self, title: str, href: str = "") -> None:
        self.title = title
        self.href = href

    def __repr__(self) -> str:
        return f"<Section:{self.title}:{self.href}>"


class Link:
    def __init__(self, href: str, title: str, uid: str | None = None) -> None:
        self.href = href
        self.title = title
        self.uid = uid

    def __repr__(self) -> str:
        return f"<Link:{self.uid}:{self.href}>"
