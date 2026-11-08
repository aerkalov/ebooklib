import io
import zipfile

from lxml import etree

import ebooklib
from ebooklib import epub

XHTML = "{" + epub.NAMESPACES["XHTML"] + "}"
OPF = "{" + epub.NAMESPACES["OPF"] + "}"
EPUB_TYPE = "{" + epub.NAMESPACES["EPUB"] + "}type"


def _write_cover_book(guide=None):
    book = epub.EpubBook()
    book.set_identifier("cover-landmark")
    book.set_title("Cover landmark")
    book.set_language("en")
    book.set_cover("image.jpg", b"fake image data")

    chapter = epub.EpubHtml(uid="chapter", file_name="chapter.xhtml", title="Chapter")
    chapter.set_content("<h1>Chapter</h1>")
    book.add_item(chapter)
    book.add_item(epub.EpubNav())
    book.toc = [chapter]
    book.spine = ["cover", "nav", chapter]
    book.guide = guide or []

    output = io.BytesIO()
    epub.write_epub(output, book)
    output.seek(0)

    with zipfile.ZipFile(output) as archive:
        nav = etree.fromstring(archive.read("EPUB/nav.xhtml"))
        opf = etree.fromstring(archive.read("EPUB/content.opf"))

    landmarks = [
        (a.get(EPUB_TYPE), a.get("href"), a.text)
        for landmarks_nav in nav.iter(XHTML + "nav")
        if landmarks_nav.get(EPUB_TYPE) == "landmarks"
        for a in landmarks_nav.iter(XHTML + "a")
    ]
    references = [(ref.get("type"), ref.get("href"), ref.get("title")) for ref in opf.iter(OPF + "reference")]
    spine = {ref.get("idref"): ref.get("linear") for ref in opf.iter(OPF + "itemref")}
    return landmarks, references, spine


class TestEpubCover:
    def test_init_default(self):
        cover = epub.EpubCover()

        assert cover.get_id() == "cover-img"
        assert cover.get_type() == ebooklib.ITEM_COVER

    def test_non_linear_cover_page_is_reachable_from_nav(self):
        # EPUB 3.3 (EPUBCheck OPF-096): non-linear content must be reachable through a hyperlink.
        landmarks, references, spine = _write_cover_book()

        assert spine["cover"] == "no"
        assert landmarks == [("cover", "cover.xhtml", "Cover")]
        assert references == [("cover", "cover.xhtml", "Cover")]

    def test_existing_cover_guide_entry_is_not_duplicated(self):
        guide = [
            {"type": "cover", "href": "cover.xhtml", "title": "Front cover"},
            {"type": "text", "href": "chapter.xhtml", "title": "Start"},
        ]
        landmarks, references, _ = _write_cover_book(guide)

        assert landmarks == [("cover", "cover.xhtml", "Front cover"), ("bodymatter", "chapter.xhtml", "Start")]
        assert references == [("cover", "cover.xhtml", "Front cover"), ("text", "chapter.xhtml", "Start")]
