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

import sys
import os.path
import zipfile
import io
import six

try:
    from urllib.parse import unquote
except ImportError:
    from urllib import unquote

import mimetypes

from lxml import etree

import ebooklib


# This really should not be here
mimetypes.init()


# Version of EPUB library
VERSION = (0, 15, 0)

NAMESPACES = {'XML': 'http://www.w3.org/XML/1998/namespace',
              'EPUB': 'http://www.idpf.org/2007/ops',
              'DAISY': 'http://www.daisy.org/z3986/2005/ncx/',
              'OPF': 'http://www.idpf.org/2007/opf',
              'CONTAINERNS': 'urn:oasis:names:tc:opendocument:xmlns:container',
              'DC': "http://purl.org/dc/elements/1.1/",
              'XHTML': 'http://www.w3.org/1999/xhtml'}

# XML Templates

CONTAINER_PATH = 'META-INF/container.xml'

CONTAINER_XML = '''<?xml version='1.0' encoding='utf-8'?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
  <rootfiles>
    <rootfile media-type="application/oebps-package+xml" full-path="EPUB/content.opf"/>
  </rootfiles>
</container>
'''

NCX_XML = '''<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd"> 
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" />'''

NAV_XML = '''<?xml version="1.0" encoding="utf-8"?><!DOCTYPE html><html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"/>'''

CHAPTER_XML = '''<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE html><html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"  epub:prefix="z3998: http://www.daisy.org/z3998/2012/vocab/structure/#"></html>'''

COVER_XML = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
 <head>
  <style>
    body { margin: 0em; padding: 0em; }
    img { max-width: 100%; max-height: 100%; }
  </style>
 </head>
 <body>
   <img src="" alt="" />
 </body>
</html>'''


IMAGE_MEDIA_TYPES = ['image/jpeg', 'image/png', 'image/svg+xml']


def parse_string(s):
    try:
        tree = etree.parse(io.BytesIO(s.encode('utf-8')))
    except:
        tree = etree.parse(io.BytesIO(s))

    return tree

def debug(obj):
    import pprint

    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(obj)


## TOC elements

class Section(object):
    def __init__(self, title):
        self.title = title

class Link(object):
    def __init__(self, href, title, uid=None):
        self.href = href
        self.title = title
        self.uid = uid

## Exceptions

class EpubException(Exception):
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


## Items

class EpubItem(object):
    def __init__(self, uid=None, file_name='', media_type='', content=''):
        self.id = uid
        self.file_name = file_name
        self.media_type = media_type
        self.content = content
        self.is_linear = True

        self.book = None

    def get_id(self):
        return self.id

    def get_name(self):
        return self.file_name

    def get_type(self):
        """
        Guess type according to the file extension. Not the best way to do it, but works for now.
        """
        _, ext = os.path.splitext(self.get_name())
        ext = ext.lower()

        for uid, ext_list in six.iteritems(ebooklib.EXTENSIONS):
            if ext in ext_list:
                return uid

        return ebooklib.ITEM_UNKNOWN
        
    def get_content(self, default=''):
        return self.content or default

    def set_content(self, content):
        self.content = content

    def __str__(self):
        return '<EpubItem:%s>' % self.id

class EpubNcx(EpubItem):
    def __init__(self, uid='ncx', file_name='toc.ncx'):
        super(EpubNcx, self).__init__(uid=uid, file_name=file_name, media_type="application/x-dtbncx+xml")

    def __str__(self):
        return '<EpubNcx:%s>' % self.id


class EpubCover(EpubItem):
    def __init__(self, uid='cover-img', file_name=''):
        super(EpubCover, self).__init__(uid=uid, file_name=file_name)

    def __str__(self):
        return '<EpubCover:%s:%s>' % (self.id, self.file_name)

        
class EpubHtml(EpubItem):
    def __init__(self, uid=None, file_name='', media_type='', content=None, title='', lang=None):
        super(EpubHtml, self).__init__(uid, file_name, media_type, content)

        self.title = title
        self.lang = lang

        self.links = []
        self.properties = []

        self._template_name = 'chapter'

    def set_language(self, lang):
        self.lang = lang

    def get_language(self):
        return self.lang

    def add_link(self, **kwgs):
        self.links.append(kwgs)

    def get_links(self):
        return (link for link in self.links)

    def get_links_of_type(self, link_type):
        return (link for link in self.links if link.get('type', '') == link_type)

    def add_item(self, item):
        if item.get_type() == ebooklib.ITEM_STYLE:
            self.add_link(href=item.get_name(), rel="stylesheet", type="text/css")

        if item.get_type() == ebooklib.ITEM_SCRIPT:
            self.add_link(href=item.get_name(), type="text/javascript")

    def get_content(self, default=None):
        tree = parse_string(self.book.get_template(self._template_name))
        tree_root = tree.getroot()

        tree_root.set('lang', self.lang or self.book.language)
        tree_root.attrib['{%s}lang' % NAMESPACES['XML']] = self.lang or self.book.language

        # add to the head also
        #  <meta charset="utf-8" />

        from lxml import html

        utf8_parser = html.HTMLParser(encoding='utf-8')
        html_tree = html.document_fromstring(self.content , parser=utf8_parser)
        html_root = html_tree.getroottree()

        if len(html_root.find('body')) != 0:
            body = html_tree.find('body')
            head = html_root.find('head')

            _head = etree.SubElement(tree_root, 'head')
            _title = etree.SubElement(_head, 'title')
            _title.text = self.title

            for lnk in self.links:
                _lnk = etree.SubElement(_head, 'link', lnk)        

            _body = etree.SubElement(tree_root, 'body')

            if body is not None:
                for i in body.getchildren():
                    _body.append(i)

            if head is not None:
                for i in head.getchildren():
                    _head.append(i)

        tree_str = etree.tostring(tree, pretty_print=True, encoding='utf-8', xml_declaration=True)        

        return tree_str

    def __str__(self):
        return '<EpubHtml:%s:%s>' % (self.id, self.file_name)


class EpubCoverHtml(EpubHtml):
    def __init__(self, uid='cover', file_name='cover.xhtml', image_name='', title='Cover'):
        super(EpubCoverHtml, self).__init__(uid=uid, file_name=file_name, title=title)

        self.image_name = image_name
        self.is_linear = False

    def get_content(self):
        self.content = self.book.get_template('cover')

        tree = parse_string(super(EpubCoverHtml, self).get_content())
        tree_root = tree.getroot()

        images = tree_root.xpath('//xhtml:img', namespaces={'xhtml': NAMESPACES['XHTML']})

        images[0].set('src', self.image_name)
        images[0].set('alt', self.title)

        tree_str = etree.tostring(tree, pretty_print=True, encoding='utf-8', xml_declaration=True)        

        return tree_str

    def __str__(self):
        return '<EpubCoverHtml:%s:%s>' % (self.id, self.file_name)

class EpubNav(EpubHtml):
    def __init__(self, uid='nav', file_name='nav.xhtml', media_type="application/xhtml+xml"):
        super(EpubNav, self).__init__(uid=uid, file_name=file_name, media_type=media_type)

    def __str__(self):
        return '<EpubNav:%s:>' % (self.id, self.file_name)


class EpubImage(EpubItem):
    def __init__(self):
        super(EpubImage, self).__init__()

    def __str__(self):
        return '<EpubImage:%s:%s>' % (self.id, self.file_name)


## EpubBook

class EpubBook(object):
    def __init__(self):
        self.EPUB_VERSION = None

        self.reset()
        
    def reset(self):
        "Initialises all needed variables to default values"

        self.uid = ''
        self.metadata = {}
        self.items = []
        self.spine = []

        self.IDENTIFIER_ID = 'id'
        self.FOLDER_NAME = 'EPUB'

        self._id_html = 0
        self._id_image = 0
        self._id_static = 0

        self.title = ''
        self.language = 'en'

        self.templates = {'ncx': NCX_XML,
                          'nav': NAV_XML,
                          'chapter': CHAPTER_XML,
                          'cover': COVER_XML}

        self.add_metadata('OPF', 'generator', '', {'name': 'generator', 'content': 'Ebook-lib %s' % '.'.join([str(s) for s in VERSION])})


    def set_identifier(self, uid):
        "Sets unique id for this epub"

        self.uid = uid

        self.add_metadata('DC', 'identifier', self.uid, {'id': self.IDENTIFIER_ID})

    def set_title(self, title):
        "Set title. You can set multiple titles."

        self.title = title

        self.add_metadata('DC', 'title', self.title)

    def set_language(self, lang):
        "Set language for this epub. You can set multiple languages."

        self.language = lang

        self.add_metadata('DC', 'language', lang)

    def set_cover(self, file_name, content, create_page=True):
        "Set cover and create cover document if needed."

        # as it is now, it can only be called once
        c0 = EpubCover(file_name=file_name)
        c0.content = content
        self.add_item(c0)        

        if create_page:
            c1 = EpubCoverHtml(image_name=file_name)
            self.add_item(c1)        

        self.add_metadata(None, 'meta', '', {'name': 'cover', 'content': 'cover-img'})

    def add_author(self, author, file_as=None, role=None, uid='creator'):
        "Add author for this document"

        self.add_metadata('DC', 'creator', author, {'id': uid})
 
        if file_as:
            self.add_metadata(None, 'meta', file_as, {'refines': '#'+uid,
                                                    'property': 'file-as',
                                                    'scheme': 'marc:relators'})
        if role:
            self.add_metadata(None, 'meta', role, {'refines': '#'+uid,
                                                 'property': 'role',
                                                 'scheme': 'marc:relators'})
                                
    def add_metadata(self, namespace, name, value, others = None):
        "Add metadata"

        if namespace in NAMESPACES:
            namespace = NAMESPACES[namespace]

        if namespace not in self.metadata:
            self.metadata[namespace] = {}

        if name not in self.metadata[namespace]:
            self.metadata[namespace][name] = []

        self.metadata[namespace][name].append(( value, others))

    def add_item(self, item):
        if item.media_type == '':
            item.media_type = mimetypes.types_map[os.path.splitext(item.file_name)[1]]

        if not item.get_id():
            if isinstance(item, EpubHtml):
                item.id = 'chapter_%d' % self._id_html
                self._id_html += 1
            elif isinstance(item, EpubImage):
                item.id = 'image_%d' % self._id_image
                self._id_image += 1
            else:
                item.id = 'static_%d' % self._id_image
                self._id_image += 1                

        item.book = self
        self.items.append(item)

        return item

    def get_item_with_id(self, uid):
        for item in self.get_items():
            if item.id == uid:
                return item

        return None

    def get_item_with_href(self, href):
        for item in self.get_items():
            if item.file_name == href:
                return item

        return None

    def get_items(self):
        return (item for item in self.items)

    def get_items_of_type(self, item_type):
        return (item for item in self.items if item.get_type() == item_type)

    def get_items_of_media_type(self, media_type):
        return (item for item in self.items if item.media_type == media_type)

    def set_template(self, name, value):
        self.templates[name] = value
    
    def get_template(self, name):
        return self.templates.get(name)


###########################################################################################################

class EpubWriter(object):    
    def __init__(self, name, book, options = None):
        self.file_name = name
        self.book = book
        self.options = options or {}

    def process(self):
        # should cache this html parsing so we don't do it for every plugin
        for item in self.book.get_items():
            if isinstance(item, EpubHtml):
                for plg in self.options.get('plugins', []):
                    if hasattr(plg, 'process_html'):
                        plg.process_html(self.book, item)

    def _write_container(self):
        self.out.writestr(CONTAINER_PATH, CONTAINER_XML)

    def _write_opf_file(self):
        root = etree.Element('package',
                             {'xmlns' : NAMESPACES['OPF'],
                              'unique-identifier' : self.book.IDENTIFIER_ID,
                              'version' : '3.0'})

        root.attrib['prefix'] = 'rendition: http://www.ipdf.org/vocab/rendition/#'
         
        ## METADATA
        metadata = etree.SubElement(root, 'metadata', nsmap = {'dc': NAMESPACES['DC'], 
                                                               'opf': NAMESPACES['OPF']})

        import datetime

        el = etree.SubElement(metadata, 'meta', {'property':'dcterms:modified'})
        el.text = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')

        for ns_name, values in six.iteritems(self.book.metadata):
            if ns_name == NAMESPACES['OPF']:
                for values in values.values():
                    for v in values:
                        el = etree.SubElement(metadata, 'meta', v[1])
                        el.text = v[0]
            else:
                for name, values in six.iteritems(values):
                    for v in values:
                        if ns_name:
                            el = etree.SubElement(metadata, '{%s}%s' % (ns_name, name), v[1])
                        else:
                            el = etree.SubElement(metadata, '%s' % name, v[1])

                        el.text = v[0]

        # MANIFEST
        manifest = etree.SubElement(root, 'manifest')
        _ncx_id = None

        # mathml, scripted, svg, remote-resources, and switch
        # nav
        # cover-image

        for item in self.book.get_items():
            if isinstance(item, EpubNav):
                etree.SubElement(manifest, 'item', {'href': item.file_name,
                                                    'id': item.id,
                                                    'media-type': item.media_type,
                                                    'properties': 'nav'})
            elif isinstance(item, EpubNcx):
                _ncx_id = item.id
                etree.SubElement(manifest, 'item', {'href': item.file_name,
                                                    'id': item.id,
                                                    'media-type': item.media_type})

            elif isinstance(item, EpubCover):
                etree.SubElement(manifest, 'item', {'href': item.file_name,
                                                    'id': item.id,
                                                    'media-type': item.media_type,
                                                    'properties': 'cover-image'})
            else:
                opts = {'href': item.file_name,
                        'id': item.id,
                        'media-type': item.media_type}

                if hasattr(item, 'properties') and len(item.properties) > 0:
                    opts['properties' ] = ' '.join(item.properties)

                etree.SubElement(manifest, 'item', opts)
            
        # SPINE
        spine = etree.SubElement(root, 'spine', {'toc': _ncx_id or 'ncx'})

        for _item in self.book.spine:
            # this is for now
            # later we should be able to fetch things from tuple

            is_linear = True

            if isinstance(_item, tuple):
                item = _item[0]

                if len(_item) > 1:
                    if _item[1] == 'no':
                        is_linear = False
            else:
                item = _item

            if isinstance(item, EpubHtml):
                opts =  {'idref': item.get_id()}

                if not item.is_linear or not is_linear:
                    opts['linear'] = 'no'
            elif isinstance(item, EpubItem):
                opts = {'idref': item.get_id()}

                if not item.is_linear or not is_linear:
                    opts['linear'] = 'no'
            else:
                opts = {'idref': item}

                try:
                    itm = self.book.get_item_with_id(item)

                    if not itm.is_linear or not is_linear:
                        opts['linear'] = 'no'
                except:
                    pass

            etree.SubElement(spine, 'itemref', opts)

        # GUIDE
#        guide = etree.SubElement(root, 'guide', {})
#        for item in self.guide:
#            etree.SubElement(guide, 'reference', item)

        tree_str = etree.tostring(root, pretty_print=True, encoding='utf-8', xml_declaration=True)        

        self.out.writestr('%s/content.opf' % self.book.FOLDER_NAME, tree_str)

    def _get_nav(self, item):
        # just a basic navigation for now
        ncx = parse_string(self.book.get_template('nav'))
        root = ncx.getroot()

        root.set('lang', self.book.language)
        root.attrib['{%s}lang' % NAMESPACES['XML']] = self.book.language


        head = etree.SubElement(root, 'head')
        title = etree.SubElement(head, 'title')
        title.text = self.book.title

        # for now this just handles css files and ignores others
        for _link in item.links:
            _lnk = etree.SubElement(head, 'link', {"href":_link.get('href', ''), "rel":"stylesheet", "type":"text/css"})        

        body = etree.SubElement(root, 'body')
        nav  = etree.SubElement(body, 'nav',  {'{%s}type' % NAMESPACES['EPUB']: 'toc', 'id': 'id'})

        content_title = etree.SubElement(nav, 'h2')
        content_title.text = self.book.title

        def _create_section(itm, items):
            ol = etree.SubElement(itm, 'ol')
            for item in items:
                if isinstance(item, tuple) or isinstance(item, list):
                    li = etree.SubElement(ol, 'li')
                    a = etree.SubElement(li, 'span')
                    a.text = item[0].title

                    _create_section(li, item[1])

                elif isinstance(item, Link):
                    li = etree.SubElement(ol, 'li')
                    a = etree.SubElement(li, 'a', {'href': item.href})
                    a.text = item.title
                elif isinstance(item, EpubHtml):
                    li = etree.SubElement(ol, 'li')
                    a = etree.SubElement(li, 'a', {'href': item.file_name})
                    a.text = item.title

        _create_section(nav, self.book.toc)

        tree_str = etree.tostring(root, pretty_print=True, encoding='utf-8', xml_declaration=True)        

        return tree_str

    def _get_ncx(self):

        # we should be able to setup language for NCX as also
        ncx = parse_string(self.book.get_template('ncx'))
        root = ncx.getroot()

        head = etree.SubElement(root, 'head')

        # get this id
        uid = etree.SubElement(head, 'meta', {'content': self.book.uid, 'name': 'dtb:uid'})
        uid = etree.SubElement(head, 'meta', {'content': '0', 'name': 'dtb:depth'})
        uid = etree.SubElement(head, 'meta', {'content': '0', 'name': 'dtb:totalPageCount'})
        uid = etree.SubElement(head, 'meta', {'content': '0', 'name': 'dtb:maxPageNumber'})

        doc_title = etree.SubElement(root, 'docTitle')
        title = etree.SubElement(doc_title, 'text')
        title.text = self.book.title

#        doc_author = etree.SubElement(root, 'docAuthor')
#        author = etree.SubElement(doc_author, 'text')
#        author.text = 'Name of the person'

        # For now just make a very simple navMap
        nav_map = etree.SubElement(root, 'navMap')

        def _create_section(itm, items, uid):
            for item in items:
                if isinstance(item, tuple) or isinstance(item, list):
                    np = etree.SubElement(itm, 'navPoint', {'id': 'sep_%d' % uid})
                    nl = etree.SubElement(np, 'navLabel')
                    nt = etree.SubElement(nl, 'text')
                    nt.text = item[0].title

                    # CAN NOT HAVE EMPTY SRC HERE
                    nc = etree.SubElement(np, 'content', {'src': ''})

                    #uid += 1
                    uid = _create_section(np, item[1], uid+1)

                elif isinstance(item, Link):
                    np = etree.SubElement(itm, 'navPoint', {'id': item.uid})
                    nl = etree.SubElement(np, 'navLabel')
                    nt = etree.SubElement(nl, 'text')
                    nt.text = item.title

                    nc = etree.SubElement(np, 'content', {'src': item.href})
                elif isinstance(item, EpubHtml):
                    _parent = itm
                    _content = _parent.find('content')

                    if _content != None:
                        if _content.get('src') == '':
                            _content.set('src', item.file_name)

                    np = etree.SubElement(itm, 'navPoint', {'id': item.get_id()})
                    nl = etree.SubElement(np, 'navLabel')
                    nt = etree.SubElement(nl, 'text')
                    nt.text = item.title
                    nc = etree.SubElement(np, 'content', {'src': item.file_name})

            return uid

        _create_section(nav_map, self.book.toc, 0)

        tree_str = etree.tostring(root, pretty_print=True, encoding='utf-8', xml_declaration=True)        

        return tree_str
        
    def _write_items(self):
        for item in self.book.get_items():
            if isinstance(item, EpubNcx):
                self.out.writestr('%s/%s' % (self.book.FOLDER_NAME, item.file_name), self._get_ncx())
            elif isinstance(item, EpubNav):
                self.out.writestr('%s/%s' % (self.book.FOLDER_NAME, item.file_name), self._get_nav(item))
            else:
                self.out.writestr('%s/%s' % (self.book.FOLDER_NAME, item.file_name), item.get_content())

    def write(self):
        # check for the option allowZip64
        self.out = zipfile.ZipFile(self.file_name, 'w', zipfile.ZIP_DEFLATED)
        self.out.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)

        self._write_container()
        self._write_opf_file()
        self._write_items()

        self.out.close()

###########################################################################################################

class EpubReader(object):
    def __init__(self, epub_file_name):
        self.file_name = epub_file_name
        self.book = EpubBook()
        self.zf = None

        self.opf_file = ''
        self.opf_dir = ''

    def load(self):
        self._load()

        return self.book
        
    def read_file(self, name):
        # Raises KeyError
        return self.zf.read(name)

    def _load_container(self):
        meta_inf = self.read_file('META-INF/container.xml')
        tree = parse_string(meta_inf)

        for root_file in tree.findall('//xmlns:rootfile[@media-type]', namespaces = {'xmlns': NAMESPACES['CONTAINERNS']}):
            if root_file.get('media-type') == "application/oebps-package+xml":
                self.opf_file =  root_file.get('full-path')
                self.opf_dir = os.path.dirname(self.opf_file)

    def _load_metadata(self):
        container_root = self.container.getroot()

        # get epub version
        self.book.version = container_root.get('version', None)

        # get unique-identifier
        if container_root.get('unique-identifier', None):
            self.book.IDENTIFIER_ID = container_root.get('unique-identifier')

        # get xml:lang
        # get metadata
        metadata = self.container.find('{%s}%s' % (NAMESPACES['OPF'], 'metadata'))

        nsmap = metadata.nsmap
        nstags = dict((k, '{%s}' % v) for k, v in six.iteritems(nsmap))
        default_ns = nstags.get(None, '')

        nsdict = dict((v, {}) for v in nsmap.values())

        def add_item(ns, tag, value, extra):
            if ns not in nsdict:
                nsdict[ns] = {}

            values = nsdict[ns].setdefault(tag, [])
            values.append((value, extra))

        for t in metadata.iter(tag=etree.Element):
            if t.tag == default_ns + 'meta':
                name = t.get('name')
                others = dict((k, v) for k, v in six.iteritems(t))

                if name and ':' in name:
                    prefix, name = name.split(':', 1)
                else:
                    prefix = None
                
                add_item(t.nsmap.get(prefix, prefix), name, t.text, others)
            else:
                tag = t.tag[t.tag.rfind('}') + 1:]

                if (t.prefix and t.prefix.lower() == 'dc') and tag == 'identifier':
                    self.book.IDENTIFIER_ID = t.get('id', None)

                others = dict((k, v) for k, v in six.iteritems(t))
                add_item(t.nsmap[t.prefix], tag, t.text, others)

        self.book.metadata = nsdict

    def _load_manifest(self):
        for r in self.container.find('{%s}%s' % (NAMESPACES['OPF'], 'manifest')):
            if r is not None and r.tag != '{%s}item' % NAMESPACES['OPF']:
                continue

            media_type = r.get('media-type')
            _properties = r.get('properties', '') 

            if _properties:
                properties = _properties.split(' ')
            else:
                properties = []

            if media_type == 'application/x-dtbncx+xml':
                ei = EpubNcx(uid=r.get('id'), file_name=unquote(r.get('href')))

                ei.content = self.read_file(os.path.join(self.opf_dir, ei.file_name))
            elif media_type == 'application/xhtml+xml':
                if 'nav' in properties:
                    ei = EpubNav(uid=r.get('id'), file_name=unquote(r.get('href')))

                    ei.content = self.read_file(os.path.join(self.opf_dir, r.get('href')))
                elif 'cover' in properties:
                    ei = EpubCoverHtml()

                    ei.content = self.read_file(os.path.join(self.opf_dir,  unquote(r.get('href'))))
                else:
                    ei = EpubHtml()

                    ei.id = r.get('id')
                    ei.file_name = unquote(r.get('href'))
                    ei.media_type = media_type
                    ei.content = self.read_file(os.path.join(self.opf_dir, ei.file_name))
                    ei.properties = properties
            elif media_type in IMAGE_MEDIA_TYPES:
                ei = EpubImage()

                ei.id = r.get('id')
                ei.file_name = unquote(r.get('href'))
                ei.media_type = media_type
                ei.content = self.read_file(os.path.join(self.opf_dir, ei.file_name))
            else:
                # different types
                ei = EpubItem()
                
                ei.id = r.get('id')
                ei.file_name = unquote(r.get('href'))
                ei.media_type = media_type

                ei.content = self.read_file(os.path.join(self.opf_dir, ei.file_name))
              # r.get('properties')

            self.book.add_item(ei)


    def _parse_ncx(self, data):
        tree = parse_string(data);
        tree_root = tree.getroot()

        nav_map = tree_root.find('{%s}navMap' % NAMESPACES['DAISY'])

        def _get_children(elems, n, nid):
            label, content = '', ''
            children = []
            _id = ''
            for a in elems.getchildren():
                if a.tag == '{%s}navLabel' %  NAMESPACES['DAISY']:
                    label = a.getchildren()[0].text
                if a.tag == '{%s}content' %  NAMESPACES['DAISY']:
                        content = a.get('src')
                if a.tag == '{%s}navPoint' %  NAMESPACES['DAISY']:
                    children.append(_get_children(a, n+1, a.get('id', '')))

            if len(children) > 0:
                if n == 0:
                    return children

                return (Section(label),
                        children)
            else:
                return (Link(content, label, nid))


        self.book.toc = _get_children(nav_map, 0, '')
        # debug(self.book.toc)

    def _load_spine(self):
        spine = self.container.find('{%s}%s' % (NAMESPACES['OPF'], 'spine'))
        
        self.book.spine = [(t.get('idref'), t.get('linear', 'yes')) for t in spine]

        toc = spine.get('toc', '')

        # should read ncx or nav file
        if toc:
            try:
                ncxFile = self.read_file(os.path.join(self.opf_dir, self.book.get_item_with_id(toc).file_name))
            except KeyError:
                raise EpubError(-1, 'Can not find ncx file.')

            self._parse_ncx(ncxFile)


    def _load_opf_file(self):
        try:
            s = self.read_file(self.opf_file)
        except KeyError:
            raise EpubError(-1, 'Can not find container file')

        self.container = parse_string(s)

        self._load_metadata()
        self._load_manifest()
        self._load_spine()
        # should read nav file if found

    
    def _load(self):
        try:
            self.zf = zipfile.ZipFile(self.file_name, 'r', compression = zipfile.ZIP_DEFLATED, allowZip64 = True)
        except zipfile.BadZipfile as bz:
            raise EpubException(0, 'Bad Zip file')
        except zipfile.LargeZipFile as bz:
            raise EpubException(1, 'Large Zip file')

        # 1st check metadata
        self._load_container()
        self._load_opf_file()
        
        self.zf.close()


## WRITE

def write_epub(name, book, options = None):
    epub = EpubWriter(name, book, options)

    epub.process()

    try:
        epub.write()
    except IOError:
        pass

## READ

def read_epub(name):
    reader = EpubReader(name)

    book = reader.load()

    return book

