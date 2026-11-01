import io
import logging
import os
import zipfile
from pathlib import Path
from typing import cast

import pytest
from lxml import etree

import ebooklib
from ebooklib import epub
from ebooklib.plugins import booktype, sourcecode, standard
from ebooklib.utils import parse_html_string, parse_string

logger = logging.getLogger(__name__)


def xpath_elements(node, expression: str) -> "list[etree._Element]":
    """Run an XPath query and return the result as a list of elements (typed helper)."""
    assert node is not None
    return cast("list[etree._Element]", node.xpath(expression))


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
            """<body><h1>Title</h1><span id="page1" epub:type="pagebreak">1</span>
                 <p>lorum ipsum.<a epub:type="noteref" href="#fn01">1</a></p>
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
        assert type(book.toc[1]) is tuple
        assert type(book.toc[1][0]) is epub.Section
        assert type(book.toc[1][1]) is list
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

        epub.write_epub(os.path.join(str(session_temp_dir), "test_basic.epub"), book, {})

        self._test_basic_book(epub.read_epub(os.path.join(str(session_temp_dir), "test_basic.epub")))

    def test_basic_read_options(self):
        book = self._create_basic_book()
        book.toc = []

        # Write to
        f = io.BytesIO()
        epub.write_epub(f, book)
        f.seek(0)

        bk = epub.read_epub(f, {"ignore_ncx": False})
        assert bk.toc == []

        bk = epub.read_epub(f, {"ignore_ncx": True})
        assert len(bk.toc) == 0

    def test_basic_file_raise_exceptions(self):
        book = self._create_basic_book()

        class FakeFile:
            def write(self, content):
                raise OSError

            def writestr(self, filename, content, compress_type):
                raise OSError

            def close(self):
                pass

            def tell(self):
                return 0

            def seek(self, offset, whence=0):
                return 0

        with pytest.raises(IOError):
            epub.write_epub(FakeFile(), book, {"raise_exceptions": True})

        assert epub.write_epub(FakeFile(), book, {"raise_exceptions": False}) is False

    def test_basic_file_save_options(self, session_temp_dir):
        book = self._create_basic_book()
        book.guide = [{"href": "test.xhtml", "title": "Introduction", "type": "bodymatter"}]
        book.set_direction("ltr")

        epub.write_epub(
            os.path.join(str(session_temp_dir), "test_basic_on.epub"),
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
            os.path.join(str(session_temp_dir), "test_basic_off.epub"),
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
            os.path.join(str(session_temp_dir), "test_basic_off.epub"),
            "r",
            compression=zipfile.ZIP_DEFLATED,
            allowZip64=True,
        )
        content_off = parse_string(zf_off.read("EPUB/content.opf"))
        nav_off = parse_string(zf_off.read("EPUB/nav.xhtml"))
        toc_off = parse_string(zf_off.read("EPUB/toc.ncx"))

        assert content_off.find(f"{{{epub.NAMESPACES['OPF']}}}guide") is None
        landmarks = nav_off.find(
            f'.//{{{epub.NAMESPACES["XHTML"]}}}nav[@{{{epub.NAMESPACES["EPUB"]}}}type="landmarks"]'
        )
        assert landmarks is None

        page_list = nav_off.find(
            f'.//{{{epub.NAMESPACES["XHTML"]}}}nav[@{{{epub.NAMESPACES["EPUB"]}}}type="page-list"]'
        )
        assert page_list is None
        spine_off = content_off.find(f".//{{{epub.NAMESPACES['OPF']}}}spine")
        assert spine_off is not None
        assert spine_off.get("page-progression-direction") is None
        assert content_off.getroot().get("dir") is None

        nav_points = toc_off.findall(f".//{{{epub.NAMESPACES['DAISY']}}}navPoint")
        assert len(nav_points) > 0
        for _n, nav_point in enumerate(nav_points, 1):
            assert "playOrder" not in nav_point.attrib

        zf_off.close()

        # Everything turned onn
        zf_on = zipfile.ZipFile(
            os.path.join(str(session_temp_dir), "test_basic_on.epub"),
            "r",
            compression=zipfile.ZIP_DEFLATED,
            allowZip64=True,
        )
        content_on = parse_string(zf_on.read("EPUB/content.opf"))
        nav_on = parse_string(zf_on.read("EPUB/nav.xhtml"))
        toc_on = parse_string(zf_on.read("EPUB/toc.ncx"))
        guide = content_on.find(f"{{{epub.NAMESPACES['OPF']}}}guide")
        print("\n\n\n\n\n", zf_on.read("EPUB/nav.xhtml"), "\n\n\n\n\n")

        assert guide is not None
        references = list(guide)
        assert len(references) == 1
        assert references[0] is not None
        assert references[0].get("href") == "test.xhtml"
        assert references[0].get("title") == "Introduction"
        assert references[0].get("type") == "bodymatter"

        landmarks = nav_on.find(f'.//{{{epub.NAMESPACES["XHTML"]}}}nav[@{{{epub.NAMESPACES["EPUB"]}}}type="landmarks"]')
        assert landmarks is not None
        landmarks_title = landmarks.find(f".//{{{epub.NAMESPACES['XHTML']}}}h2")
        assert landmarks_title is not None
        assert landmarks_title.text == "My Guide"

        page_list = nav_on.find(f'.//{{{epub.NAMESPACES["XHTML"]}}}nav[@{{{epub.NAMESPACES["EPUB"]}}}type="page-list"]')
        assert page_list is not None
        page_list_title = page_list.find(f".//{{{epub.NAMESPACES['XHTML']}}}h2")
        assert page_list_title is not None
        assert page_list_title.text == "My Pages"

        pages_ol = page_list.find(f".//{{{epub.NAMESPACES['XHTML']}}}ol")
        assert pages_ol is not None
        assert len(pages_ol.findall(f"{{{epub.NAMESPACES['XHTML']}}}li")) == 1
        pages_li = pages_ol.find(f".//{{{epub.NAMESPACES['XHTML']}}}li")
        assert pages_li is not None
        pages_a = pages_li.find(f".//{{{epub.NAMESPACES['XHTML']}}}a")
        assert pages_a is not None
        assert pages_a.get("href") == "test.xhtml#page1"
        assert pages_a.text == "1"

        spine_on = content_on.find(f".//{{{epub.NAMESPACES['OPF']}}}spine")
        assert spine_on is not None
        assert spine_on.get("page-progression-direction") == "ltr"

        assert content_on.getroot().get("dir") == "ltr"

        nav_points = toc_on.findall(f".//{{{epub.NAMESPACES['DAISY']}}}navPoint")
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
        assert chapter1 is not None
        html_tree = parse_html_string(chapter1.get_content())
        body = html_tree.find("body")
        link = xpath_elements(body, ".//a")

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
        assert chapter1 is not None
        html_tree = parse_html_string(chapter1.get_content())
        body = html_tree.find("body")

        link01 = xpath_elements(body, ".//a[@id='test01']")[0]
        link02 = xpath_elements(body, ".//a[@id='test02']")[0]

        assert link01.attrib.get("href") == "../test01.xhtml"
        assert link02.attrib.get("href") == "test02.xhtml#something"

        link_noteref = xpath_elements(body, ".//a[@href='#InsertNoteID_1']")[0]

        assert link_noteref.attrib.get("href") == "#InsertNoteID_1"
        assert link_noteref.text == "1"

        aside = xpath_elements(body, ".//aside[@id='InsertNoteID_1']")[0]
        aside_p = aside.find("p")
        assert aside_p is not None
        assert aside_p.text == "prvi footnote "

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
        assert chapter1 is not None
        html_tree = parse_html_string(chapter1.get_content())

        body = html_tree.find("body")
        highlight_div = xpath_elements(body, ".//div[@class='highlight']")

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

    def test_epubbook_multiple_authors_have_unique_ids(self):
        book = epub.EpubBook()

        book.add_author("First Author")
        book.add_author("Second Author")
        book.add_author("Third Author", uid="third")

        ids = [others["id"] for _, others in book.get_metadata("DC", "creator")]

        assert ids == ["creator", "creator_1", "third"]
        assert len(set(ids)) == len(ids)

    @pytest.mark.parametrize("namespace", [None, "custom", "urn:example:metadata", "DC", "OPF"])
    def test_epubbook_missing_metadata(self, namespace):
        book = epub.EpubBook()
        namespaces = set(book.metadata)

        assert book.get_metadata(namespace, "missing") == []
        assert set(book.metadata) == namespaces

        book.add_metadata(namespace, "missing", "value")
        assert book.get_metadata(namespace, "missing") == [("value", None)]

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


def test_cover_manifest_identity_is_preserved():
    reader = epub.EpubReader(io.BytesIO())
    reader.container = parse_string(
        b'<package xmlns="http://www.idpf.org/2007/opf"><manifest>'
        b'<item id="front-cover" href="Text/front%20cover.xhtml" '
        b'media-type="application/xhtml+xml" properties="cover"/>'
        b"</manifest></package>"
    )
    archive = io.BytesIO()
    content = b"<html><body><p>Cover</p></body></html>"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("Text/front cover.xhtml", content)
    archive.seek(0)
    with zipfile.ZipFile(archive) as zf:
        reader.zf = zf
        reader._load_manifest()

    cover = reader.book.get_item_with_id("front-cover")
    assert isinstance(cover, epub.EpubCoverHtml)
    assert reader.book.get_item_with_href("Text/front cover.xhtml") is cover
    assert cover.media_type == "application/xhtml+xml"
    assert cover.content == content


@pytest.mark.parametrize(
    "item_class, prefix",
    [(epub.EpubHtml, "chapter"), (epub.EpubImage, "image"), (epub.EpubItem, "static")],
)
def test_generated_item_ids_skip_existing_ids(item_class, prefix):
    book = epub.EpubBook()
    first = book.add_item(epub.EpubItem(uid=f"{prefix}_0", file_name="first.dat"))
    second = book.add_item(epub.EpubItem(uid=f"{prefix}_1", file_name="second.dat"))
    generated = book.add_item(item_class(file_name="generated.dat"))
    following = book.add_item(item_class(file_name="following.dat"))

    assert generated.id == f"{prefix}_2"
    assert following.id == f"{prefix}_3"
    assert book.get_item_with_id(f"{prefix}_0") is first
    assert book.get_item_with_id(f"{prefix}_1") is second
    assert book.get_item_with_id(generated.id) is generated


def test_generated_ids_do_not_collide_after_read_epub():
    """Items without an ID added to a loaded book must not reuse IDs from the file."""
    book = epub.read_epub(Path(__file__).parent / "resources" / "test01.epub")
    existing_ids = [item.get_id() for item in book.get_items()]
    assert len(existing_ids) == len(set(existing_ids))

    added = [book.add_item(epub.EpubHtml(file_name=f"extra_{n}.xhtml")) for n in range(3)]

    ids = [item.get_id() for item in book.get_items()]
    assert len(ids) == len(set(ids))
    for item in added:
        assert item.id
        assert book.get_item_with_id(item.id) is item


def test_explicit_item_ids_are_not_checked_for_uniqueness():
    """Documented behaviour: only generated IDs avoid collisions, explicit IDs are used as given."""
    book = epub.EpubBook()
    first = book.add_item(epub.EpubItem(uid="same", file_name="a.dat"))
    second = book.add_item(epub.EpubItem(uid="same", file_name="b.dat"))

    assert first.id == second.id == "same"
    assert book.get_item_with_id("same") is first


def test_empty_ncx_toc_survives_round_trip():
    book = epub.EpubBook()
    book.set_title("Empty table of contents")
    chapter = epub.EpubHtml(file_name="chapter.xhtml", content="<p>Chapter</p>")
    book.add_item(chapter)
    book.add_item(epub.EpubNcx())
    book.spine = [chapter]
    archive = io.BytesIO()
    epub.write_epub(archive, book)
    archive.seek(0)

    restored = epub.read_epub(archive)
    assert restored.toc == []
    epub.write_epub(io.BytesIO(), restored)


def _ncx_book(ncx: bytes, nav_entries: bool = False) -> io.BytesIO:
    """Build an EPUB whose NCX is replaced by ``ncx``, optionally with a populated EPUB 3 nav."""
    book = epub.EpubBook()
    book.set_title("Replaced NCX")
    chapter = epub.EpubHtml(title="Chapter", file_name="chapter.xhtml", content="<p>Chapter</p>")
    book.add_item(chapter)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.toc = [chapter] if nav_entries else []
    book.spine = ["nav", chapter]
    source = io.BytesIO()
    epub.write_epub(source, book)
    source.seek(0)

    output = io.BytesIO()
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(output, "w") as target:
        for entry in src.infolist():
            data = src.read(entry.filename)
            if entry.filename.endswith(".ncx"):
                data = ncx
            target.writestr(entry, data)
    output.seek(0)
    return output


_NCX = (
    b'<?xml version="1.0" encoding="utf-8"?><ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">'
    b"<head/><docTitle><text>t</text></docTitle>%s</ncx>"
)


@pytest.mark.parametrize(
    "navmap",
    [b"<navMap/>", b"", b"<navMap><navPoint id='a'><navLabel/><content src='chapter.xhtml'/></navPoint></navMap>"],
    ids=["empty-navmap", "missing-navmap", "navlabel-without-text"],
)
def test_malformed_or_empty_ncx_gives_list_toc_that_can_be_written(navmap):
    """An NCX without entries or with a broken navLabel must not break reading or writing."""
    restored = epub.read_epub(_ncx_book(_NCX % navmap), {"ignore_ncx": False})

    assert isinstance(restored.toc, list)
    epub.write_epub(io.BytesIO(), restored)


def test_empty_ncx_falls_back_to_nav_document_toc():
    """With an empty NCX the table of contents comes from the EPUB 3 nav document."""
    restored = epub.read_epub(_ncx_book(_NCX % b"<navMap/>", nav_entries=True), {"ignore_ncx": False})

    assert [(link.href, link.title) for link in restored.toc] == [("chapter.xhtml", "Chapter")]
