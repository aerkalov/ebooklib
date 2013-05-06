About EbookLib
==============

E-book library for Python capable of handling EPUB2/EPUB3 and Kindle format

Installation
============



Usage
=====

Reading
-------

    from ebooklib import epub

    book = epub.readEPUB('test.epub')

Writing
-------

    from ebooklib import epub

    book = epub.EpubBook()

    # set metadata
    book.set_identifier('id123456')
    book.set_title('This is my book')
    book.set_language('en')

    book.add_author('Author Authorowski')
    book.add_author('Danko Bananko', file_as='Gospodin Danko Bananko', role='ill', uid='coauthor')

    # create chapter
    c1 = epub.EpubHtml(title='Intro 1', file_name='chap_01.xhtml', lang='hr')
    c1.content=u'<html><head></head><body><h1>This is I!</h1><p>This is something i am writing.</p><p>Šime Đodan ima puno posla.</p></body></html>'

    # add chapter
    book.add_item(c1)

    # define Table Of Contents
    book.toc = (epub.Link('chap_01.xhtml', 'Introduction', 'intro'),
                (epub.Section('Languages'),
                 (c1, ))
                )

    # add default NCX and Nav file
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # define CSS style
    nav_css = 'BODY {color: white;}'
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)

    # add CSS file
    book.add_item(nav_css)

    # basic spine
    book.spine = ['nav', c1]

    # write to the file
    epub.writeEPUB('test.epub', book, {})



License
=======

EbookLib is licensed under the AGPL license.


Authors
=======
* Aleksandar Erkalovic <aerkalov@gmail.com>
* Borko Jandras <bjandras@gmail.com>




