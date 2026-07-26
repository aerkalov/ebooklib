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

from typing import cast

from ebooklib.plugins.base import BasePlugin
from ebooklib.utils import parse_html_string


class BooktypeLinks(BasePlugin):
    NAME = "Booktype Links"

    def __init__(self, booktype_book):
        self.booktype_book = booktype_book

    def html_before_write(self, book, chapter):
        from urllib.parse import urljoin, urlparse

        from lxml import etree

        try:
            tree = parse_html_string(chapter.content)
        except Exception:
            return

        body = tree.find("body")

        if body is not None and len(body) != 0:
            # should also be aware to handle
            # ../chapter/
            # ../chapter/#reference
            # ../chapter#reference

            for _link in cast("list[etree._Element]", body.xpath("//a")):
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
                        _link.set("href", f"{_u.path}.xhtml")

                    if _u.fragment != "":
                        _link.set("href", urljoin(_link.get("href") or "", f"#{_u.fragment}"))

                    _name = _link.get("name")
                    if _name is not None:
                        _link.set("id", _name)
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

        body = tree.find("body")

        if body is not None and len(body) != 0:
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
            for footnote in cast("list[etree._Element]", body.xpath('//span[@class="InsertNoteMarker"]')):
                footnote_id = (footnote.get("id") or "")[:-8]
                a = footnote[0][0]

                footnote_text = cast("list[etree._Element]", body.xpath(f'//li[@id="{footnote_id}"]'))[0]

                a.attrib[f"{{{epub.NAMESPACES['EPUB']}}}type"] = "noteref"
                ftn = etree.SubElement(body, "aside", {"id": footnote_id})
                ftn.attrib["{{{epub.NAMESPACES['EPUB']}}}type"] = "footnote"
                ftn_p = etree.SubElement(ftn, "p")
                ftn_p.text = footnote_text.text

            old_footnote = cast("list[etree._Element]", body.xpath('//ol[@id="InsertNote_NoteList"]'))
            if len(old_footnote) > 0:
                body.remove(old_footnote[0])

        chapter.content = etree.tostring(tree, pretty_print=True, encoding="utf-8")
