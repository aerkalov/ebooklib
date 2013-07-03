import sys

import ebooklib
from ebooklib import epub
from ebooklib.utils import debug

book = epub.read_epub(sys.argv[1])

debug(book.metadata)
debug(book.spine)
debug(book.toc)

#for it in book.items:
#    debug( it.get_type())

for x in  book.get_items_of_type(ebooklib.ITEM_IMAGE):
    debug( x)

from ebooklib.plugins import standard, tidyhtml

opts = {'plugins': [standard.SyntaxPlugin(), tidyhtml.TidyPlugin()]}

epub.write_epub('test.epub', book, opts)
