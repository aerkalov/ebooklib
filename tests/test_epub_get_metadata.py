import os

from ebooklib import epub

BASE_DIR = os.path.dirname(__file__)


def _make_book_with_meta(tmp_path):
    book = epub.EpubBook()
    book.set_identifier("ebooklib-test-get-metadata")
    book.set_title("Metadata round trip")
    book.set_language("en")
    book.add_metadata(None, "meta", "textual", {"property": "schema:accessMode"})

    chapter = epub.EpubHtml(title="Chapter", file_name="chapter.xhtml", lang="en")
    chapter.content = "<html><body><p>Content</p></body></html>"
    book.add_item(chapter)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav", chapter]

    path = str(tmp_path / "roundtrip.epub")
    epub.write_epub(path, book, {})
    return path


def test_get_metadata_unknown_namespace_returns_empty():
    # Asking about a namespace that was never written must not raise.
    book = epub.EpubBook()

    assert book.get_metadata("http://example.com/ns", "title") == []
    assert book.get_metadata(None, "meta") == []


def test_get_metadata_after_read_epub(tmp_path):
    # Regression test: read_epub() replaces book.metadata with a dict keyed
    # by namespace URIs, so the None namespace used for package <meta>
    # entries is absent and get_metadata(None, "meta") used to raise
    # KeyError instead of returning the entries.
    book = epub.read_epub(_make_book_with_meta(tmp_path))

    meta = book.get_metadata(None, "meta")
    values = [value for value, _others in meta]
    assert "textual" in values

    # A missing name under an existing convention still returns [].
    assert book.get_metadata(None, "no-such-name") == []
    # An entirely absent namespace also returns [].
    assert book.get_metadata("http://example.com/ns", "meta") == []
