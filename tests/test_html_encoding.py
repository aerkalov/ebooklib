import zipfile

import pytest
from lxml import etree, html

from ebooklib import epub, utils


@pytest.mark.parametrize(
    "declaration",
    [
        "",
        '<?xml version="1.0"?>',
        '<?xml version="1.0" encoding="utf-8"?>',
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<?xml version="1.0" encoding="iso-8859-1"?>',
    ],
)
@pytest.mark.parametrize("as_bytes", [False, True])
def test_html_encoding_roundtrip(tmp_path, declaration, as_bytes):
    # Unicode has already been decoded. Both inputs use the parser's UTF-8.
    text = (
        declaration + '<html xmlns="http://www.w3.org/1999/xhtml">'
        "<head><title>Input title</title></head><body>"
        '<p id="content">Café 中文 😀 &amp; tea</p></body></html>'
    )
    content = text.encode("utf-8") if as_bytes else text
    assert utils.parse_html_string(content).xpath("//p")[0].text == "Café 中文 😀 & tea"
    book = epub.EpubBook()
    book.set_identifier("synthetic-encoding")
    book.set_title("Synthetic book")
    book.set_language("en")
    chapter = epub.EpubHtml(title="Chapter", file_name="chapter.xhtml")
    chapter.set_content(content)
    style = epub.EpubItem(uid="css", file_name="style.css", media_type="text/css", content="p { color: black; }")
    chapter.add_item(style)
    book.add_item(style)
    book.add_item(chapter)
    book.spine = [chapter]
    book.toc = [chapter]
    book.add_item(epub.EpubNav())
    output = tmp_path / "book.epub"
    assert epub.write_epub(output, book)
    with zipfile.ZipFile(output) as archive:
        written = archive.read("EPUB/chapter.xhtml")
        parsed = utils.parse_html_string(written)
        assert parsed.xpath("//p")[0].text == "Café 中文 😀 & tea"
        assert parsed.xpath("//link/@href") == ["style.css"]
    restored = epub.read_epub(output)
    restored_chapter = restored.get_item_with_href("chapter.xhtml")
    assert restored_chapter is not None
    assert "Café 中文 😀 & tea" in utils.parse_html_string(restored_chapter.get_content()).text_content()
    rewritten = tmp_path / "rewritten.epub"
    assert epub.write_epub(rewritten, restored)
    with zipfile.ZipFile(rewritten) as archive:
        assert utils.parse_html_string(archive.read("EPUB/chapter.xhtml")).xpath("//p")[0].text == "Café 中文 😀 & tea"


@pytest.mark.parametrize("content", ["<p>Café 中文</p>", b"<p>plain bytes</p>"])
def test_fragment_input_remains_supported(content):
    assert len(utils.parse_html_string(content).xpath("//p")) == 1


def test_existing_recovery_for_invalid_unicode_is_unchanged():
    # Do not encode already-supported input before trying lxml's existing path.
    tree = utils.parse_html_string("<p>before\ud800after</p>")
    original = html.document_fromstring("<p>before\ud800after</p>", parser=html.HTMLParser(encoding="utf-8"))
    assert etree.tostring(tree) == etree.tostring(original)


def test_xml_declaration_chapter_does_not_write_empty(tmp_path):
    book = epub.EpubBook()
    book.set_identifier("direct-writer")
    book.set_title("Direct writer")
    book.set_language("en")
    chapter = epub.EpubHtml(title="Chapter", file_name="chapter.xhtml")
    chapter.content = '<?xml version="1.0" encoding="utf-8"?><html><body><p>Keep this body</p></body></html>'
    book.add_item(chapter)
    book.spine = [chapter]
    book.toc = [chapter]
    book.add_item(epub.EpubNav())
    output = tmp_path / "book.epub"
    assert epub.write_epub(output, book)
    with zipfile.ZipFile(output) as archive:
        assert b"Keep this body" in archive.read("EPUB/chapter.xhtml")
