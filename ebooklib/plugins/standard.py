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

# TODO:
#   - should also look for the _required_ elements
# http://www.w3.org/html/wg/drafts/html/master/tabular-data.html#the-table-element

ATTRIBUTES_GLOBAL = [
    "accesskey",
    "class",
    "contenteditable",
    "contextmenu",
    "dir",
    "draggable",
    "dropzone",
    "hidden",
    "id",
    "inert",
    "itemid",
    "itemprop",
    "itemref",
    "itemscope",
    "itemtype",
    "lang",
    "spellcheck",
    "style",
    "tabindex",
    "title",
    "translate",
    "epub:type",
]

# Remove <u> for now from here
DEPRECATED_TAGS = [
    "acronym",
    "applet",
    "basefont",
    "big",
    "center",
    "dir",
    "font",
    "frame",
    "frameset",
    "isindex",
    "noframes",
    "s",
    "strike",
    "tt",
]


def leave_only(item, tag_list):
    for _attr in list(item.attrib.keys()):
        if _attr not in tag_list:
            del item.attrib[_attr]


class SyntaxPlugin(BasePlugin):
    NAME = "Check HTML syntax"

    def html_before_write(self, book, chapter):
        from lxml import etree

        try:
            tree = parse_html_string(chapter.content)
        except Exception:
            return

        root = tree.getroottree()

        # delete deprecated tags
        # i should really have a list of allowed tags
        for tag in DEPRECATED_TAGS:
            etree.strip_tags(root, tag)

        head = tree.find("head")

        if head is not None and len(head) != 0:
            for _item in head:
                match _item.tag:
                    case "base":
                        leave_only(_item, ATTRIBUTES_GLOBAL + ["href", "target"])
                    case "link":
                        leave_only(
                            _item,
                            ATTRIBUTES_GLOBAL + ["href", "crossorigin", "rel", "media", "hreflang", "type", "sizes"],
                        )
                    case "title":
                        if _item.text == "":
                            head.remove(_item)
                    case "meta":
                        leave_only(_item, ATTRIBUTES_GLOBAL + ["name", "http-equiv", "content", "charset"])
                        # just remove for now, but really should not be like this
                        head.remove(_item)
                    case "script":
                        leave_only(
                            _item, ATTRIBUTES_GLOBAL + ["src", "type", "charset", "async", "defer", "crossorigin"]
                        )
                    case "source":
                        leave_only(_item, ATTRIBUTES_GLOBAL + ["src", "type", "media"])
                    case "style":
                        leave_only(_item, ATTRIBUTES_GLOBAL + ["media", "type", "scoped"])
                    case _:
                        leave_only(_item, ATTRIBUTES_GLOBAL)

        body = tree.find("body")

        if body is not None and len(body) != 0:
            for _item in body.iter():
                # it is not
                # <a class="indexterm" href="ch05.html#ix_epub:trigger_element">

                match _item.tag:
                    case "a":
                        leave_only(_item, ATTRIBUTES_GLOBAL + ["href", "target", "download", "rel", "hreflang", "type"])
                    case "area":
                        leave_only(
                            _item,
                            ATTRIBUTES_GLOBAL
                            + ["alt", "coords", "shape", "href", "target", "download", "rel", "hreflang", "type"],
                        )
                    case "audio":
                        leave_only(
                            _item,
                            ATTRIBUTES_GLOBAL
                            + ["src", "crossorigin", "preload", "autoplay", "mediagroup", "loop", "muted", "controls"],
                        )
                    case "blockquote":
                        leave_only(_item, ATTRIBUTES_GLOBAL + ["cite"])
                    case "button":
                        leave_only(
                            _item,
                            ATTRIBUTES_GLOBAL
                            + [
                                "autofocus",
                                "disabled",
                                "form",
                                "formaction",
                                "formenctype",
                                "formmethod",
                                "formnovalidate",
                                "formtarget",
                                "name",
                                "type",
                                "value",
                                "menu",
                            ],
                        )
                    case "canvas":
                        leave_only(_item, ATTRIBUTES_GLOBAL + ["width", "height"])
                    case "del":
                        leave_only(_item, ATTRIBUTES_GLOBAL + ["cite", "datetime"])
                    case "details":
                        leave_only(_item, ATTRIBUTES_GLOBAL + ["open"])
                    case "embed":
                        leave_only(_item, ATTRIBUTES_GLOBAL + ["src", "type", "width", "height"])
                    case "fieldset":
                        leave_only(_item, ATTRIBUTES_GLOBAL + ["disable", "form", "name"])
                    case "form":
                        leave_only(
                            _item,
                            ATTRIBUTES_GLOBAL
                            + [
                                "accept-charset",
                                "action",
                                "autocomplete",
                                "enctype",
                                "method",
                                "name",
                                "novalidate",
                                "target",
                            ],
                        )
                    case "iframe":
                        leave_only(
                            _item,
                            ATTRIBUTES_GLOBAL
                            + ["src", "srcdoc", "name", "sandbox", "seamless", "allowfullscreen", "width", "height"],
                        )
                    case "img":
                        _src = _item.get("src", "").lower()
                        if _src.startswith(("http://", "https://")):
                            if "remote-resources" not in chapter.properties:
                                chapter.properties.append("remote-resources")
                                # THIS DOES NOT WORK, ONLY VIDEO AND AUDIO FILES CAN BE REMOTE RESOURCES
                                # THAT MEANS I SHOULD ALSO CATCH <SOURCE TAG
                                from ebooklib import epub

                                _img = epub.EpubImage(file_name=_item.get("src") or "")
                                book.add_item(_img)
                        leave_only(
                            _item,
                            ATTRIBUTES_GLOBAL + ["alt", "src", "crossorigin", "usemap", "ismap", "width", "height"],
                        )
                    case "input":
                        leave_only(
                            _item,
                            ATTRIBUTES_GLOBAL
                            + [
                                "accept",
                                "alt",
                                "autocomplete",
                                "autofocus",
                                "checked",
                                "dirname",
                                "disabled",
                                "form",
                                "formaction",
                                "formenctype",
                                "formmethod",
                                "formnovalidate",
                                "formtarget",
                                "height",
                                "inputmode",
                                "list",
                                "max",
                                "maxlength",
                                "min",
                                "multiple",
                                "name",
                                "pattern",
                                "placeholder",
                                "readonly",
                                "required",
                                "size",
                                "src",
                                "steptype",
                                "value",
                                "width",
                            ],
                        )
                    case "ins":
                        leave_only(_item, ATTRIBUTES_GLOBAL + ["cite", "datetime"])
                    case "keygen":
                        leave_only(
                            _item, ATTRIBUTES_GLOBAL + ["autofocus", "challenge", "disabled", "form", "keytype", "name"]
                        )
                    case "label":
                        leave_only(_item, ATTRIBUTES_GLOBAL + ["form", "for"])
                    case "map":
                        leave_only(_item, ATTRIBUTES_GLOBAL + ["name"])
                    case "menu":
                        leave_only(_item, ATTRIBUTES_GLOBAL + ["type", "label"])
                    case "object":
                        leave_only(
                            _item,
                            ATTRIBUTES_GLOBAL
                            + ["data", "type", "typemustmatch", "name", "usemap", "form", "width", "height"],
                        )
                    case "ol":
                        leave_only(_item, ATTRIBUTES_GLOBAL + ["reversed", "start", "type"])
                    case "optgroup":
                        leave_only(_item, ATTRIBUTES_GLOBAL + ["disabled", "label"])
                    case "option":
                        leave_only(_item, ATTRIBUTES_GLOBAL + ["disabled", "label", "selected", "value"])
                    case "output":
                        leave_only(_item, ATTRIBUTES_GLOBAL + ["for", "form", "name"])
                    case "param":
                        leave_only(_item, ATTRIBUTES_GLOBAL + ["name", "value"])
                    case "progress":
                        leave_only(_item, ATTRIBUTES_GLOBAL + ["value", "max"])
                    case "q":
                        leave_only(_item, ATTRIBUTES_GLOBAL + ["cite"])
                    case "select":
                        leave_only(
                            _item,
                            ATTRIBUTES_GLOBAL
                            + ["autofocus", "disabled", "form", "multiple", "name", "required", "size"],
                        )
                    case "table":
                        if _item.get("border", None):
                            if _item.get("border") == "0":
                                _item.set("border", "")

                        if _item.get("summary", None):
                            _caption = etree.Element("caption", {})
                            _caption.text = _item.get("summary")
                            _item.insert(0, _caption)

                            # add it as caption
                            del _item.attrib["summary"]

                        leave_only(_item, ATTRIBUTES_GLOBAL + ["border", "sortable"])
                    case "dl":
                        _d = _item.find("dd")
                        if _d is not None and len(_d) == 0:
                            pass

                            # http://html5doctor.com/the-dl-element/
                            # should be like this really
                            # some of the elements can be missing
                            # dl
                            #   dt
                            #   dd
                            #   dt
                            #   dd
                    case "td":
                        leave_only(_item, ATTRIBUTES_GLOBAL + ["colspan", "rowspan", "headers"])
                    case "textarea":
                        leave_only(
                            _item,
                            ATTRIBUTES_GLOBAL
                            + [
                                "autocomplete",
                                "autofocus",
                                "cols",
                                "dirname",
                                "disabled",
                                "form",
                                "inputmode",
                                "maxlength",
                                "name",
                                "placeholder",
                                "readonly",
                                "required",
                                "rows",
                                "wrap",
                            ],
                        )
                    case "col" | "colgroup":
                        leave_only(_item, ATTRIBUTES_GLOBAL + ["span"])
                    case "th":
                        leave_only(
                            _item, ATTRIBUTES_GLOBAL + ["colspan", "rowspan", "headers", "scope", "abbr", "sorted"]
                        )
                    case "time":
                        leave_only(_item, ATTRIBUTES_GLOBAL + ["datetime"])
                    case "track":
                        leave_only(_item, ATTRIBUTES_GLOBAL + ["kind", "src", "srclang", "label", "default"])
                    case "video":
                        leave_only(
                            _item,
                            ATTRIBUTES_GLOBAL
                            + [
                                "src",
                                "crossorigin",
                                "poster",
                                "preload",
                                "autoplay",
                                "mediagroup",
                                "loop",
                                "muted",
                                "controls",
                                "width",
                                "height",
                            ],
                        )
                    case "svg":
                        # We need to add property "svg" in case we have embeded svg file
                        if "svg" not in chapter.properties:
                            chapter.properties.append("svg")

                        if _item.get("viewbox", None):
                            del _item.attrib["viewbox"]

                        if _item.get("preserveaspectratio", None):
                            del _item.attrib["preserveaspectratio"]
                    case _:
                        for _attr in list(_item.attrib.keys()):
                            if _attr not in ATTRIBUTES_GLOBAL:
                                del _item.attrib[_attr]

        chapter.content = etree.tostring(tree, pretty_print=True, encoding="utf-8", xml_declaration=True)

        return chapter.content
