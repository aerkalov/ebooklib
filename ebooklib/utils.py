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

import io
import mimetypes
import os

from lxml import etree

mimetype_initialised = False


def debug(obj: object) -> None:
    import pprint

    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(obj)


def parse_string(s: str | bytes) -> etree._ElementTree:
    parser = etree.XMLParser(recover=True, resolve_entities=False)
    if isinstance(s, str):
        tree = etree.parse(io.BytesIO(s.encode("utf-8")), parser=parser)
    else:
        tree = etree.parse(io.BytesIO(s), parser=parser)

    return tree


def parse_html_string(s: str | bytes):
    from lxml import html

    utf8_parser = html.HTMLParser(encoding="utf-8")

    html_tree = html.document_fromstring(s, parser=utf8_parser)

    return html_tree


def guess_type(extenstion: str) -> tuple[str | None, str | None]:
    global mimetype_initialised

    if not mimetype_initialised:
        mimetypes.init()
        mimetypes.add_type("application/xhtml+xml", ".xhtml")
        mimetype_initialised = True

    return mimetypes.guess_type(extenstion)


def create_pagebreak(pageref: str, label: str | None = None, html: bool = True) -> etree._Element | str:
    from ebooklib.consts import NAMESPACES

    pageref_attributes = {
        f"{{{NAMESPACES['EPUB']}}}type": "pagebreak",
        "title": pageref,
        "id": pageref,
    }

    pageref_elem = etree.Element("span", pageref_attributes, nsmap={"epub": NAMESPACES["EPUB"]})

    if label:
        pageref_elem.text = label

    if html:
        return etree.tostring(pageref_elem, encoding="unicode")

    return pageref_elem


def get_headers(elem) -> str | None:
    for n in range(1, 7):
        headers = elem.xpath(f"./h{n}")

        if len(headers) > 0:
            text = headers[0].text_content().strip()
            if len(text) > 0:
                return text
    return None


def get_pages(item) -> list[tuple[str, str, str]]:
    body = parse_html_string(item.get_body_content())
    pages = []

    for elem in body.iter():
        if "epub:type" in elem.attrib:
            if elem.get("id") is not None:
                _text = None

                if elem.text is not None and elem.text.strip() != "":
                    _text = elem.text.strip()

                if _text is None:
                    _text = elem.get("aria-label")

                if _text is None:
                    _text = get_headers(elem)

                pages.append((item.get_name(), elem.get("id"), _text or elem.get("id")))

    return pages


def get_pages_for_items(items) -> list[tuple[str, str, str]]:
    pages_from_docs = [get_pages(item) for item in items]

    return [item for pages in pages_from_docs for item in pages]


class Directory:
    """Reads files from an unpacked EPUB directory, using the same interface as ZipFile."""

    def __init__(self, directory_path: str | os.PathLike) -> None:
        self.directory_path = directory_path

    def read(self, subname: str) -> bytes:
        # Guard against path traversal (e.g. "../../secret") escaping the EPUB directory.
        base_path = os.path.realpath(self.directory_path)
        full_path = os.path.realpath(os.path.join(base_path, subname))

        if os.path.commonpath([base_path, full_path]) != base_path:
            raise KeyError(f"There is no item named {subname!r} in the directory")

        with open(full_path, "rb") as fp:
            return fp.read()

    def close(self) -> None:
        pass
