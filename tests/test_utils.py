import os

import pytest

from ebooklib import epub, utils


class TestEpubItemInitialization:
    def _create_basic_book(self):
        book = epub.EpubBook()

        book.set_identifier("test123456")
        book.set_title("Test book")
        book.set_language("en")
        book.add_author("Test Author")

        doc1 = epub.EpubHtml(uid="chap_1", file_name="test.xhtml")

        doc2 = epub.EpubHtml(uid="chap_2", file_name="test2.xhtml")

        book.add_item(doc1)
        book.add_item(doc2)

        book.toc = (
            doc1,
            doc2,
        )
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = ["nav", doc1, doc2]

        return book

    def test_pagebreak(self):
        pb = utils.create_pagebreak("page1", label="label", html=True)

        assert pb == (
            '<span xmlns:epub="http://www.idpf.org/2007/ops" epub:type="pagebreak"'
            ' title="page1" id="page1">label</span>'
        )


class TestGetPages:
    @pytest.mark.parametrize(
        "epub_type",
        [
            "pagebreak",
            " pagebreak ",
            "pagebreak other",
            "other pagebreak",
            "other pagebreak another",
            "other\tpagebreak\nanother",
            "other\rpagebreak",
            "pagebreak pagebreak",
        ],
    )
    def test_accepts_pagebreak_token(self, epub_type):
        item = epub.EpubHtml(file_name="chapter.xhtml")
        item.set_content(f'<span id="page1" epub:type="{epub_type}">1</span>')

        assert utils.get_pages(item) == [("chapter.xhtml", "page1", "1")]

    @pytest.mark.parametrize(
        "epub_type",
        [
            None,
            "",
            " \t\r\n",
            "copyright-page",
            "chapter",
            "footnote",
            "not-pagebreak",
            "pagebreak-extra",
            "other:pagebreak",
            "Pagebreak",
            "other\u00a0pagebreak",
            "pagebreak\u2003other",
        ],
    )
    def test_ignores_other_semantics(self, epub_type):
        item = epub.EpubHtml(file_name="chapter.xhtml")
        attribute = f' epub:type="{epub_type}"' if epub_type is not None else ""
        item.set_content(f'<span id="not-a-page"{attribute}>Not a page</span>')

        assert utils.get_pages(item) == []

    def test_requires_id(self):
        item = epub.EpubHtml(file_name="chapter.xhtml")
        item.set_content('<span epub:type="pagebreak">1</span>')

        assert utils.get_pages(item) == []

    def test_preserves_label_precedence_and_document_order(self):
        item = epub.EpubHtml(file_name="chapter.xhtml")
        item.set_content(
            '<div id="p4" epub:type="pagebreak" aria-label="ARIA"> Text <h1>Heading</h1></div>'
            '<div id="p3" epub:type="pagebreak" aria-label="ARIA"> <h1>Heading</h1></div>'
            '<div id="p2" epub:type="pagebreak"><h2>Heading <span>two</span></h2></div>'
            '<span id="p1" epub:type="pagebreak"></span>'
        )

        assert utils.get_pages(item) == [
            ("chapter.xhtml", "p4", "Text"),
            ("chapter.xhtml", "p3", "ARIA"),
            ("chapter.xhtml", "p2", "Heading two"),
            ("chapter.xhtml", "p1", "p1"),
        ]


class TestDirectory:
    def test_read_within_directory(self, tmp_path):
        (tmp_path / "Text").mkdir()
        (tmp_path / "Text" / "c.xhtml").write_bytes(b"hello")

        directory = utils.Directory(str(tmp_path))

        assert directory.read(os.path.join("Text", "c.xhtml")) == b"hello"

    def test_read_rejects_path_traversal(self, tmp_path):
        # See #359: a crafted (URL-decoded) manifest href must not be allowed
        # to escape the source directory.
        directory = utils.Directory(str(tmp_path))

        with pytest.raises(OSError, match="escapes the source directory"):
            directory.read(os.path.join("..", "..", "etc", "passwd"))

    def test_read_rejects_absolute_path_outside_directory(self, tmp_path):
        directory = utils.Directory(str(tmp_path))

        with pytest.raises(OSError, match="escapes the source directory"):
            directory.read(os.path.join(os.sep, "etc", "passwd"))
