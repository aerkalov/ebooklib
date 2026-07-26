import sys

import ebooklib
from ebooklib import epub
from ebooklib.utils import debug

book = epub.read_epub(sys.argv[1])

debug(book.metadata)
debug(book.spine)
debug(book.toc)

debug("================================")
debug("SMIL")

for x in book.get_items_of_type(ebooklib.ITEM_SMIL):
    debug(x)

debug("================================")
debug("DOCUMENTS")

for x in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
    if isinstance(x, epub.EpubHtml):
        debug(f"[{x}] media_overlay={x.media_overlay}")

debug("================================")
