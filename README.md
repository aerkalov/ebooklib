# About EbookLib

EbookLib is a Python library for managing EPUB2/EPUB3. It's capable of reading and writing EPUB files programmatically.

Heads up! EbookLib 0.20 is the final version supporting Python 2.7. Moving forward, we're leaving legacy code behind and embracing modern Python features to make EbookLib even more awesome.

We are working on [refreshing the project](https://github.com/aerkalov/ebooklib/issues/318) so please check and comment if you have your own ideas what needs to happen with the project.

Want to contribute? It's easy! We welcome bug reports, suggestions, and Pull Requests. Before submitting a Pull Request, [please take a quick look at our simple guidelines](https://github.com/aerkalov/ebooklib/wiki/Contributing). Our contribution process is straightforward, with no special procedures
to worry about.

The API is designed to be as simple as possible, while at the same time making complex things possible too.  It has support for covers, table of contents, spine, guide, metadata and etc.

EbookLib is used in [Booktype](https://github.com/booktype/Booktype/) from Sourcefabric, as well as [Audiblez](https://github.com/santinic/audiblez), [e2m](https://github.com/wisupai/e2m), [ebook2audiobook](https://github.com/DrewThomasson/ebook2audiobook), [Marker](https://github.com/VikParuchuri/marker) and [Telemeta](https://github.com/Parisson/Telemeta). You can find a more extensive list of projects utilizing EbookLib [here](https://github.com/aerkalov/ebooklib/wiki/Who-uses-ebooklib).

Packages of EbookLib for GNU/Linux are available in [Debian](https://packages.debian.org/python-ebooklib) and [Ubuntu](http://packages.ubuntu.com/python-ebooklib).

Sphinx documentation is generated from the templates in the docs/ directory and made available at http://ebooklib.readthedocs.io

# Usage

## Reading
```py
import os
import ebooklib
from ebooklib import epub

book = epub.read_epub('test.epub')

# Export all images from the Book
for image in book.get_items_of_type(ebooklib.ITEM_IMAGE):
    with open(os.path.basename(image.get_name()), "wb") as f:
        f.write(image.get_content())
```


## Writing
```py
from ebooklib import epub

book = epub.EpubBook()

# Set metadata
book.set_identifier("GB33BUKB20201555555555")
book.set_title("The Book of the Mysterious")
book.set_language("en")

book.add_author("John Smith")
book.add_author(
    "Hans Müller",
    file_as="Dr. Hans Müller",
    role="ill",
    uid="coauthor",
)

book.add_metadata("DC", "description", "A mysterious journey into hidden secrets")
book.add_metadata("DC", "publisher", "Mystic Books Publishing House")

# Create chapter in English
c1 = epub.EpubHtml(title="Introduction", file_name="introduction.xhtml", lang="en")
c1.content = (
    "<h1>The Book of the Mysterious</h1>"
    "<p>Welcome to a journey into the unknown. In these pages, you'll discover "
    "secrets that have remained hidden for centuries.</p>"
    '<p><img alt="Book Cover" src="static/ebooklib.gif"/></p>'
)
# Create chapter in German
c2 = epub.EpubHtml(title="Einführung", file_name="einfuehrung.xhtml", lang="de")
c2.content = (
    "<h1>Das Buch des Geheimnisvollen</h1>"
    "<p>Willkommen zu einer Reise ins Unbekannte. Auf diesen Seiten werden Sie "
    "Geheimnisse entdecken, die jahrhundertelang verborgen geblieben sind.</p>"
)

# Create image from the local image
img = epub.EpubImage(
    uid="image_1",
    file_name="static/ebooklib.gif",
    media_type="image/gif",
    content=open("ebooklib.gif", "rb").read(),
)

# Define CSS style
nav_css = epub.EpubItem(
    uid="style_nav",
    file_name="style/nav.css",
    media_type="text/css",
    content="BODY {color: black; background-color: white;}",
)

# Every chapter must me added to the book
book.add_item(c1)
book.add_item(c2)
# This also includes images, style sheets, etc.
book.add_item(img)
book.add_item(nav_css)

# Define Table Of Contents
book.toc = (
    epub.Link("introduction.xhtml", "Introduction", "intro"),
    (epub.Section("Deutsche Sektion"), (c2,)),
)

# Basic spine
book.spine = ["nav", c1, c2]

# Add default NCX (not required) and Nav files.
book.add_item(epub.EpubNcx())
book.add_item(epub.EpubNav())

# Write to the file
epub.write_epub("the_book_of_the_mysterious.epub", book)
```


# License
EbookLib is licensed under the [AGPL license](LICENSE.txt).


# Authors
Full list of authors is in [AUTHORS.txt](AUTHORS.txt) file.
