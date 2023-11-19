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

from lxml import etree


mimetype_initialised = False


def debug(obj):
    import pprint

    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(obj)


def parse_string(s):
    parser = etree.XMLParser(recover=True, resolve_entities=False)
    try:
        tree = etree.parse(io.BytesIO(s.encode('utf-8')) , parser=parser)
    except:
        tree = etree.parse(io.BytesIO(s) , parser=parser)

    return tree


def parse_html_string(s):
    from lxml import html

    utf8_parser = html.HTMLParser(encoding='utf-8')

    html_tree = html.document_fromstring(s, parser=utf8_parser)

    return html_tree


def guess_type(extenstion):
    global mimetype_initialised

    if not mimetype_initialised:
        mimetypes.init()
        mimetypes.add_type('application/xhtml+xml', '.xhtml')
        mimetype_initialised = True

    return mimetypes.guess_type(extenstion)


def create_pagebreak(pageref, label=None, html=True):
    from ebooklib.epub import NAMESPACES

    pageref_attributes = {
        '{%s}type' % NAMESPACES['EPUB']: 'pagebreak',
        'title': u'{}'.format(pageref),
        'id': u'{}'.format(pageref),
     }

    pageref_elem = etree.Element('span', pageref_attributes, nsmap={'epub': NAMESPACES['EPUB']})

    if label:
        pageref_elem.text = label

    if html:
        return etree.tostring(pageref_elem, encoding='unicode')

    return pageref_elem


def get_headers(elem):
    for n in range(1, 7):
        headers = elem.xpath('./h{}'.format(n))

        if len(headers) > 0:
            text = headers[0].text_content().strip()
            if len(text) > 0:
                return text
    return None


def get_pages(item):
    body = parse_html_string(item.get_body_content())
    pages = []

    for elem in body.iter():
        if 'epub:type' in elem.attrib:
            if elem.get('id') is not None:
                _text = None
                
                if elem.text is not None and elem.text.strip() != '':
                    _text = elem.text.strip()

                if _text is None:
                    _text = elem.get('aria-label')

                if _text is None:
                    _text = get_headers(elem)

                pages.append((item.get_name(), elem.get('id'), _text or elem.get('id')))

    return pages


def get_pages_for_items(items):
    pages_from_docs = [get_pages(item) for item in items]

    return [item for pages in pages_from_docs for item in pages]
