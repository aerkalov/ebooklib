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

"""
https://www.w3.org/TR/SVG/attindex.html

Javascript Code:

```
let targetList = {};
document.querySelectorAll("body > table > tbody > tr").forEach(function(trElement) { 
    var target = trElement.querySelector("th > span > a > span");
    if (target && target.textContent && /[A-Z]/.test(target.textContent)) {
        targetList[target.textContent.toLowerCase()] = target.textContent;
    }
})
JSON.stringify(targetList, null, 2);
```

Updated @ 2023-12-13 15:00 UTC
"""
html_element_attributes_case_sensitive_lookup = {
  "attributename": "attributeName",
  "basefrequency": "baseFrequency",
  "calcmode": "calcMode",
  "clippathunits": "clipPathUnits",
  "diffuseconstant": "diffuseConstant",
  "edgemode": "edgeMode",
  "filterunits": "filterUnits",
  "gradienttransform": "gradientTransform",
  "gradientunits": "gradientUnits",
  "kernelmatrix": "kernelMatrix",
  "kernelunitlength": "kernelUnitLength",
  "keypoints": "keyPoints",
  "keysplines": "keySplines",
  "keytimes": "keyTimes",
  "lengthadjust": "lengthAdjust",
  "limitingconeangle": "limitingConeAngle",
  "markerheight": "markerHeight",
  "markerunits": "markerUnits",
  "markerwidth": "markerWidth",
  "maskcontentunits": "maskContentUnits",
  "maskunits": "maskUnits",
  "numoctaves": "numOctaves",
  "pathlength": "pathLength",
  "patterncontentunits": "patternContentUnits",
  "patterntransform": "patternTransform",
  "patternunits": "patternUnits",
  "pointsatx": "pointsAtX",
  "pointsaty": "pointsAtY",
  "pointsatz": "pointsAtZ",
  "preservealpha": "preserveAlpha",
  "preserveaspectratio": "preserveAspectRatio",
  "primitiveunits": "primitiveUnits",
  "refx": "refX",
  "refy": "refY",
  "repeatcount": "repeatCount",
  "repeatdur": "repeatDur",
  "requiredextensions": "requiredExtensions",
  "specularconstant": "specularConstant",
  "specularexponent": "specularExponent",
  "spreadmethod": "spreadMethod",
  "startoffset": "startOffset",
  "stddeviation": "stdDeviation",
  "stitchtiles": "stitchTiles",
  "surfacescale": "surfaceScale",
  "systemlanguage": "systemLanguage",
  "tablevalues": "tableValues",
  "targetx": "targetX",
  "targety": "targetY",
  "textlength": "textLength",
  "viewbox": "viewBox",
  "xchannelselector": "xChannelSelector",
  "ychannelselector": "yChannelSelector",
  "zoomandpan": "zoomAndPan"
}



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

    try:
        for element in html_tree.xpath('//*'):
            for attribute, value in element.attrib.items():
                if attribute in html_element_attributes_case_sensitive_lookup:
                    del element.attrib[attribute]
                    element.attrib[ html_element_attributes_case_sensitive_lookup[attribute] ] = value
    except:
        pass

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
        """Read the file ``subname`` relative to the EPUB directory and return its bytes.

        ``subname`` typically comes from OPF manifest ``href`` attributes, which are
        attacker-controlled and URL-decoded, so the resolved path must stay inside the
        EPUB directory.

        :param subname: Path of the file, relative to the EPUB directory.
        :returns: Raw content of the file.
        :raises OSError: If ``subname`` escapes the EPUB directory (path traversal,
            e.g. ``"../../secret"``), or if the file cannot be read.
        """
        # Guard against path traversal (e.g. "../../secret") escaping the EPUB directory.
        base_path = os.path.realpath(self.directory_path)
        full_path = os.path.realpath(os.path.join(base_path, subname))

        if os.path.commonpath([base_path, full_path]) != base_path:
            raise OSError(f"Invalid path, escapes the source directory: {subname!r}")

        with open(full_path, "rb") as fp:
            return fp.read()

    def close(self) -> None:
        pass
