import logging
from typing import cast

import pytest
from lxml import etree

import ebooklib
from ebooklib import epub
from ebooklib.utils import parse_html_string

logger = logging.getLogger(__name__)


class TestEpubHtml:
    def test_init(self):
        doc = epub.EpubHtml()

        assert doc.is_chapter() is True
        assert doc.get_type() == ebooklib.ITEM_DOCUMENT

    def test_language(self):
        doc1 = epub.EpubHtml(lang="en")
        assert doc1.get_language() == "en"

        doc2 = epub.EpubHtml()
        doc2.set_language("es")
        assert doc2.get_language() == "es"

    def test_links(self):
        doc1 = epub.EpubHtml()

        doc1.add_link(href="Styles/styles1.css", rel="stylesheet", type="text/css")
        doc1.add_link(href="Styles/styles2.css", rel="stylesheet", type="text/css")
        assert len(list(doc1.get_links())) == 2

        doc1.add_link(
            rel="alternate",
            type="application/rss+xml",
            title="Feed",
            href="https://www.github.com/feed/",
        )
        assert len(list(doc1.get_links())) == 3

        doc1.add_link(rel="icon", href="https://www.github.com/favicon.ico", sizes="32x32")
        assert len(list(doc1.get_links())) == 4

        doc1.add_link(href="Scripts/script.js", rel="stylesheet", type="text/javascript")
        assert len(list(doc1.get_links())) == 5
        assert "scripted" in doc1.properties

    def test_items(self):
        doc1 = epub.EpubHtml()

        default_css = epub.EpubItem(
            uid="style_default",
            file_name="style/default.css",
            media_type="text/css",
            content="",
        )
        doc1.add_item(default_css)
        assert len(list(doc1.get_links())) == 1

    def test_content_1(self):
        book = epub.EpubBook()

        doc1 = epub.EpubHtml(file_name="test.xhtml")
        doc1.set_content(
            """<html><head><title>This is my title</title>
<style>
  body {background-color: green;}
</style>
<link rel="stylesheet" href="style.css">
<body>
 <h1>Title</h1>
 <p>Paragraph with some</p>
</body>
</html>
"""
        )
        book.add_item(doc1)

        html_tree = parse_html_string(doc1.get_content())

        head = html_tree.find("head")
        body = html_tree.find("body")
        assert head is not None
        assert body is not None
        assert len(head) == 0
        assert len(body) == 2
        assert len(cast("list[etree._Element]", html_tree.xpath("//h1[contains(text(), 'Title')]"))) == 1

        doc1.title = "This is my title"
        html_tree = parse_html_string(doc1.get_content())

        head = html_tree.find("head")
        assert head is not None
        assert len(head) == 1
        assert len(cast("list[etree._Element]", html_tree.xpath("//title[contains(text(), 'This is my title')]"))) == 1

        doc1.set_language("de")
        html_tree = parse_html_string(doc1.get_content())
        assert html_tree.attrib["lang"] == "de"


@pytest.mark.parametrize("content", ["Plain text &amp; symbols", "Before <em>inside</em> after"])
def test_body_text_is_preserved(content):
    book = epub.EpubBook()
    doc = epub.EpubHtml(file_name="chapter.xhtml", content=f"<body>{content}</body>")
    book.add_item(doc)
    expected = parse_html_string(f"<body>{content}</body>").find("body").text_content()

    assert parse_html_string(doc.get_content()).find("body").text_content() == expected
    assert parse_html_string(doc.get_body_content()).find("body").text_content() == expected


@pytest.mark.parametrize("whitespace", ["\n  ", " ", "\t\r\n", "\f"])
def test_whitespace_only_body_text_is_not_copied(whitespace):
    """Indentation before the first element must not change the generated document."""
    book = epub.EpubBook()
    indented = epub.EpubHtml(file_name="a.xhtml", content=f"<body>{whitespace}<p>Hi</p>\n<p>there</p></body>")
    compact = epub.EpubHtml(file_name="b.xhtml", content="<body><p>Hi</p>\n<p>there</p></body>")
    book.add_item(indented)
    book.add_item(compact)

    assert indented.get_content() == compact.get_content()


def test_no_break_space_body_text_is_preserved():
    """U+00A0 is visible content, not HTML whitespace, so it is kept."""
    doc = epub.EpubHtml(file_name="chapter.xhtml", content="<body>\u00a0<p>Hi</p></body>")
    epub.EpubBook().add_item(doc)

    body = parse_html_string(doc.get_content()).find("body")
    assert body is not None
    assert body.text == "\u00a0"
    assert epub.EpubHtml(file_name="n.xhtml", content="<body>\u00a0</body>").get_body_content() != b""


@pytest.mark.parametrize("content", ["<body></body>", "<body>\n  </body>", "<body> \t\r\n</body>"])
def test_whitespace_only_body_without_children_is_empty(content):
    """A body with only whitespace and no child elements yields no body content."""
    doc = epub.EpubHtml(file_name="chapter.xhtml", content=content)
    epub.EpubBook().add_item(doc)

    assert doc.get_body_content() == b""


def test_leading_body_text_keeps_surrounding_whitespace_and_children():
    """Meaningful leading text is preserved together with the following elements."""
    doc = epub.EpubHtml(file_name="chapter.xhtml", content="<body>\n  Before <em>inside</em> after\n<p>End</p></body>")
    epub.EpubBook().add_item(doc)

    body = parse_html_string(doc.get_content()).find("body")
    assert body is not None
    assert (body.text or "").strip() == "Before"
    assert [child.tag for child in body] == ["em", "p"]
    assert (body[0].tail or "").strip() == "after"
    assert b"Before" in doc.get_body_content()
