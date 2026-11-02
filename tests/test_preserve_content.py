import datetime
import io
import posixpath
import textwrap
import zipfile
from pathlib import Path
from typing import cast

import pytest
from lxml import etree

from ebooklib import epub

XHTML = "http://www.w3.org/1999/xhtml"
NS = {"x": XHTML, "opf": "http://www.idpf.org/2007/opf", "ncx": "http://www.daisy.org/z3986/2005/ncx/"}
OPTIONS = {"mtime": datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc), "raise_exceptions": True}
ORIGINAL = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" '
    'xml:lang="en" lang="en"><head><title>Original</title>'
    '<meta name="description" content="Synthetic chapter"/>'
    '<link href="../styles/main.css" rel="stylesheet" type="text/css"/>'
    '<style type="text/css">.inline { font-style: italic; }</style></head>'
    '<body id="original-body" class="main"><h1>Original</h1>'
    '<p class="inline" style="color: navy"><span>A</span><span>B</span></p>'
    "<p><span>C</span> <span>D</span></p><p>Café 中文 😀</p></body></html>\n"
).encode()
SECOND = (
    b'<?xml version="1.0" encoding="UTF-8"?>\r\n'
    b'<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en"><head><title>Second</title>'
    b'<link href="../styles/main.css" rel="stylesheet" type="text/css"/></head>\r\n'
    b'<body id="second-body">\r\n<h1>Second</h1><p>Unchanged whitespace. </p>\r\n</body></html>\r\n'
)
CSS = b".main { color: black; } .inline { font-weight: bold; }"


def make_source():
    """Create a complete synthetic input independently of EpubHtml serialization."""
    book = epub.EpubBook()
    book.set_identifier("synthetic-preserve-content")
    book.set_title("Synthetic preservation workflow")
    book.set_language("en")
    book.add_author("Synthetic Author")
    # Generic items write these source documents verbatim on unchanged master too.
    for uid, name, content in [("original", "Text/original.xhtml", ORIGINAL), ("second", "Text/second.xhtml", SECOND)]:
        book.add_item(epub.EpubItem(uid, name, "application/xhtml+xml", content))
    book.add_item(epub.EpubItem("css", "styles/main.css", "text/css", CSS))
    book.set_cover(
        "images/cover.svg",
        b'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">'
        b'<title>Synthetic cover</title><rect width="100" height="100" fill="navy"/></svg>',
    )
    book.guide = [{"href": "cover.xhtml", "type": "cover", "title": "Cover"}]
    book.add_item(epub.EpubNav(title="Contents"))
    book.add_item(epub.EpubNcx())
    book.toc = [
        epub.Link("Text/original.xhtml", "Old original title", "old"),
        epub.Link("Text/second.xhtml", "Second", "s"),
    ]
    book.spine = ["nav", "cover", "original", "second"]
    source = io.BytesIO()
    assert epub.write_epub(source, book, OPTIONS)
    return source.getvalue()


def edit_book(source, preserve=True):
    book = epub.read_epub(io.BytesIO(source))
    # Select only the existing ordinary chapters. Add new fragment chapters afterwards.
    for item in book.get_items():
        if isinstance(item, epub.EpubHtml) and item.is_chapter():
            item.preserve_content = preserve
    added = epub.EpubHtml(uid="added", title="Added chapter", file_name="Text/added.xhtml", lang="en")
    added.content = '<h1 id="added-heading">Added chapter</h1><p>Generated from a fragment.</p>'
    added.add_link(href="../styles/main.css", rel="stylesheet", type="text/css")
    book.add_item(added)
    book.toc = [
        epub.Link("Text/original.xhtml#original-body", "Renamed original", "renamed"),
        added,
        epub.Link("Text/second.xhtml", "Second", "s"),
    ]
    book.spine.insert(3, added)
    return book


def write_bytes(book, options=None):
    output = io.BytesIO()
    assert epub.write_epub(output, book, OPTIONS | (options or {}))
    return output.getvalue()


def assert_workflow(output):
    with zipfile.ZipFile(io.BytesIO(output)) as archive:
        assert archive.read("EPUB/Text/original.xhtml") == ORIGINAL
        assert archive.read("EPUB/Text/second.xhtml") == SECOND
        original = etree.fromstring(archive.read("EPUB/Text/original.xhtml"))
        assert original.xpath("./x:body/@id", namespaces=NS) == ["original-body"]
        spans = cast("list[etree._Element]", original.xpath("./x:body/x:p[1]/x:span", namespaces=NS))
        assert spans[0].tail is None
        spaced = cast("list[etree._Element]", original.xpath("./x:body/x:p[2]/x:span", namespaces=NS))
        assert spaced[0].tail == " "
        assert original.xpath("./x:body/@class", namespaces=NS) == ["main"]
        assert original.xpath("./x:head/x:style/text()", namespaces=NS) == [".inline { font-style: italic; }"]
        assert original.xpath("./x:body/x:p[1]/@style", namespaces=NS) == ["color: navy"]
        added = etree.fromstring(archive.read("EPUB/Text/added.xhtml"))
        assert added.tag == f"{{{XHTML}}}html"
        assert added.xpath("./x:head/x:title/text()", namespaces=NS) == ["Added chapter"]
        assert added.xpath("./x:body/x:h1/@id", namespaces=NS) == ["added-heading"]
        assert added.get("lang") == "en"
        expected = ["Text/original.xhtml#original-body", "Text/added.xhtml", "Text/second.xhtml"]
        nav = etree.fromstring(archive.read("EPUB/nav.xhtml"))
        ncx = etree.fromstring(archive.read("EPUB/toc.ncx"))
        assert nav.xpath("//x:nav[@id='id']//x:a/@href", namespaces=NS) == expected
        assert nav.xpath("//x:nav[@id='id']//x:a/text()", namespaces=NS) == [
            "Renamed original",
            "Added chapter",
            "Second",
        ]
        assert ncx.xpath("//ncx:content/@src", namespaces=NS) == expected
        package = etree.fromstring(archive.read("EPUB/content.opf"))
        assert package.xpath("./opf:spine/opf:itemref/@idref", namespaces=NS) == [
            "nav",
            "cover",
            "original",
            "added",
            "second",
        ]
        cover = etree.fromstring(archive.read("EPUB/cover.xhtml"))
        assert cover.xpath("//x:img/@src", namespaces=NS) == ["images/cover.svg"]
        assert cover.xpath("//x:img/@alt", namespaces=NS) == ["Cover"]
        assert archive.read("EPUB/styles/main.css") == CSS
        # Check every relative resource and document link, including fragment targets.
        for name in archive.namelist():
            if not name.endswith(".xhtml"):
                continue
            tree = etree.fromstring(archive.read(name))
            for link in cast("list[str]", tree.xpath("//@href | //@src")):
                target, _, fragment = link.partition("#")
                target = posixpath.normpath(posixpath.join(posixpath.dirname(name), target)) if target else name
                assert target in archive.namelist(), (name, link)
                if fragment:
                    assert fragment in cast("list[str]", etree.fromstring(archive.read(target)).xpath("//@id"))
    for ignore_ncx in [True, False]:
        restored = epub.read_epub(io.BytesIO(output), {"ignore_ncx": ignore_ncx})
        assert [item.href for item in restored.toc] == expected
        assert restored.spine == [
            ("nav", "yes"),
            ("cover", "no"),
            ("original", "yes"),
            ("added", "yes"),
            ("second", "yes"),
        ]
        chapter = restored.get_item_with_id("original")
        style = restored.get_item_with_id("css")
        assert isinstance(chapter, epub.EpubHtml)
        assert style is not None
        assert chapter.content == ORIGINAL
        assert not chapter.preserve_content
        assert style.content == CSS


def test_toc_edit_preserves_selected_documents():
    assert_workflow(write_bytes(edit_book(make_source())))


def test_tutorial_preservation_example(tmp_path, monkeypatch):
    source = make_source()
    before = epub.read_epub(io.BytesIO(source))
    assert before.get_item_with_href("chapter.xhtml") is None
    expected = [(entry.href, entry.title) for entry in before.toc] + [("added.xhtml", "Added chapter")]
    (tmp_path / "input.epub").write_bytes(source)
    tutorial = Path(__file__).resolve().parents[1] / "docs/tutorial.rst"
    snippet = tutorial.read_text().split("the normal template behavior unless explicitly selected::\n\n", 1)[1]
    snippet = textwrap.dedent(snippet.split("\n\n``EpubHtml", 1)[0])
    monkeypatch.chdir(tmp_path)
    exec(compile(snippet, str(tutorial), "exec"), {"epub": epub})

    output = (tmp_path / "output.epub").read_bytes()
    for ignore_ncx in [True, False]:
        restored = epub.read_epub(io.BytesIO(output), {"ignore_ncx": ignore_ncx})
        assert [(entry.href, entry.title) for entry in restored.toc] == expected
        assert restored.spine[:-1] == before.spine
        added = restored.get_item_with_href("added.xhtml")
        assert isinstance(added, epub.EpubHtml)
        assert restored.spine[-1] == (added.id, "yes")
    with zipfile.ZipFile(io.BytesIO(output)) as archive:
        assert archive.read("EPUB/Text/original.xhtml") == ORIGINAL
        assert archive.read("EPUB/Text/second.xhtml") == SECOND
        added_tree = etree.fromstring(archive.read("EPUB/added.xhtml"))
        assert added_tree.tag == f"{{{XHTML}}}html"
        assert added_tree.xpath("./x:head/x:title/text()", namespaces=NS) == ["Added chapter"]
        ncx = etree.fromstring(archive.read("EPUB/toc.ncx"))
        ids = cast("list[str]", ncx.xpath("//ncx:navPoint/@id", namespaces=NS))
        assert all(ids)
        assert len(ids) == len(set(ids))
        for name in archive.namelist():
            if not name.endswith(".xhtml"):
                continue
            tree = etree.fromstring(archive.read(name))
            for link in cast("list[str]", tree.xpath("//@href | //@src")):
                target, _, fragment = link.partition("#")
                target = posixpath.normpath(posixpath.join(posixpath.dirname(name), target)) if target else name
                assert target in archive.namelist(), (name, link)
                if fragment:
                    assert fragment in cast("list[str]", etree.fromstring(archive.read(target)).xpath("//@id"))


def test_default_still_rebuilds_documents():
    source = make_source()
    with zipfile.ZipFile(io.BytesIO(write_bytes(edit_book(source, False)))) as archive:
        assert archive.read("EPUB/Text/original.xhtml") != ORIGINAL
        tree = etree.fromstring(archive.read("EPUB/Text/original.xhtml"))
        assert tree.xpath("./x:head/x:link", namespaces=NS) == []
        assert tree.xpath("./x:body/@id", namespaces=NS) == []
        spans = cast("list[etree._Element]", tree.xpath("./x:body/x:p[1]/x:span", namespaces=NS))
        assert spans[0].tail is not None


@pytest.mark.parametrize("feature", ["head", "body", "whitespace"])
def test_selected_chapter_retains_original_structure(feature):
    with zipfile.ZipFile(io.BytesIO(write_bytes(edit_book(make_source())))) as archive:
        root = etree.fromstring(archive.read("EPUB/Text/original.xhtml"))
    if feature == "head":
        assert root.xpath("./x:head/x:link/@href", namespaces=NS) == ["../styles/main.css"]
        assert root.xpath("./x:head/x:meta/@content", namespaces=NS) == ["Synthetic chapter"]
    elif feature == "body":
        assert root.xpath("./x:body/@id", namespaces=NS) == ["original-body"]
        assert root.xpath("./x:body/@class", namespaces=NS) == ["main"]
    else:
        spans = cast("list[etree._Element]", root.xpath("./x:body/x:p[1]/x:span", namespaces=NS))
        assert spans[0].tail is None


def test_default_document_properties_still_apply():
    doc = epub.EpubHtml(file_name="default.xhtml", title="Generated", lang="de", direction="rtl", content=ORIGINAL)
    doc.add_link(href="new.css", rel="stylesheet")
    doc.add_meta(name="new", content="value")
    epub.EpubBook().add_item(doc)
    assert not doc.preserve_content
    root = etree.fromstring(doc.get_content())
    assert root.get("lang") == "de"
    assert root.get("dir") == "rtl"
    assert root.xpath("./x:head/x:title/text()", namespaces=NS) == ["Generated"]
    assert root.xpath("./x:head/x:link/@href", namespaces=NS) == ["new.css"]
    assert root.xpath("./x:head/x:meta/@name", namespaces=NS) == ["new"]


@pytest.mark.parametrize("encoding", ["utf-8", "utf-16", "iso-8859-1"])
def test_preserve_bytes_keeps_encoding(encoding):
    text = ORIGINAL.decode("utf-8").replace('encoding="UTF-8"', f'encoding="{encoding}"').replace("中文 😀", "tea")
    content = text.encode(encoding)
    doc = epub.EpubHtml(file_name="encoded.xhtml", title="Encoded", content=content, preserve_content=True)
    book = epub.EpubBook()
    book.add_item(doc)
    book.spine = [doc]
    book.toc = [doc]
    book.add_item(epub.EpubNav())
    assert doc.get_content() == content
    assert "Café" in cast("str", etree.fromstring(doc.get_content()).xpath("string()"))
    output = write_bytes(book)
    with zipfile.ZipFile(io.BytesIO(output)) as archive:
        assert archive.read("EPUB/encoded.xhtml") == content
    restored = epub.read_epub(io.BytesIO(output)).get_item_with_href("encoded.xhtml")
    assert restored is not None
    assert restored.content == content


@pytest.mark.parametrize("declaration", ["", '<?xml version="1.0"?>', '<?xml version="1.0" encoding="UTF-8"?>'])
def test_preserve_unicode_is_utf8(declaration):
    text = declaration + ORIGINAL.decode("utf-8").split("\n", 1)[1]
    doc = epub.EpubHtml(content=text, preserve_content=True)
    epub.EpubBook().add_item(doc)
    assert doc.get_content() == text.encode("utf-8")


@pytest.mark.parametrize("encoding", ["utf-16", "iso-8859-1", "ascii", "unknown-codec"])
def test_preserve_unicode_rejects_conflicting_declaration(encoding):
    doc = epub.EpubHtml(content=ORIGINAL.decode("utf-8").replace("UTF-8", encoding), preserve_content=True)
    epub.EpubBook().add_item(doc)
    with pytest.raises(ValueError, match="UTF-8"):
        doc.get_content()


def test_current_content_and_writer_plugins_are_used():
    book = edit_book(make_source())
    original = book.get_item_with_id("original")
    original.set_content(ORIGINAL.replace(b"Synthetic chapter", b"Edited directly"))
    calls = []

    class Plugin:
        def before_write(self, book):
            calls.append("book")

        def html_before_write(self, book, item):
            if item.id == "original":
                calls.append("chapter")
                item.set_content(item.content.replace(b"Edited directly", b"Edited by plugin"))

    with zipfile.ZipFile(io.BytesIO(write_bytes(book, {"plugins": [Plugin()]}))) as archive:
        assert archive.read("EPUB/Text/original.xhtml") == ORIGINAL.replace(b"Synthetic chapter", b"Edited by plugin")
    assert calls == ["book", "chapter"]


@pytest.mark.parametrize("call_super", [True, False])
def test_subclass_getter_is_still_dispatched(call_super):
    calls = []

    class CustomChapter(epub.EpubHtml):
        def get_content(self, default=None):
            calls.append(self.id)
            if not call_super:
                return ORIGINAL.replace(b"Original</h1>", b"Custom</h1>")
            return super().get_content(default).replace(b"Original</h1>", b"Custom</h1>")

    book = edit_book(make_source())
    custom = CustomChapter(uid="custom", file_name="custom.xhtml", content=ORIGINAL, preserve_content=True)
    book.add_item(custom)
    with zipfile.ZipFile(io.BytesIO(write_bytes(book))) as archive:
        assert archive.read("EPUB/custom.xhtml") == ORIGINAL.replace(b"Original</h1>", b"Custom</h1>")
    assert calls == ["custom"]


def test_reader_plugin_changes_are_preserved():
    class Plugin:
        def html_after_read(self, book, item):
            if item.id == "original":
                item.set_content(item.content.replace(b"Synthetic chapter", b"Reader plugin change"))

    book = epub.read_epub(io.BytesIO(make_source()), {"plugins": [Plugin()]})
    original = book.get_item_with_id("original")
    assert isinstance(original, epub.EpubHtml)
    original.preserve_content = True
    with zipfile.ZipFile(io.BytesIO(write_bytes(book))) as archive:
        assert archive.read("EPUB/Text/original.xhtml") == ORIGINAL.replace(
            b"Synthetic chapter", b"Reader plugin change"
        )


def test_generated_nav_and_cover_ignore_preservation_flag():
    book = edit_book(make_source())
    generated_cover = epub.EpubCoverHtml(
        uid="generated-cover", file_name="generated-cover.xhtml", image_name="images/cover.svg", title="Generated cover"
    )
    generated_cover.content = b"This must be replaced by the cover template."
    book.add_item(generated_cover)
    assert isinstance(book.get_item_with_id("generated-cover"), epub.EpubCoverHtml)
    assert not generated_cover.is_chapter()
    for item in book.get_items():
        if isinstance(item, epub.EpubHtml):
            item.preserve_content = True
    # Keep the added fragment on the generated path.
    book.get_item_with_id("added").preserve_content = False
    assert generated_cover.preserve_content
    output = write_bytes(book)
    assert_workflow(output)
    with zipfile.ZipFile(io.BytesIO(output)) as archive:
        cover = etree.fromstring(archive.read("EPUB/generated-cover.xhtml"))
        assert cover.xpath("//x:img/@src", namespaces=NS) == ["images/cover.svg"]
        assert cover.xpath("//x:img/@alt", namespaces=NS) == ["Generated cover"]


def test_preservation_owns_document_and_does_not_require_template():
    doc = epub.EpubHtml(content=ORIGINAL, title="Ignored", lang="de", direction="rtl", preserve_content=True)
    doc.add_link(href="ignored.css", rel="stylesheet")
    doc.add_meta(name="ignored", content="ignored")
    book = epub.EpubBook()
    book.add_item(doc)
    book.templates.pop("chapter")
    assert doc.get_content() == ORIGINAL
    doc.preserve_content = False
    with pytest.raises(ValueError, match="template"):
        doc.get_content()


def test_unattached_preserved_chapter_keeps_attachment_error():
    with pytest.raises(ValueError, match="not attached"):
        epub.EpubHtml(content=ORIGINAL, preserve_content=True).get_content()


@pytest.mark.parametrize("content", [b"", b"<p>fragment</p>", b"<html>malformed", ""])
def test_preservation_is_not_validation(content):
    # The caller must supply a complete, valid document; no silent repairs occur.
    doc = epub.EpubHtml(content=content, preserve_content=True)
    epub.EpubBook().add_item(doc)
    assert doc.get_content() == (content.encode("utf-8") if isinstance(content, str) else content)


def test_preservation_rejects_unsupported_content_type():
    doc = epub.EpubHtml(content=ORIGINAL, preserve_content=True)
    epub.EpubBook().add_item(doc)
    doc.content = None  # ty: ignore[invalid-assignment]
    with pytest.raises(TypeError, match="str or bytes"):
        doc.get_content()
