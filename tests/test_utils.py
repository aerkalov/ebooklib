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
