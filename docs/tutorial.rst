Tutorial
========

Introduction
------------

Ebooklib is used to manage EPUB2/EPUB3 files.

Reading EPUB
------------
::

    import ebooklib
    from ebooklib import epub

    book = epub.read_epub('test.epub')

There is a :func:`ebooklib.epub.read_epub` function used for reading EPUB files. It accepts full file path to the
EPUB file as argument. It will return instance of :class:`ebooklib.epub.EpubBook` class.


Metadata
++++++++

Method :meth:`ebooklib.epub.EpubBook.get_metadata` is used for fetching metadata. It accepts 2 arguments. First argument
is name of the namespace ('DC' for Dublin Core and 'OPF' for custom metadata). Second argument is name of the key.
It always returns a list. List will be empty if nothing is defined for that key.

Minimal required metadata from Dublic Core set (for EPUB3) is:

* DC:identifier
* DC:title
* DC:language

'DC' namespace is used when accessing Dublin Core metadata.

::

    >>> book.get_metadata('DC', 'title')
    [('Ratio', {})]

    >>> book.get_metadata('DC', 'creator')
    [('Firstname Lastname ', {})]

    >>> book.get_metadata('DC', 'identifier')
    [('9781416566120', {'id': 'isbn_9781416566120'})]


Optional metadata from the Dublic Core set is:

* DC:creator
* DC:contributor
* DC:publisher
* DC:rights
* DC:coverage
* DC:date
* DC:description

This is how Dublin Core metadata is defined inside of content.opf file.

::

    <dc:language>en</dc:language>
    <dc:identifier id="isbn_9781416566120">9781416566120</dc:identifier>

You can also have custom metadata. For instance this is how custom metadata is defined in content.opf file.
You can define same key more then once.
2
::

    <meta content="my-cover-image" name="cover"/>
    <meta content="cover-image" name="cover"/>

When accessing custom metadata you will use namespace 'OPF'. Notice you will get more then one result now.

::

    >>> book.get_metadata('OPF', 'cover')
    [(None, {'content': 'my-cover-image', 'name': 'cover'}),
     (None, {'content': 'cover-image', 'name': 'cover'})]

Check the official documentation for more info:

* http://www.idpf.org/epub/30/spec/epub30-publications.html#sec-opf-dcmes-optional.
* http://www.idpf.org/epub/30/spec/epub30-publications.html
* http://dublincore.org/documents/dces/


Items
+++++

All of the resources (style sheets, images, videos, sounds, scripts and html files) are items.


::

    images = book.get_items_of_type(ebooklib.ITEM_IMAGE)

Fetch items by their type with :meth:`ebooklib.epub.EpubBook.get_items_of_type`.

Here is a list of current item types you can use:

* ITEM_UNKNOWN
* ITEM_IMAGE
* ITEM_STYLE
* ITEM_SCRIPT
* ITEM_NAVIGATION
* ITEM_VECTOR
* ITEM_FONT
* ITEM_VIDEO
* ITEM_AUDIO
* ITEM_DOCUMENT
* ITEM_COVER
* ITEM_SMIL

::

    cover_image = book.get_item_with_id('cover-image')

Fetch items by their id (if you know it) with :meth:`ebooklib.epub.EpubBook.get_item_with_id`.

::

    index = book.get_item_with_href('index.xhtml')

Fetch them by their filename with :meth:`ebooklib.epub.EpubBook.get_item_with_href`.

::

    items = book.get_items_of_media_type('image/png')

Fetch them by their media type with :meth:`ebooklib.epub.EpubBook.get_items_of_type`.

::

    all_items = book.get_items()

Return all of the items with :meth:`ebooklib.epub.EpubBook.get_items`. This is what you are going to use most
of the times when handling unknown EPUB files.

**Important to remember!** Methods *get_item_with_id*, *get_item_with_href* will
return item object. Methods *get_items_of_type*, *get_items_of_type* and *get_items* will return iterator (and not list).

To get a content from existing item (regarding if it is image, style sheet or html file) you use :meth:`ebooklib.epub.EpubItem.get_content`.
For HTML items you also have :meth:`ebooklib.epub.EpubHtml.get_body_content`. What is the difference? Get_content always
return entire content of the file while get_body_content only returns whatever is in the <body> part of the HTML document.

::

    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            print('==================================')
            print('NAME : ', item.get_name())
            print('----------------------------------')
            print(item.get_content())
            print('==================================')


Creating EPUB
-------------

::

    from ebooklib import epub

    book = epub.EpubBook()

EPUB has some minimal metadata requirements which you need to fulfil. You need to define unique identifier, title of the book
and language used inside. When it comes to language code recommended best practice is to use a controlled vocabulary such as RFC 4646
- http://www.ietf.org/rfc/rfc4646.txt.

::

    book.set_identifier('sample123456')
    book.set_title('Sample book')
    book.set_language('en')

    book.add_author('Aleksandar Erkalovic')

You can also add custom metadata. First one is from the Dublic Core namespace and second one is purely custom.

::

    book.add_metadata('DC', 'description', 'This is description for my book')
    book.add_metadata(None, 'meta', '', {'name': 'key', 'content': 'value'})

This is how our custom metadata will end up in the *content.opf* file.

::

    <dc:description>This is description for my book</dc:description>
    <meta content="value" name="key"></meta>

Chapters are represented by :class:`ebooklib.epub.EpubHtml`. You must define the *file_name* and *title*. In our case
title is going to be used when generating Table of Contents.

When defining content you can define it as valid HTML file or just parts of HTML elements you have as a content. It will
ignore whatever you have in <head> element.

::

    # intro chapter
    c1 = epub.EpubHtml(title='Introduction',
                       file_name='intro.xhtml',
                       lang='en')
    c1.set_content(u'<html><body><h1>Introduction</h1><p>Introduction paragraph.</p></body></html>')

    # about chapter
    c2 = epub.EpubHtml(title='About this book',
                       file_name='about.xhtml')
    c2.set_content('<h1>About this book</h1><p>This is a book.</p>')

Do some basic debugging to see what kind of content will end up in the book. In this case we have inserted title
of the chapter and language definition. It would also add links to the style sheet files if we have attached them
to this chapter.

::

    >>> print(c1.get_content())
    b'<?xml version=\'1.0\' encoding=\'utf-8\'?>\n<!DOCTYPE html>\n<html xmlns="http://www.w3.org/1999/xhtml"
    xmlns:epub="http://www.idpf.org/2007/ops" epub:prefix="z3998: http://www.daisy.org/z3998/2012/vocab/structure/#"
    lang="en" xml:lang="en">\n  <head>\n    <title>Introduction</title>\n  </head>\n  <body>\n    <h1>Introduction</h1>\n
    <p>Introduction paragraph.</p>\n  </body>\n</html>\n'

Any kind of item (style sheet, image, HTML file) must be added to the book.

::

    book.add_item(c1)
    book.add_item(c2)


You can add any kind of file to the book. For instance, in this case we are adding style sheet file. We define
filename, unique id, media_type and content for it. Just like the chapter files you need to add it to the book.
Style sheet files could also be added to the chapter. In that case links would be automatically added to the
chapter HTML.

::

    style = 'body { font-family: Times, Times New Roman, serif; }'

    nav_css = epub.EpubItem(uid="style_nav",
                            file_name="style/nav.css",
                            media_type="text/css",
                            content=style)
    book.add_item(nav_css)


Table of the contents must be defined manually. ToC is a tuple/list of elements. You can either define link manually
with :class:`ebooklib.epub.Link` or just insert item object inside. When you manually insert you can define different
title in the ToC than in the chapter. If you just insert item object it will use whatever title you defined for
that item when creating it.

Sections are just tuple with two values. First one is title of the section and 2nd is tuple/list with subchapters.

::

    book.toc = (epub.Link('intro.xhtml', 'Introduction', 'intro'),
                  (
                    epub.Section('Languages'),
                    (c1, c2)
                  )
                )

So as the Spine. You can use unique id for the item or just add instance of it to the spine.

::

    book.spine = ['nav', c1, c2]


At the end we need to add NCX and Navigation tile. They will not be added automatically.

::

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())


At the end write down your book. You need to specify full path to the book, you can not write it down to the
File Object or something else.

::

    epub.write_epub('test.epub', book)

It also accepts some of the options.

=================   ====================================
Option              Default value
=================   ====================================
epub2_guide         True
epub3_landmark      True
epub3_pages         True
landmark_title      "Guide"
pages_title         "Pages"
spine_direction     True
package_direction   False
play_order          {'enabled': False, 'start_from': 1}
=================   ====================================

Example when overriding default options:

::

    epub.write_epub('test.epub', book, {"epub3_pages": False})


Samples
-------
Further examples are available in https://github.com/aerkalov/ebooklib/tree/master/samples
