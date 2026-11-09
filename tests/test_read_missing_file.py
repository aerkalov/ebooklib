import zipfile

import pytest

from ebooklib import epub


def _book(tmp_path):
    book = epub.EpubBook()
    book.set_identifier("id")
    book.set_title("Title")
    book.set_language("en")
    chapter = epub.EpubHtml(title="One", file_name="one.xhtml")
    chapter.set_content("<html><body><p>Hello</p></body></html>")
    book.add_item(chapter)
    book.add_item(epub.EpubImage(uid="a", file_name="images/a.png", media_type="image/png", content=b"png"))
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = [chapter]
    path = tmp_path / "book.epub"
    epub.write_epub(str(path), book)
    return path


def test_read_epub_with_a_missing_manifest_file(tmp_path):
    path = _book(tmp_path)
    stripped = tmp_path / "stripped.epub"
    with zipfile.ZipFile(path) as source, zipfile.ZipFile(stripped, "w") as target:
        for item in source.infolist():
            if not item.filename.endswith("images/a.png"):
                target.writestr(item, source.read(item))

    with pytest.warns(UserWarning, match="images/a.png"):
        book = epub.read_epub(str(stripped))

    assert book.get_item_with_href("one.xhtml") is not None
    image = book.get_item_with_href("images/a.png")
    assert image is not None
    assert image.content == b""
