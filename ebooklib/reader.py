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

"""EpubReader - loads an EPUB file into an EpubBook."""

import os
import posixpath as zip_path
import warnings
import zipfile
from typing import Any, cast
from urllib.parse import unquote

from lxml import etree

from ebooklib.book import EpubBook
from ebooklib.consts import IMAGE_MEDIA_TYPES, NAMESPACES
from ebooklib.exceptions import EpubException
from ebooklib.items import EpubCover, EpubCoverHtml, EpubHtml, EpubImage, EpubItem, EpubNav, EpubNcx, EpubSMIL
from ebooklib.toc import Link, Section
from ebooklib.utils import Directory, parse_html_string, parse_string


class EpubReader:
    DEFAULT_OPTIONS: dict[str, Any] = {"ignore_ncx": True}

    def __init__(self, epub_file_name, options: dict[str, Any] | None = None) -> None:
        self.file_name = epub_file_name
        self.book = EpubBook()
        self.zf: zipfile.ZipFile | Directory | None = None

        self.opf_file = ""
        self.opf_dir = ""

        self.options = dict(self.DEFAULT_OPTIONS)
        if options:
            self.options.update(options)

        self._check_deprecated()

    def _check_deprecated(self) -> None:
        if self.options.get("ignore_ncx") is None:
            warnings.warn("In the future version we will turn default option ignore_ncx to True.", stacklevel=2)

    def process(self) -> None:
        # should cache this html parsing so we don't do it for every plugin
        for plg in self.options.get("plugins", []):
            if hasattr(plg, "after_read"):
                plg.after_read(self.book)

        for item in self.book.get_items():
            if isinstance(item, EpubHtml):
                for plg in self.options.get("plugins", []):
                    if hasattr(plg, "html_after_read"):
                        plg.html_after_read(self.book, item)

    def load(self) -> EpubBook:
        self._load()

        return self.book

    def read_file(self, name: str) -> bytes:
        # Raises KeyError
        if self.zf is None:
            raise EpubException(-1, "EPUB file is not opened")

        name = zip_path.normpath(name)
        return self.zf.read(name)

    def _load_container(self) -> None:
        meta_inf = self.read_file("META-INF/container.xml")
        tree = parse_string(meta_inf)

        for root_file in tree.findall(
            ".//xmlns:rootfile[@media-type]", namespaces={"xmlns": NAMESPACES["CONTAINERNS"]}
        ):
            if root_file.get("media-type") == "application/oebps-package+xml":
                self.opf_file = root_file.get("full-path") or ""
                self.opf_dir = zip_path.dirname(self.opf_file)

    def _load_metadata(self) -> None:
        container_root = self.container.getroot()

        # get epub version
        self.book.version = container_root.get("version", None)

        # get unique-identifier
        unique_identifier = container_root.get("unique-identifier", None)
        if unique_identifier:
            self.book.IDENTIFIER_ID = unique_identifier

        # get xml:lang
        # get metadata
        metadata = self.container.find(f"{{{NAMESPACES['OPF']}}}metadata")
        if metadata is None:
            raise EpubException(-1, "Can not find metadata element")

        nsmap = metadata.nsmap
        default_ns = nsmap.get(None, "")

        nsdict: dict[str | None, dict[str, list[Any]]] = {v: {} for v in nsmap.values()}

        def add_item(ns, tag, value, extra):
            if ns not in nsdict:
                nsdict[ns] = {}

            values = nsdict[ns].setdefault(tag, [])
            values.append((value, extra))

        for t in metadata:
            if not etree.iselement(t) or t.tag is etree.Comment:
                continue
            if t.tag == default_ns + "meta":
                name = t.get("name")
                others = dict(t.items())

                if name and ":" in name:
                    prefix, name = name.split(":", 1)
                else:
                    prefix = None

                add_item(t.nsmap.get(prefix, prefix), name, t.text, others)
            else:
                tag = t.tag[t.tag.rfind("}") + 1 :]

                if (t.prefix and t.prefix.lower() == "dc") and tag == "identifier":
                    _id = t.get("id", None)

                    if _id:
                        self.book.IDENTIFIER_ID = _id

                others = dict(t.items())
                add_item(t.nsmap[t.prefix], tag, t.text, others)

        self.book.metadata = nsdict

        titles = self.book.get_metadata("DC", "title")
        if len(titles) > 0:
            self.book.title = titles[0][0]

        for value, others in self.book.get_metadata("DC", "identifier"):
            if others.get("id") == self.book.IDENTIFIER_ID:
                self.book.uid = value

    def _load_manifest(self) -> None:
        manifest = self.container.find(f"{{{NAMESPACES['OPF']}}}manifest")
        if manifest is None:
            raise EpubException(-1, "Can not find manifest element")

        for r in manifest:
            if r is not None and r.tag != f"{{{NAMESPACES['OPF']}}}item":
                continue

            uid = r.get("id")
            href = unquote(r.get("href") or "")
            media_type = r.get("media-type") or ""
            _properties = r.get("properties", "")

            if _properties:
                properties = _properties.split(" ")
            else:
                properties = []

            # people use wrong content types
            if media_type == "image/jpg":
                media_type = "image/jpeg"

            ei: EpubItem

            match media_type:
                case "application/x-dtbncx+xml":
                    ei = EpubNcx(uid=uid, file_name=href)

                    ei.content = self.read_file(zip_path.join(self.opf_dir, ei.file_name))
                case "application/smil+xml":
                    ei = EpubSMIL(uid=uid, file_name=href)

                    ei.content = self.read_file(zip_path.join(self.opf_dir, ei.file_name))
                case "application/xhtml+xml" if "nav" in properties:
                    ei = EpubNav(uid=uid, file_name=href)

                    ei.content = self.read_file(zip_path.join(self.opf_dir, ei.file_name))
                case "application/xhtml+xml" if "cover" in properties:
                    ei = EpubCoverHtml()

                    ei.content = self.read_file(zip_path.join(self.opf_dir, href))
                case "application/xhtml+xml":
                    ei = EpubHtml()

                    ei.id = uid
                    ei.file_name = href
                    ei.media_type = media_type
                    ei.media_overlay = r.get("media-overlay", None)
                    ei.media_duration = r.get("duration", None)
                    ei.content = self.read_file(zip_path.join(self.opf_dir, ei.get_name()))
                    ei.properties = properties
                case _ if media_type in IMAGE_MEDIA_TYPES and "cover-image" in properties:
                    ei = EpubCover(uid=uid, file_name=href)

                    ei.media_type = media_type
                    ei.content = self.read_file(zip_path.join(self.opf_dir, ei.get_name()))
                case _ if media_type in IMAGE_MEDIA_TYPES:
                    ei = EpubImage()

                    ei.id = uid
                    ei.file_name = href
                    ei.media_type = media_type
                    ei.content = self.read_file(zip_path.join(self.opf_dir, ei.get_name()))
                case _:
                    # different types
                    ei = EpubItem()

                    ei.id = uid
                    ei.file_name = href
                    ei.media_type = media_type

                    ei.content = self.read_file(zip_path.join(self.opf_dir, ei.get_name()))

            self.book.add_item(ei)

    def _parse_ncx(self, data: bytes) -> None:
        tree = parse_string(data)
        tree_root = tree.getroot()

        nav_map = tree_root.find(f"{{{NAMESPACES['DAISY']}}}navMap")

        def _get_children(elems, n, nid):
            label, content = "", ""
            children = []

            for a in elems:
                if a.tag == f"{{{NAMESPACES['DAISY']}}}navLabel":
                    label = a[0].text
                if a.tag == f"{{{NAMESPACES['DAISY']}}}content":
                    content = a.get("src", "")
                if a.tag == f"{{{NAMESPACES['DAISY']}}}navPoint":
                    children.append(_get_children(a, n + 1, a.get("id", "")))

            if len(children) > 0:
                if n == 0:
                    return children

                return (Section(label, href=content), children)
            else:
                return Link(content, label, nid)

        self.book.toc = _get_children(nav_map, 0, "")

    def _parse_nav(self, data: str | bytes, base_path: str, navtype: str = "toc") -> None:
        html_node = parse_html_string(data)
        if navtype == "toc":
            # parsing the table of contents
            nav_node = cast("list[etree._Element]", html_node.xpath("//nav[@*='toc']"))[0]
        else:
            # parsing the list of pages
            _page_list = cast("list[etree._Element]", html_node.xpath("//nav[@*='page-list']"))
            if len(_page_list) == 0:
                return
            nav_node = _page_list[0]

        def parse_list(list_node):
            items = []

            for item_node in list_node.findall("li"):
                sublist_node = item_node.find("ol")
                link_node = item_node.find("a")

                if sublist_node is not None:
                    title = item_node[0].text_content()
                    children = parse_list(sublist_node)

                    if link_node is not None and link_node.get("href"):
                        href = zip_path.normpath(zip_path.join(base_path, link_node.get("href")))
                        items.append((Section(title, href=href), children))
                    else:
                        items.append((Section(title), children))
                elif link_node is not None and link_node.get("href"):
                    title = link_node.text_content()
                    href = zip_path.normpath(zip_path.join(base_path, link_node.get("href")))

                    items.append(Link(href, title))

            return items

        if navtype == "toc":
            self.book.toc = parse_list(nav_node.find("ol"))
        elif nav_node is not None:
            # generate the pages list if there is one
            self.book.pages = parse_list(nav_node.find("ol"))

            # generate the per-file pages lists
            # because of the order of parsing the files, this can't be done
            # when building the EpubHtml objects
            htmlfiles = {}
            for htmlfile in self.book.items:
                if isinstance(htmlfile, EpubHtml):
                    htmlfiles[htmlfile.file_name] = htmlfile
            for page in self.book.pages:
                try:
                    (filename, idref) = page.href.split("#")
                except ValueError:
                    filename = page.href
                if filename in htmlfiles:
                    htmlfiles[filename].pages.append(page)

    def _load_spine(self) -> None:
        spine = self.container.find(f"{{{NAMESPACES['OPF']}}}spine")
        if spine is None:
            raise EpubException(-1, "Can not find spine element")

        self.book.spine = [(t.get("idref"), t.get("linear", "yes")) for t in spine]

        toc = spine.get("toc", "")
        self.book.set_direction(spine.get("page-progression-direction", None))

        # should read ncx or nav file
        nav_item = next((item for item in self.book.items if isinstance(item, EpubNav)), None)
        if toc:
            if not self.options.get("ignore_ncx") or not nav_item:
                ncx_item = self.book.get_item_with_id(toc)

                if ncx_item is None:
                    raise EpubException(-1, "Can not find ncx file.")

                try:
                    ncxFile = self.read_file(zip_path.join(self.opf_dir, ncx_item.get_name()))
                except KeyError:
                    raise EpubException(-1, "Can not find ncx file.") from None

                self._parse_ncx(ncxFile)

    def _load_guide(self) -> None:
        guide = self.container.find(f"{{{NAMESPACES['OPF']}}}guide")
        if guide is not None:
            self.book.guide = [{"href": t.get("href"), "title": t.get("title"), "type": t.get("type")} for t in guide]

    def _load_opf_file(self) -> None:
        try:
            s = self.read_file(self.opf_file)
        except KeyError:
            raise EpubException(-1, "Can not find container file") from None

        self.container = parse_string(s)

        self._load_metadata()
        self._load_manifest()
        self._load_spine()
        self._load_guide()

        # read nav file if found
        nav_item = next((item for item in self.book.items if isinstance(item, EpubNav)), None)
        if nav_item:
            if self.options.get("ignore_ncx") or not self.book.toc:
                self._parse_nav(nav_item.content, zip_path.dirname(nav_item.file_name), navtype="toc")
            self._parse_nav(nav_item.content, zip_path.dirname(nav_item.file_name), navtype="pages")

    def _load(self) -> None:
        self.zf = None

        file_name = self.file_name
        if isinstance(file_name, bytes):
            # bytes filesystem paths are decoded so both branches below get str
            file_name = os.fsdecode(file_name)

        if isinstance(file_name, str | os.PathLike):
            if os.path.isdir(file_name):
                self.zf = Directory(file_name)

        if self.zf is None:
            try:
                self.zf = zipfile.ZipFile(file_name, "r", compression=zipfile.ZIP_DEFLATED, allowZip64=True)
            except zipfile.BadZipfile:
                raise EpubException(0, "Bad Zip file") from None
            except zipfile.LargeZipFile:
                raise EpubException(1, "Large Zip file") from None

        # 1st check metadata
        self._load_container()
        self._load_opf_file()

        self.zf.close()


def read_epub(name, options: dict[str, Any] | None = None) -> EpubBook:
    """
    Creates new instance of EpubBook with the content defined in the input file.

    >>> book = ebooklib.read_epub('book.epub')

    :Args:
      - name: full path to the input file
      - options: extra options as dictionary (optional)

    :Returns:
      Instance of EpubBook.
    """
    reader = EpubReader(name, options)

    book = reader.load()
    reader.process()

    return book
