Tutorial
========

Introduction
------------

Ebooklib is used to manage EPUB2/EPUB3 files.

Reading EPUB
------------
::

    import io
    from pathlib import Path

    import ebooklib
    from ebooklib import epub

    # Read from a file
    book = epub.read_epub('my_awesome_book.epub')
    book = epub.read_epub(Path('my_favorite_book.epub'), options={"ignore_ncx": True})

    # Read from a file-like object
    book = epub.read_epub(io.BytesIO(open('my_favorite_book.epub', 'rb').read()))

    # Read from a path to the directory containing the extracted EPUB file
    book = epub.read_epub('../extracted_book/')

There is a :func:`ebooklib.epub.read_epub` function used for reading EPUB files. It accepts a path to the EPUB file, a file-like object, or a
path to the directory containing the extracted EPUB file. It will return an instance of the :class:`ebooklib.epub.EpubBook` class.

.. warning::

   Be aware that reading EPUB files, making in-place modifications, and writing them back will probably not create what you want.
   More information here: :doc:`faq`.


Metadata
++++++++

The method :meth:`ebooklib.epub.EpubBook.get_metadata` is used for fetching metadata. It accepts two arguments. The first argument
is the name of the namespace ('DC' for Dublin Core and 'OPF' for custom metadata). The second argument is the name of the key.
It always returns a list. The list will be empty if nothing is defined for that key.

Minimal required metadata from Dublin Core set (for EPUB3) is:

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

A book can have several ``dc:identifier`` elements (for example an ISBN next to the main identifier). The package
document's ``unique-identifier`` attribute says which one is the identifier of the publication, and that is the one
``read_epub()`` uses for ``book.uid`` and ``book.IDENTIFIER_ID``, whatever its position among the other identifiers.
All identifiers stay available through ``get_metadata('DC', 'identifier')`` and are written back unchanged. Only if
the attribute is missing, or names an ``id`` that no identifier has (an invalid package), is the last identifier that
has an ``id`` used.


Optional metadata from the Dublin Core set is:

* DC:creator
* DC:contributor
* DC:publisher
* DC:rights
* DC:coverage
* DC:date
* DC:description

This is how Dublin Core metadata is defined inside the content.opf file.

::

    <dc:language>en</dc:language>
    <dc:identifier id="isbn_9781416566120">9781416566120</dc:identifier>

You can also have custom metadata. For instance, this is how custom metadata is defined in the content.opf file.
You can define the same key more than once.

::

    <meta content="my-cover-image" name="cover"/>
    <meta content="cover-image" name="cover"/>

When accessing custom metadata, you will use the namespace 'OPF'. Notice that you will get more than one result now.

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
of the time when handling unknown EPUB files.

**Important to remember!** The methods *get_item_with_id*, *get_item_with_href* will
return item object. The methods *get_items_of_type*, *get_items_of_type* and *get_items* will return iterator (and not list).

To get the content from an existing item (regardless of whether it is an image, style sheet, or HTML file), you use :meth:`ebooklib.epub.EpubItem.get_content`.
For HTML items, you also have :meth:`ebooklib.epub.EpubHtml.get_body_content`. What is the difference? The get_content method always
returns the entire content of the file, while get_body_content only returns whatever is in the <body> part of the HTML document.

Text placed directly in the ``<body>`` (before the first child element), for example ``<body>Before <em>inside</em> after</body>``,
is kept by both methods, and a body that only contains text is returned by ``get_body_content``. Whitespace-only text, such as the
newline and indentation before the first element, is ignored when the document is generated, so ordinary indented chapters produce
the same output as before. A body with only whitespace and no child elements gives an empty ``get_body_content()``.

::

    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            print('==================================')
            print('NAME : ', item.get_name())
            print('----------------------------------')
            print(item.get_content())
            print('==================================')


Reading navigation
~~~~~~~~~~~~~~~~~~

For EPUB 3 books, ``read_epub()`` fills ``book.toc`` and ``book.pages`` from the
navigation document (``nav``). The ``nav`` elements are identified the way the EPUB
specification defines them, by their ``epub:type`` attribute, which holds a
whitespace-separated list of tokens. For example ``epub:type="toc frontmatter"`` is a valid
table of contents. The attribute is matched by its namespace
(``http://www.idpf.org/2007/ops``), so it works with any namespace prefix. ``class``, ``id``
and other attributes have no meaning for the specification and are not used when a
semantic ``epub:type`` match exists.

Books that do not follow the specification are still read, using these fallbacks in order,
only when the semantic lookup found nothing (or the file is not well-formed XML):

1. the first ``nav`` with any attribute whose value is exactly ``toc`` (or ``page-list``),
   such as ``type="toc"``. This legacy match may select an unrelated ``<nav class="toc">`` menu,
   so make sure your books declare ``epub:type`` properly;
2. for the table of contents only, the document's single ``nav`` element, if there is exactly one.
   A page list is never guessed.

A missing page list is ignored because it is optional; ``book.pages`` stays empty.

Whichever source is used, ``book.toc`` is always a list (or tuple, when you set it yourself) of
:class:`ebooklib.epub.Link` and :class:`ebooklib.epub.Section` entries. A book without any table of
contents entries gives an empty list, including an EPUB 2 NCX file with an empty ``navMap``
(or no ``navMap`` at all), so the book can safely be written back with ``write_epub()``. If the NCX has
no entries and the book has an EPUB 3 navigation document, the table of contents is read from it. The NCX is only
used when you pass ``{"ignore_ncx": False}`` to ``read_epub()``; by default the navigation document is preferred.


Reading order
~~~~~~~~~~~~~

``get_items()`` follows manifest/insertion order, not reading order. For a loaded
book returned by ``read_epub()``, ``book.spine`` contains ``(idref, linear)``
tuples. Use those IDs to place spine items first, followed by non-spine resources::

    spine_positions = {
        item_id: position
        for position, (item_id, _) in enumerate(book.spine)
    }
    reading_items = sorted(
        book.get_items(),
        key=lambda item: spine_positions.get(item.get_id(), len(book.spine)),
    )
    for item in reading_items:
        print(item.get_id())

The sort is stable, so non-spine items keep their manifest order at the end.
This includes auxiliary spine entries marked ``linear="no"`` in their declared
positions, rather than limiting the result to the primary reading sequence.
Missing spine references add no items: only resources returned by ``get_items()``
are sorted. This recipe is for loaded books, not the string or item-object spine
entries used when creating a book; it does not sort by filenames or NCX play order.


Creating EPUB
-------------

::

    from ebooklib import epub

    book = epub.EpubBook()

EPUB has some minimal metadata requirements that you need to fulfill. You need to define a unique identifier, the title of the book,
and the language used. When it comes to the language code, the recommended best practice is to use a controlled vocabulary such as RFC 4646
- http://www.ietf.org/rfc/rfc4646.txt.

::

    book.set_identifier("GB33BUKB20201555555555")
    book.set_title("The Book of the Mysterious")
    book.set_language("en")

    book.add_author("John Smith")

You can also add custom metadata. The first one is from the Dublin Core namespace and the second one is purely custom.

::

    book.add_metadata("DC", "description", "A mysterious journey into hidden secrets")
    book.add_metadata(None, 'meta', '', {'name': 'key', 'content': 'value'})

This is how our custom metadata will end up in the *content.opf* file.

::

    <dc:description>This is description for my book</dc:description>
    <meta content="value" name="key"></meta>

Chapters are represented by :class:`ebooklib.epub.EpubHtml`. You must define the *file_name* and *title*. In our case,
the title is going to be used when generating the Table of Contents.

When defining content, you can define it as a valid HTML file or just parts of HTML elements you have as content. It will
ignore whatever you have in the <head> element.

Content may be a Unicode string or UTF-8 bytes, including an XHTML document with
an XML encoding declaration. If the parser rejects a Unicode encoding declaration,
EbookLib retries with UTF-8 bytes; the declaration does not change characters
that have already been decoded. Byte input is also parsed as UTF-8, so decode other encodings before
passing the content to EbookLib. Passing bytes does not bypass the chapter
template or preserve the original <head>. Add stylesheets to both the chapter
and the book as shown below.

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

Do some basic debugging to see what kind of content will end up in the book. In this case, we have inserted the title
of the chapter and the language definition. It would also add links to the style sheet files if we have attached them
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

Item IDs
++++++++

Every item in the book needs a unique ID, which is used in the manifest, the spine and by
:meth:`ebooklib.epub.EpubBook.get_item_with_id`. If you do not pass a ``uid`` to the item,
:meth:`ebooklib.epub.EpubBook.add_item` generates one: ``chapter_N`` for
:class:`ebooklib.epub.EpubHtml`, ``image_N`` for :class:`ebooklib.epub.EpubImage` and ``static_N``
for any other item. Generated IDs skip IDs that are already in the book, so it is safe to add items
without an ID to a book you loaded with ``read_epub()`` that already contains ``chapter_0``.

``add_item()`` returns the item it added, so you can read the generated ID from it::

    chapter = book.add_item(epub.EpubHtml(title='Extra', file_name='extra.xhtml'))
    print(chapter.id)  # chapter_0, or the next free number

The exact generated values are an implementation detail and may change. If your code needs to find an item later,
give it an explicit ``uid`` or keep the returned object. Explicit IDs are not checked: you are responsible for
keeping the ones you choose unique, because an explicit ID that duplicates an existing one makes
``get_item_with_id()`` return the first matching item.


You can add any kind of file to the book. For instance, in this case we are adding a style sheet file. We define
the filename, unique id, media_type, and content for it. Just like the chapter files, you need to add it to the book.
Style sheet files can also be added to the chapter. In that case, links would be automatically added to the
chapter HTML.

::

    style = "body { font-family: Times, Times New Roman, serif; }"

    nav_css = epub.EpubItem(
        uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style
    )

    # Add to the chapter, this will add a link to the style sheet to the chapter HTML
    c2.add_item(nav_css)
    # Add to the book
    book.add_item(nav_css)

There is a simple method to set a cover image. This will create a cover document and add it to the book.
If you are not happy with the default cover page, you can create your own.

::

    book.set_cover("image.jpg", open('cover.jpg', 'rb').read())


The Table of Contents must be defined manually. The ToC is a tuple/list of elements. You can either define a link manually
with :class:`ebooklib.epub.Link` or just insert an item object inside. When you manually insert, you can define a different
title in the ToC than in the chapter. If you just insert an item object, it will use whatever title you defined for
that item when creating it.

Sections are just tuples with two values. The first one is the title of the section and the second is a tuple/list with subchapters.

::

    book.toc = (
        epub.Link("intro.xhtml", "Introduction", "intro"),
        (epub.Section("Languages"), (c1, c2)),
    )

The same goes for the Spine. You can use the unique id for the item or just add an instance of it to the spine.

::

    book.spine = ['nav', c1, c2]


At the end, we need to add NCX and Navigation files. They will not be added automatically.

::

    # Add NCX only if you want to support EPUB 2 reading systems
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())


At the end, write your book. You need to specify the full path to the book or provide a file-like object.
By default, an exception is raised if something goes wrong while writing. Pass the option
*raise_exceptions* as ``False`` to get the old behaviour, where the function returns ``False``
instead of raising and you need to check the return value.

::

    # Write to a file
    epub.write_epub('test.epub', book)

    # Write to a file-like object
    f = io.BytesIO()
    epub.write_epub(f, book)
    f.seek(0)


It also accepts some options.

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
raise_exceptions    True
compresslevel       6
=================   ====================================

The compresslevel ranges from 0 to 9, where 0 is no compression.

The ``mtime`` option (a ``datetime``) sets the ``dcterms:modified`` value and the timestamp of every file in the
archive. Naive values are treated as local time and converted to UTC for ``dcterms:modified``. Passing the same ``mtime``
for the same book gives byte-identical files, which is useful for reproducible builds.

``read_epub()`` has its own options. The option ``ignore_ncx`` (default ``True``) makes the reader prefer the EPUB 3
navigation document over the NCX file; pass ``{"ignore_ncx": False}`` to read the NCX first.

Example of overriding default options:

::

    epub.write_epub('test.epub', book, {"epub3_pages": False})


Samples
-------
Further examples are available in https://github.com/aerkalov/ebooklib/tree/master/samples
