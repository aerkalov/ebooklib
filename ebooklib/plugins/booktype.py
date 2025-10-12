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

from ebooklib.plugins.base import BasePlugin
from ebooklib.utils import parse_html_string


class BooktypeLinks(BasePlugin):
    NAME = "Booktype Links"

    def __init__(self, booktype_book):
        self.booktype_book = booktype_book

    def html_before_write(self, book, chapter):
        try:
            from urlparse import urljoin, urlparse
        except ImportError:
            from urllib.parse import urljoin, urlparse

        from lxml import etree

        try:
            tree = parse_html_string(chapter.content)
        except Exception:
            return

        root = tree.getroottree()

        if len(root.find("body")) != 0:
            body = tree.find("body")

            # should also be aware to handle
            # ../chapter/
            # ../chapter/#reference
            # ../chapter#reference

            for _link in body.xpath("//a"):
                # This is just temporary for the footnotes
                if _link.get("href", "").find("InsertNoteID") != -1:
                    _ln = _link.get("href", "")
                    i = _ln.find("#")
                    _link.set("href", _ln[i:])

                    continue

                _u = urlparse(_link.get("href", ""))

                # Let us care only for internal links at the moment
                if _u.scheme == "":
                    if _u.path != "":
                        _link.set("href", "{path}.xhtml".format(path=_u.path))  # noqa: UP032

                    if _u.fragment != "":
                        _link.set("href", urljoin(_link.get("href"), "#{fragment}".format(fragment=_u.fragment)))  # noqa: UP032

                    if _link.get("name") is not None:
                        _link.set("id", _link.get("name"))
                        etree.strip_attributes(_link, "name")

        chapter.content = etree.tostring(tree, pretty_print=True, encoding="utf-8")


class BooktypeFootnotes(BasePlugin):
    NAME = "Booktype Footnotes"

    def __init__(self, booktype_book):
        self.booktype_book = booktype_book

    def html_before_write(self, book, chapter):
        from lxml import etree

        from ebooklib import epub

        try:
            tree = parse_html_string(chapter.content)
        except Exception:
            return

        root = tree.getroottree()

        if len(root.find("body")) != 0:
            body = tree.find("body")

            # <span id="InsertNoteID_1_marker1" class="InsertNoteMarker">
            #   <sup><a href="#InsertNoteID_1">1</a></sup>
            # <span>

            # <ol id="InsertNote_NoteList">
            #   <li id="InsertNoteID_1">prvi footnote
            #     <span id="InsertNoteID_1_LinkBacks">
            #       <sup><a href="#InsertNoteID_1_marker1">^</a></sup>
            #     </span>
            #   </li>
            # </ol>

            # <a epub:type="noteref" href="#n1">1</a></p>
            # <aside epub:type="footnote" id="n1"><p>These have been corrected in this EPUB3 edition.</p></aside>
            for footnote in body.xpath('//span[@class="InsertNoteMarker"]'):
                footnote_id = footnote.get("id")[:-8]
                a = footnote.getchildren()[0].getchildren()[0]

                footnote_text = body.xpath('//li[@id="{footnote_id}"]'.format(footnote_id=footnote_id))[0]  # noqa: UP032

                a.attrib["{%s}type" % epub.NAMESPACES["EPUB"]] = "noteref"  # noqa
                ftn = etree.SubElement(body, "aside", {"id": footnote_id})
                ftn.attrib["{%s}type" % epub.NAMESPACES["EPUB"]] = "footnote"  # noqa
                ftn_p = etree.SubElement(ftn, "p")
                ftn_p.text = footnote_text.text

            old_footnote = body.xpath('//ol[@id="InsertNote_NoteList"]')
            if len(old_footnote) > 0:
                body.remove(old_footnote[0])

        chapter.content = etree.tostring(tree, pretty_print=True, encoding="utf-8")
