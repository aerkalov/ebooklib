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

"""
Backwards compatible public API for EbookLib.

Historically all of EbookLib lived in this module. The implementation has
been split into smaller modules (:mod:`ebooklib.book`, :mod:`ebooklib.items`,
:mod:`ebooklib.reader`, :mod:`ebooklib.writer`, :mod:`ebooklib.toc`,
:mod:`ebooklib.consts` and :mod:`ebooklib.exceptions`) but everything is
still importable from ``ebooklib.epub`` and will remain so until a future
major release.
"""

from ebooklib.book import EpubBook
from ebooklib.consts import (
    CHAPTER_XML,
    CONTAINER_PATH,
    CONTAINER_XML,
    COVER_XML,
    IMAGE_MEDIA_TYPES,
    NAMESPACES,
    NAV_XML,
    NCX_XML,
    VERSION,
)
from ebooklib.exceptions import EpubException
from ebooklib.items import (
    EpubCover,
    EpubCoverHtml,
    EpubHtml,
    EpubImage,
    EpubItem,
    EpubNav,
    EpubNcx,
    EpubSMIL,
)
from ebooklib.reader import EpubReader, read_epub
from ebooklib.toc import Link, Section
from ebooklib.writer import EpubWriter, write_epub

__all__ = [
    # consts
    "VERSION",
    "NAMESPACES",
    "CONTAINER_PATH",
    "CONTAINER_XML",
    "NCX_XML",
    "NAV_XML",
    "CHAPTER_XML",
    "COVER_XML",
    "IMAGE_MEDIA_TYPES",
    # toc
    "Section",
    "Link",
    # exceptions
    "EpubException",
    # items
    "EpubItem",
    "EpubNcx",
    "EpubCover",
    "EpubHtml",
    "EpubCoverHtml",
    "EpubNav",
    "EpubImage",
    "EpubSMIL",
    # book
    "EpubBook",
    # writer / reader
    "EpubWriter",
    "write_epub",
    "EpubReader",
    "read_epub",
]
