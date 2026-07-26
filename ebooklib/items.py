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

"""Items which can be part of an EPUB book."""

import posixpath as zip_path
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, cast

from lxml import etree

import ebooklib
from ebooklib.consts import NAMESPACES
from ebooklib.utils import parse_html_string, parse_string

if TYPE_CHECKING:
    from ebooklib.book import EpubBook


class EpubItem:
    """
    Base class for the items in a book.
    """

    def __init__(
        self,
        uid: str | None = None,
        file_name: str = "",
        media_type: str = "",
        content: str | bytes | None = None,
        manifest: bool = True,
    ) -> None:
        """
        :Args:
          - uid: Unique identifier for this item (optional)
          - file_name: File name for this item (optional)
          - media_type: Media type for this item (optional)
          - content: Content for this item (optional)
          - manifest: Manifest for this item (optional)
        """
        self.id = uid
        self.file_name = file_name
        self.media_type = media_type
        self.content: str | bytes = content or b""
        self.is_linear = True
        self.manifest = manifest

        self.book: EpubBook | None = None

    def get_id(self) -> str | None:
        """
        Returns unique identifier for this item.

        :Returns:
          Returns uid number as string.
        """
        return self.id

    def get_name(self) -> str:
        """
        Returns name for this item. By default it is always file name but it does not have to be.

        :Returns:
          Returns file name for this item.
        """
        return self.file_name

    def get_type(self) -> int:
        """
        Guess type according to the file extension. Might not be the best way how to do it, but it works for now.

        Items can be of type:
          - ITEM_UNKNOWN = 0
          - ITEM_IMAGE = 1
          - ITEM_STYLE = 2
          - ITEM_SCRIPT = 3
          - ITEM_NAVIGATION = 4
          - ITEM_VECTOR = 5
          - ITEM_FONT = 6
          - ITEM_VIDEO = 7
          - ITEM_AUDIO = 8
          - ITEM_DOCUMENT = 9
          - ITEM_COVER = 10

        We map type according to the extensions which are defined in ebooklib.EXTENSIONS.

        :Returns:
          Returns type of the item as number.
        """
        _, ext = zip_path.splitext(self.get_name())
        ext = ext.lower()

        for uid, ext_list in ebooklib.EXTENSIONS.items():
            if ext in ext_list:
                return uid

        return ebooklib.ITEM_UNKNOWN

    def get_content(self, default: str | bytes | None = None) -> str | bytes:
        """
        Returns content of the item. Content is usually of type 'bytes' but
        API users assign 'str' as well.

        :Args:
          - default: Default value for the content if it is not already defined.

        :Returns:
          Returns content of the item.
        """
        if default is None:
            default = b""
        return self.content or default

    def set_content(self, content: str | bytes) -> None:
        """
        Sets content value for this item.

        :Args:
          - content: Content value
        """
        self.content = content

    def __str__(self) -> str:
        return f"<EpubItem:{self.id}>"


class EpubNcx(EpubItem):
    """Represents Navigation Control File (NCX) in the EPUB."""

    def __init__(self, uid: str | None = "ncx", file_name: str = "toc.ncx") -> None:
        super().__init__(uid=uid, file_name=file_name, media_type="application/x-dtbncx+xml")

    def __str__(self) -> str:
        return f"<EpubNcx:{self.id}>"


class EpubCover(EpubItem):
    """
    Represents Cover image in the EPUB file.
    """

    def __init__(self, uid: str | None = "cover-img", file_name: str = "") -> None:
        super().__init__(uid=uid, file_name=file_name)

    def get_type(self) -> int:
        return ebooklib.ITEM_COVER

    def __str__(self) -> str:
        return f"<EpubCover:{self.id}:{self.file_name}>"


class EpubHtml(EpubItem):
    """
    Represents HTML document in the EPUB file.
    """

    _template_name = "chapter"

    def __init__(
        self,
        uid: str | None = None,
        file_name: str = "",
        media_type: str = "",
        content: str | bytes | None = None,
        title: str = "",
        lang: str | None = None,
        direction: str | None = None,
        media_overlay: str | None = None,
        media_duration: str | None = None,
    ) -> None:
        super().__init__(uid, file_name, media_type, content)

        self.title = title
        self.lang = lang
        self.direction = direction

        self.media_overlay = media_overlay
        self.media_duration = media_duration

        self.metas: list[dict[str, Any]] = []
        self.links: list[dict[str, Any]] = []
        self.properties: list[str] = []
        self.pages: list[Any] = []

    def is_chapter(self) -> bool:
        """
        Returns if this document is chapter or not.

        :Returns:
          Returns book value.
        """
        return True

    def get_type(self) -> int:
        """
        Always returns ebooklib.ITEM_DOCUMENT as type of this document.

        :Returns:
          Always returns ebooklib.ITEM_DOCUMENT
        """

        return ebooklib.ITEM_DOCUMENT

    def set_language(self, lang: str | None) -> None:
        """
        Sets language for this book item. By default it will use language of the book but it
        can be overwritten with this call.
        """
        self.lang = lang

    def get_language(self) -> str | None:
        """
        Get language code for this book item. Language of the book item can be different from
        the language settings defined globaly for book.

        :Returns:
          As string returns language code.
        """
        return self.lang

    def add_meta(self, **kwgs: Any) -> None:
        """
        Add additional <meta> to the document.

        >>> add_meta(name='viewport', content='width=device-width, initial-scale=1')
        """
        self.metas.append(kwgs)

    def get_metas(self) -> Iterator[dict[str, Any]]:
        """
        Returns list of additional metas defined for this document.

        :Returns:
          As tuple return list of metas.
        """
        return (meta for meta in self.metas)

    def add_link(self, **kwgs: Any) -> None:
        """
        Add additional link to the document. Links will be embeded only inside of this document.

        >>> add_link(href='styles.css', rel='stylesheet', type='text/css')
        """
        self.links.append(kwgs)
        if kwgs.get("type") == "text/javascript":
            if "scripted" not in self.properties:
                self.properties.append("scripted")

    def get_links(self) -> Iterator[dict[str, Any]]:
        """
        Returns list of additional links defined for this document.

        :Returns:
          As tuple return list of links.
        """
        return (link for link in self.links)

    def get_links_of_type(self, link_type: str) -> Iterator[dict[str, Any]]:
        """
        Returns list of additional links of specific type.

        :Returns:
          As tuple returns list of links.
        """
        return (link for link in self.links if link.get("type", "") == link_type)

    def add_item(self, item: EpubItem) -> None:
        """
        Add other item to this document. It will create additional links according to the item type.

        :Args:
          - item: item we want to add defined as instance of EpubItem
        """
        if item.get_type() == ebooklib.ITEM_STYLE:
            self.add_link(href=item.get_name(), rel="stylesheet", type="text/css")

        if item.get_type() == ebooklib.ITEM_SCRIPT:
            self.add_link(src=item.get_name(), type="text/javascript")

    def get_body_content(self) -> bytes:
        """
        Returns content of BODY element for this HTML document. Content will be of type 'bytes'.

        :Returns:
          Returns content of this document.
        """

        try:
            html_tree = parse_html_string(self.content)
        except Exception:
            return b""

        body = html_tree.find("body")

        if body is not None and len(body) != 0:
            tree_str = etree.tostring(body, pretty_print=True, encoding="utf-8", xml_declaration=False)

            # this is so stupid
            if tree_str.startswith(b"<body>"):
                n = tree_str.rindex(b"</body>")

                return tree_str[6:n]

            return tree_str

        return b""

    def get_content(self, default: str | bytes | None = None) -> bytes:
        """
        Returns content for this document as HTML string. Content will be of type 'bytes'.

        :Args:
          - default: Default value for the content if it is not defined.

        :Returns:
          Returns content of this document.
        """

        book = self.book
        if book is None:
            raise ValueError("EpubHtml item is not attached to a book. Call book.add_item() first.")

        template = book.get_template(self._template_name)
        if template is None:
            raise ValueError(f"Book does not define template {self._template_name!r}.")

        tree = parse_string(template)
        tree_root = tree.getroot()

        tree_root.set("lang", self.lang or book.language)
        tree_root.attrib[f"{{{NAMESPACES['XML']}}}lang"] = self.lang or book.language

        # add to the head also
        #  <meta charset="utf-8" />

        try:
            html_tree = parse_html_string(self.content)
        except Exception:
            return b""

        _html_root = html_tree.getroottree()

        # create and populate head

        _head = etree.SubElement(tree_root, "head")

        for meta in self.metas:
            _meta = etree.SubElement(_head, "meta", meta)

        if self.title != "":
            _title = etree.SubElement(_head, "title")
            _title.text = self.title

        for lnk in self.links:
            if lnk.get("type") == "text/javascript":
                _lnk = etree.SubElement(_head, "script", lnk)
                # force <script></script>
                _lnk.text = ""
            else:
                _lnk = etree.SubElement(_head, "link", lnk)

        # create and populate body

        _body = etree.SubElement(tree_root, "body")
        if self.direction:
            _body.set("dir", self.direction)
            tree_root.set("dir", self.direction)

        body = html_tree.find("body")
        if body is not None:
            for i in list(body):
                _body.append(i)

        tree_str = etree.tostring(tree, pretty_print=True, encoding="utf-8", xml_declaration=True)

        return tree_str

    def __str__(self) -> str:
        return f"<EpubHtml:{self.id}:{self.file_name}>"


class EpubCoverHtml(EpubHtml):
    """
    Represents Cover page in the EPUB file.
    """

    def __init__(
        self, uid: str = "cover", file_name: str = "cover.xhtml", image_name: str = "", title: str = "Cover"
    ) -> None:
        super().__init__(uid=uid, file_name=file_name, title=title)

        self.image_name = image_name
        self.is_linear = False

    def is_chapter(self) -> bool:
        """
        Returns if this document is chapter or not.

        :Returns:
          Returns book value.
        """

        return False

    def get_content(self, default: str | bytes | None = None) -> bytes:
        """
        Returns content for cover page as HTML string. Content will be of type 'bytes'.

        :Returns:
          Returns content of this document.
        """

        book = self.book
        if book is None:
            raise ValueError("EpubCoverHtml item is not attached to a book. Call book.add_item() first.")

        self.content = book.get_template("cover") or b""

        tree = parse_string(super().get_content())
        tree_root = tree.getroot()

        images = cast("list[etree._Element]", tree_root.xpath("//xhtml:img", namespaces={"xhtml": NAMESPACES["XHTML"]}))

        images[0].set("src", self.image_name)
        images[0].set("alt", self.title)

        tree_str = etree.tostring(tree, pretty_print=True, encoding="utf-8", xml_declaration=True)

        return tree_str

    def __str__(self) -> str:
        return f"<EpubCoverHtml:{self.id}:{self.file_name}>"


class EpubNav(EpubHtml):
    """
    Represents Navigation Document in the EPUB file.
    """

    def __init__(
        self,
        uid: str | None = "nav",
        file_name: str = "nav.xhtml",
        media_type: str = "application/xhtml+xml",
        title: str = "",
        direction: str | None = None,
    ) -> None:
        super().__init__(uid=uid, file_name=file_name, media_type=media_type, title=title, direction=direction)

    def is_chapter(self) -> bool:
        """
        Returns if this document is chapter or not.

        :Returns:
          Returns book value.
        """

        return False

    def __str__(self) -> str:
        return f"<EpubNav:{self.id}:{self.file_name}>"


class EpubImage(EpubItem):
    """
    Represents Image in the EPUB file.
    """

    def get_type(self) -> int:
        return ebooklib.ITEM_IMAGE

    def __str__(self) -> str:
        return f"<EpubImage:{self.id}:{self.file_name}>"


class EpubSMIL(EpubItem):
    def __init__(self, uid: str | None = None, file_name: str = "", content: str | bytes | None = None) -> None:
        super().__init__(uid=uid, file_name=file_name, media_type="application/smil+xml", content=content)

    def get_type(self) -> int:
        return ebooklib.ITEM_SMIL

    def __str__(self) -> str:
        return f"<EpubSMIL:{self.id}:{self.file_name}>"
