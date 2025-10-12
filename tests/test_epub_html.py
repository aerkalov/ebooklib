import logging

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

        assert len(html_tree.find("head").getchildren()) == 0
        assert len(html_tree.find("body").getchildren()) == 2
        assert len(html_tree.xpath("//h1[contains(text(), 'Title')]")) == 1

        doc1.title = "This is my title"
        html_tree = parse_html_string(doc1.get_content())

        assert len(html_tree.find("head").getchildren()) == 1
        assert len(html_tree.xpath("//title[contains(text(), 'This is my title')]")) == 1

        doc1.set_language("de")
        html_tree = parse_html_string(doc1.get_content())
        assert html_tree.attrib["lang"] == "de"
