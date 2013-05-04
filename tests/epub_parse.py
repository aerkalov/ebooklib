import sys

from ebooklib import epub


book = epub.readEPUB(sys.argv[1])

print book.metadata

for it in book.items:
    print it

book.add_item(epub.EpubNav())
epub.writeEPUB('test.epub', book, {})

