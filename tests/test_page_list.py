"""Regression tests for automatically generated page navigation (issue #339)."""

import io
import zipfile

import pytest
from lxml import etree

from ebooklib import epub

XHTML = "{" + epub.NAMESPACES["XHTML"] + "}"
EPUB_TYPE = "{" + epub.NAMESPACES["EPUB"] + "}type"


def _create_book(with_pagebreaks):
    book = epub.EpubBook()
    book.set_identifier("page-list-regression")
    book.set_title("Page navigation test")
    book.set_language("en")

    copyright_page = epub.EpubHtml(uid="copyright", file_name="copyright.xhtml", title="Copyright")
    copyright_marker = '<span id="page-ii" epub:type="pagebreak">ii</span>' if with_pagebreaks else ""
    copyright_page.set_content(
        '<section id="copyright" epub:type="copyright-page"><h1>Copyright</h1>'
        f"{copyright_marker}<p>Synthetic copyright notice.</p></section>"
    )

    chapter = epub.EpubHtml(uid="chapter", file_name="text/chapter.xhtml", title="Chapter")
    chapter_markers = (
        '<span id="page-1" epub:type="pagebreak other" aria-label="Ignored">1</span>'
        '<span id="page-2" epub:type="other\tpagebreak" aria-label="2"></span>'
        '<div id="page-3" epub:type="other\npagebreak\ranother"><h2>3</h2></div>'
        '<span id="page-4" epub:type=" pagebreak "></span>'
        '<span epub:type="pagebreak">No target ID</span>'
        if with_pagebreaks
        else ""
    )
    chapter.set_content(
        '<section id="chapter" epub:type="chapter"><h1>Chapter</h1>'
        f"{chapter_markers}<p>Keep this chapter text.</p>"
        '<aside id="note" epub:type="footnote"><p>Keep this note.</p></aside>'
        '<span id="near-match" epub:type="pagebreak-extra">Not a page</span></section>'
    )

    book.add_item(copyright_page)
    book.add_item(chapter)
    book.add_item(epub.EpubNav())
    book.toc = (copyright_page, chapter)
    book.spine = ["nav", copyright_page, chapter]
    book.guide = [{"href": "text/chapter.xhtml", "title": "Start", "type": "text"}]
    return book


def _write_book(book):
    output = io.BytesIO()
    epub.write_epub(output, book)
    output.seek(0)
    return output


def _nav_links(nav, nav_type):
    return [(a.get("href"), a.text) for a in nav.findall(f'.//{XHTML}nav[@{EPUB_TYPE}="{nav_type}"]//{XHTML}a')]


@pytest.mark.parametrize("with_pagebreaks", [True, False])
def test_page_list_survives_write_read_write(with_pagebreaks):
    original = _write_book(_create_book(with_pagebreaks))
    restored = epub.read_epub(original)
    rewritten = _write_book(restored)
    expected_pages = (
        [
            ("copyright.xhtml#page-ii", "ii"),
            ("text/chapter.xhtml#page-1", "1"),
            ("text/chapter.xhtml#page-2", "2"),
            ("text/chapter.xhtml#page-3", "3"),
            ("text/chapter.xhtml#page-4", "page-4"),
        ]
        if with_pagebreaks
        else []
    )

    with zipfile.ZipFile(original) as first, zipfile.ZipFile(rewritten) as second:
        for archive in (first, second):
            nav = etree.fromstring(archive.read("EPUB/nav.xhtml"))
            assert _nav_links(nav, "page-list") == expected_pages
            page_lists = nav.findall(f'.//{XHTML}nav[@{EPUB_TYPE}="page-list"]')
            assert len(page_lists) == (1 if with_pagebreaks else 0)
            assert _nav_links(nav, "toc") == [("copyright.xhtml", "Copyright"), ("text/chapter.xhtml", "Chapter")]
            assert _nav_links(nav, "landmarks") == [("text/chapter.xhtml", "Start")]

        for filename in ("copyright.xhtml", "text/chapter.xhtml"):
            parser = etree.XMLParser(remove_blank_text=True)
            first_body = etree.fromstring(first.read(f"EPUB/{filename}"), parser).find(f"{XHTML}body")
            second_body = etree.fromstring(second.read(f"EPUB/{filename}"), parser).find(f"{XHTML}body")
            assert first_body is not None
            assert second_body is not None
            # Ignore serializer indentation, but preserve content, semantics, IDs and labels.
            assert etree.tostring(second_body) == etree.tostring(first_body)

    assert restored.spine == [("nav", "yes"), ("copyright", "yes"), ("chapter", "yes")]
