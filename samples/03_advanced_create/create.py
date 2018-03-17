# coding=utf-8

from ebooklib import epub


if __name__ == '__main__':
    book = epub.EpubBook()

    # add metadata
    book.set_identifier('sample123456')
    book.set_title('Sample book')
    book.set_language('en')

    book.add_author('Aleksandar Erkalovic')

    # intro chapter
    c1 = epub.EpubHtml(title='Introduction', file_name='intro.xhtml', lang='hr')
    c1.content=u'<html><head></head><body><h1>Introduction</h1><p>Introduction paragraph where i explain what is happening.</p></body></html>'

    # defube style
    style = '''BODY { text-align: justify;}'''

    default_css = epub.EpubItem(uid="style_default", file_name="style/default.css", media_type="text/css", content=style)
    book.add_item(default_css)


    # about chapter
    c2 = epub.EpubHtml(title='About this book', file_name='about.xhtml')
    c2.content='<h1>About this book</h1><p>Helou, this is my book! There are many books, but this one is mine.</p>'
    c2.set_language('hr')
    c2.properties.append('rendition:layout-pre-paginated rendition:orientation-landscape rendition:spread-none')
    c2.add_item(default_css)

    # add chapters to the book
    book.add_item(c1)
    book.add_item(c2)


    
    # create table of contents
    # - add manual link
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

    # create epub file
    epub.write_epub('test.epub', book, {})

