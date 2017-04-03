# coding=utf-8

from ebooklib import epub
from ebooklib.plugins.base import BasePlugin

class SamplePlugin(BasePlugin):
    NAME = 'Sample Plugin'

    # Very useless but example of what can be done
    def html_before_write(self, book, chapter):
        from urlparse import urlparse, urljoin

        from lxml import html, etree

        utf8_parser = html.HTMLParser(encoding='utf-8')
        tree = html.document_fromstring(chapter.content, parser=utf8_parser)
        root = tree.getroottree()

        if len(root.find('body')) != 0:
            body = tree.find('body')


            for _link in body.xpath("//a[@class='test']"):
                _link.set('href', 'http://www.binarni.net/')
                    
        chapter.content = etree.tostring(tree, pretty_print=True, encoding='utf-8')
    


if __name__ == '__main__':
    book = epub.EpubBook()

    # add metadata
    book.set_identifier('sample123456')
    book.set_title('Sample book')
    book.set_language('en')

    book.add_author('Aleksandar Erkalovic')

    # intro chapter
    c1 = epub.EpubHtml(title='Introduction', file_name='intro.xhtml', lang='en')
    c1.content=u'<html><head></head><body><h1>Introduction</h1><p>Introduction paragraph <a class="test">with a link</a> where i explain what is happening.</p></body></html>'

    # about chapter
    c2 = epub.EpubHtml(title='About this book', file_name='about.xhtml')
    c2.content='<h1>About this book</h1><p>Helou, this is my book! There are many books, but this one is mine.</p>'

    # add chapters to the book
    book.add_item(c1)
    book.add_item(c2)
    
    # create table of contents
    # - add section
    # - add auto created links to chapters

    book.toc = (epub.Link('intro.xhtml', 'Introduction', 'intro'),
                (epub.Section('Languages'),
                 (c1, c2))
                )

    # add navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # define css style
    style = '''
@namespace epub "http://www.idpf.org/2007/ops";

body {
    font-family: Cambria, Liberation Serif, Bitstream Vera Serif, Georgia, Times, Times New Roman, serif;
}

h2 {
     text-align: left;
     text-transform: uppercase;
     font-weight: 200;     
}

ol {
        list-style-type: none;
}

ol > li:first-child {
        margin-top: 0.3em;
}


nav[epub|type~='toc'] > ol > li > ol  {
    list-style-type:square;
}


nav[epub|type~='toc'] > ol > li > ol > li {
        margin-top: 0.3em;
}

'''

    # add css file
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    # create spine
    book.spine = ['nav', c1, c2]

    
    opts = {'plugins': [SamplePlugin()]}

    # create epub file
    epub.write_epub('test.epub', book, opts)

