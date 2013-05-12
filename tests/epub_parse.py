import sys

from ebooklib import epub

book = epub.read_epub(sys.argv[1])

epub.debug(book.metadata)
epub.debug(book.spine)
epub.debug(book.toc)
for it in book.items:
    epub.debug( it.file_name)

for x in  book.get_items_of_type(epub.ITEM_IMAGE):
    print x


