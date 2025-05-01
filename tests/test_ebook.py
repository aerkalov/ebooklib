import io
import logging
import os
import zipfile
from pathlib import Path

import ebooklib
import pytest
from ebooklib import epub
from ebooklib.plugins import booktype, sourcecode, standard
from ebooklib.utils import parse_html_string, parse_string

logger = logging.getLogger(__name__)


@pytest.mark.usefixtures("session_temp_dir")
class TestEbook:
    def _create_basic_book(self, ncx=True):
        book = epub.EpubBook()

        book.set_identifier("test123456")
        book.set_title("Test book")
        book.set_language("en")
        book.add_author("Test Author")
        book.set_cover("image.jpg", b"fake image data")

        doc1 = epub.EpubHtml(uid="chap_1", file_name="test.xhtml")
        doc1.set_content(
            """<body><h1>Title</h1><p>lorum ipsum.<a epub:type="noteref" href="#fn01">1</a></p>
                 <aside epub:type="footnote" id="fn01">
                     <p>These have been corrected in this EPUB3 edition.</p>
                 </aside>
            </body>"""
        )

        doc2 = epub.EpubHtml(uid="chap_2", file_name="test2.xhtml")
        doc2.set_content(
            """"<body><h1>Title2</h1><p>lorum ipsum.<a epub:type="noteref" href="#en01">1</a></p>
                  <aside epub:type="endnote">
                      <p>These have been corrected in this EPUB3 edition.</p>
                  </aside>
            </body>"""
        )

        css1 = epub.EpubItem(
            uid="style",
            file_name="style.css",
            media_type="text/css",
            content="BODY { color: black; }",
        )
        book.add_item(css1)

        book.add_item(doc1)
        book.add_item(doc2)

        book.toc = (
            doc1,
            (epub.Section("Section"), (doc2,)),
        )

        if ncx:
            book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = ["nav", doc1, doc2]

        return book

    def _test_basic_book(self, book):
        assert len(book.toc) == 2
        assert type(book.toc[0]) is epub.Link
        assert type(book.toc[1]) is type(tuple())
        assert type(book.toc[1][0]) is epub.Section
        assert type(book.toc[1][1]) is type(list())
        assert book.spine == [("nav", "yes"), ("chap_1", "yes"), ("chap_2", "yes")]

        assert book.get_item_with_id("chap_1") is not None
        assert book.get_item_with_id("style") is not None
        assert book.get_item_with_href("test.xhtml") is not None
        assert book.get_item_with_href("style.css") is not None
        assert len(list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))) == 4
        assert len(list(book.get_items_of_type(ebooklib.ITEM_NAVIGATION))) == 1
        assert len(list(book.get_items_of_type(ebooklib.ITEM_STYLE))) == 1
        assert len(list(book.get_items_of_type(ebooklib.ITEM_COVER))) == 1

        assert book.get_metadata("DC", "title") == [("Test book", {})]
        assert book.get_metadata("DC", "identifier") == [("test123456", {"id": "id"})]
        assert book.get_metadata("DC", "language") == [("en", {})]

    def test_basic_bytes(self):
        book = self._create_basic_book()

        # Write to
        f = io.BytesIO()
        epub.write_epub(f, book, {})
        f.seek(0)

        self._test_basic_book(epub.read_epub(f))

    def test_basic_file(self, session_temp_dir):
        book = self._create_basic_book()

        epub.write_epub(session_temp_dir / "test_basic.epub", book, {})

        self._test_basic_book(epub.read_epub(session_temp_dir / "test_basic.epub"))

    def test_basic_read_options(self):
        book = self._create_basic_book()
        book.toc = []

        # Write to
        f = io.BytesIO()
        epub.write_epub(f, book)
        f.seek(0)

        bk = epub.read_epub(f, {"ignore_ncx": False})
        assert type(bk.toc) is epub.Link

        bk = epub.read_epub(f, {"ignore_ncx": True})
        assert len(bk.toc) == 0

    def test_basic_file_raise_exceptions(self):
        book = self._create_basic_book()

        class FakeFile:
            def write(self, content):
                raise IOError

            def writestr(self, filename, content, compress_type):
                raise IOError

            def close(self):
                pass

        with pytest.raises(IOError):
            epub.write_epub(FakeFile(), book, {"raise_exceptions": True})

        assert epub.write_epub(FakeFile(), book, {"raise_exceptions": False}) is False

    def test_basic_file_save_options(self, session_temp_dir):
        book = self._create_basic_book()
        book.guide = [{"href": "test.xhtml", "title": "Introduction", "type": "bodymatter"}]
        book.set_direction("ltr")

        epub.write_epub(
            session_temp_dir / "test_basic_on.epub",
            book,
            {
                "epub2_guide": True,
                "epub3_landmark": True,
                "epub3_pages": True,
                "landmark_title": "My Guide",
                "pages_title": "My Pages",
                "spine_direction": True,
                "package_direction": True,
                "play_order": {"enabled": True, "start_from": 1},
            },
        )
        epub.write_epub(
            session_temp_dir / "test_basic_off.epub",
            book,
            {
                "epub2_guide": False,
                "epub3_landmark": False,
                "epub3_pages": False,
                "spine_direction": False,
                "package_direction": False,
            },
        )

        # Everything turned off
        zf_off = zipfile.ZipFile(
            session_temp_dir / "test_basic_off.epub",
            "r",
            compression=zipfile.ZIP_DEFLATED,
            allowZip64=True,
        )
        content_off = parse_string(zf_off.read("EPUB/content.opf"))
        nav_off = parse_string(zf_off.read("EPUB/nav.xhtml"))
        toc_off = parse_string(zf_off.read("EPUB/toc.ncx"))

        assert content_off.find("{%s}%s" % (epub.NAMESPACES["OPF"], "guide")) is None
        landmarks = nav_off.find(
            './/{%s}nav[@{%s}type="landmarks"]' % (epub.NAMESPACES["XHTML"], epub.NAMESPACES["EPUB"])
        )
        assert landmarks is None

        page_list = nav_off.find(
            './/{%s}nav[@{%s}type="page-list"]' % (epub.NAMESPACES["XHTML"], epub.NAMESPACES["EPUB"])
        )
        assert page_list is None
        assert content_off.find(".//{%s}spine" % epub.NAMESPACES["OPF"]).get("page-progression-direction") is None
        assert content_off.getroot().get("dir") is None

        nav_points = toc_off.findall(".//{%s}navPoint" % epub.NAMESPACES["DAISY"])
        assert len(nav_points) > 0
        for n, nav_point in enumerate(nav_points, 1):
            assert "playOrder" not in nav_point.attrib

        zf_off.close()

        # Everything turned onn
        zf_on = zipfile.ZipFile(
            session_temp_dir / "test_basic_on.epub",
            "r",
            compression=zipfile.ZIP_DEFLATED,
            allowZip64=True,
        )
        content_on = parse_string(zf_on.read("EPUB/content.opf"))
        nav_on = parse_string(zf_on.read("EPUB/nav.xhtml"))
        toc_on = parse_string(zf_on.read("EPUB/toc.ncx"))
        guide = content_on.find("{%s}%s" % (epub.NAMESPACES["OPF"], "guide"))
        references = list(guide)

        assert guide is not None
        assert len(references) == 1
        assert references[0] is not None
        assert references[0].get("href") == "test.xhtml"
        assert references[0].get("title") == "Introduction"
        assert references[0].get("type") == "bodymatter"

        landmarks = nav_on.find(
            './/{%s}nav[@{%s}type="landmarks"]' % (epub.NAMESPACES["XHTML"], epub.NAMESPACES["EPUB"])
        )
        assert landmarks is not None
        assert landmarks.find(".//{%s}h2" % epub.NAMESPACES["XHTML"]).text == "My Guide"

        page_list = nav_on.find(
            './/{%s}nav[@{%s}type="page-list"]' % (epub.NAMESPACES["XHTML"], epub.NAMESPACES["EPUB"])
        )
        assert page_list is not None
        assert page_list.find(".//{%s}h2" % epub.NAMESPACES["XHTML"]).text == "My Pages"

        assert (
            page_list.find(".//{%s}ol" % epub.NAMESPACES["XHTML"])
            .find(".//{%s}li" % epub.NAMESPACES["XHTML"])
            .find(".//{%s}a" % epub.NAMESPACES["XHTML"])
            .get("href")
            == "test.xhtml#fn01"
        )
        assert (
            page_list.find(".//{%s}ol" % epub.NAMESPACES["XHTML"])
            .find(".//{%s}li" % epub.NAMESPACES["XHTML"])
            .find(".//{%s}a" % epub.NAMESPACES["XHTML"])
            .text
            == "fn01"
        )

        assert content_on.find(".//{%s}spine" % epub.NAMESPACES["OPF"]).get("page-progression-direction") == "ltr"

        assert content_on.getroot().get("dir") == "ltr"

        nav_points = toc_on.findall(".//{%s}navPoint" % epub.NAMESPACES["DAISY"])
        assert len(nav_points) > 0
        for n, nav_point in enumerate(nav_points, 1):
            assert "playOrder" in nav_point.attrib
            assert nav_point.get("playOrder") == str(n)

        zf_on.close()

    def test_syntax_plugin(self):
        book = self._create_basic_book()

        doc1 = epub.EpubHtml(uid="chap_syntax", file_name="syntax.xhtml")
        doc1.set_content(
            "<body><h1>Title</h1><p>Wrong<p>Correct <a href='document.xhtml'"
            " onclick='javascript:something();'>link</a></p></body>"
        )
        book.add_item(doc1)

        # create epub file
        f = io.BytesIO()
        epub.write_epub(f, book, {"plugins": [standard.SyntaxPlugin()]})
        f.seek(0)

        book2 = epub.read_epub(f)

        chapter1 = book2.get_item_with_id("chap_syntax")
        html_tree = parse_html_string(chapter1.get_content())
        body = html_tree.find("body")
        link = body.xpath(".//a")

        assert len(link) == 1
        # Make sure plugin erases unwanted attributes
        assert link[0].attrib.get("onclick") is None

    def test_booktype_plugin(self):
        book = self._create_basic_book()

        doc1 = epub.EpubHtml(uid="chap_syntax", file_name="syntax.xhtml")
        doc1.set_content(
            """<body><h1>Title</h1><p>Wrong<p>Correct <a name="test01" href="../test01" """
            """>link</a><a name="test02"href="test02#something">test 02 link</a></p>"""
            """<p><span id="InsertNoteID_1_marker1" class="InsertNoteMarker"><sup><a href="#InsertNoteID_1">"""
            """1</a></sup>"""
            """</span></p><p><ol id="InsertNote_NoteList"><li id="InsertNoteID_1">prvi footnote """
            """<span id="InsertNoteID_1_LinkBacks"><sup>"""
            """<a href="#InsertNoteID_1_marker1">^</a></sup></span></li>"""
            """</ol></p>"""
            """</body>"""
        )
        book.add_item(doc1)

        # create epub file
        f = io.BytesIO()
        epub.write_epub(
            f,
            book,
            {
                "plugins": [
                    booktype.BooktypeLinks(book),
                    booktype.BooktypeFootnotes(book),
                ]
            },
        )
        f.seek(0)

        book2 = epub.read_epub(f)

        chapter1 = book2.get_item_with_id("chap_syntax")
        html_tree = parse_html_string(chapter1.get_content())
        body = html_tree.find("body")

        link01 = body.xpath(".//a[@id='test01']")[0]
        link02 = body.xpath(".//a[@id='test02']")[0]

        assert link01.attrib.get("href") == "../test01.xhtml"
        assert link02.attrib.get("href") == "test02.xhtml#something"

        link_noteref = body.xpath(".//a[@href='#InsertNoteID_1']")[0]

        assert link_noteref.attrib.get("href") == "#InsertNoteID_1"
        assert link_noteref.text == "1"

        aside = body.xpath(".//aside[@id='InsertNoteID_1']")[0]
        assert aside.find("p").text == "prvi footnote "

    def test_sourcecode_plugin(self):
        book = self._create_basic_book()

        doc1 = epub.EpubHtml(uid="chap_syntax", file_name="syntax.xhtml")
        doc1.set_content(
            "<body><h1>Title</h1><p>Wrong</p><pre class='source-python'>print('Hello, world!')</pre></body>"
        )
        book.add_item(doc1)

        # create epub file
        f = io.BytesIO()
        epub.write_epub(f, book, {"plugins": [sourcecode.SourceHighlighter()]})
        f.seek(0)

        book2 = epub.read_epub(f)

        chapter1 = book2.get_item_with_id("chap_syntax")
        html_tree = parse_html_string(chapter1.get_content())

        body = html_tree.find("body")
        highlight_div = body.xpath(".//div[@class='highlight']")

        assert len(highlight_div) == 1

    def _test_metadata(self, book):
        assert book.get_metadata("DC", "subject") == [("Fiction", None)]
        assert book.get_metadata("DC", "contributor") == [("Editor", {"role": "edt"})]
        assert book.get_metadata(None, "meta") == [
            ("", {"name": "cover", "content": "cover-img"}),
            ("", {"name": "key", "content": "value"}),
            ("", {"name": "key2", "content": "value2"}),
        ]

    def test_epubbook_add_metadata(self):
        book = self._create_basic_book()

        book.add_metadata("DC", "subject", "Fiction")
        book.add_metadata("DC", "contributor", "Editor", {"role": "edt"})
        book.add_metadata(None, "meta", "", {"name": "key", "content": "value"})
        book.add_metadata(None, "meta", "", {"name": "key2", "content": "value2"})

        self._test_metadata(book)

    def _test_epubbook(self, name):
        # TODO:
        # - add other roles here besides creator
        book = epub.read_epub(name)

        assert book.get_metadata("DC", "identifier") == [("sample123456", {"id": "id"})]
        assert book.uid == "sample123456"

        assert book.get_metadata("DC", "title") == [("Sample book", {})]

        assert book.get_metadata("DC", "language") == [("en", {})]
        assert book.language == "en"

        assert book.get_metadata("DC", "creator") == [("Aleksandar Erkalovic", {"id": "creator"})]

        assert len(list(book.get_items())) == 6

    def test_epubbook_read_epub_as_filepath(self):
        self._test_epubbook(Path(__file__).parent / "resources" / "test01.epub")

    def test_epubbook_read_epub_as_string(self):
        self._test_epubbook(os.path.join(os.path.dirname(__file__), "resources", "test01.epub"))

    def test_epubbook_read_epub_as_bytes(self):
        self._test_epubbook(io.BytesIO((Path(__file__).parent / "resources" / "test01.epub").open("rb").read()))
