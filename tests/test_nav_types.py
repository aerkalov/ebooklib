"""Read/write regressions for semantic navigation selection."""

import io
import zipfile

import pytest
from lxml import etree

from ebooklib import epub

EPUB_NS = epub.NAMESPACES["EPUB"]
XHTML = "{" + epub.NAMESPACES["XHTML"] + "}"


def _book_bytes():
    book = epub.EpubBook()
    book.set_identifier("synthetic-nav-types")
    book.set_title("Navigation type regression")
    book.set_language("en")
    chapter = epub.EpubHtml(uid="chapter", file_name="text/chapter.xhtml", title="Chapter")
    chapter.set_content('<h1 id="start">Chapter</h1><span id="p1" epub:type="pagebreak">1</span>')
    book.add_item(chapter)
    book.add_item(epub.EpubNav(file_name="navigation/nav.xhtml"))
    book.toc = [(epub.Section("Part", "text/chapter.xhtml#start"), [chapter])]
    book.spine = ["nav", chapter]
    output = io.BytesIO()
    epub.write_epub(output, book)
    return output


def _change_nav(change):
    output = io.BytesIO()
    with zipfile.ZipFile(_book_bytes()) as source, zipfile.ZipFile(output, "w") as target:
        for entry in source.infolist():
            content = source.read(entry.filename)
            if entry.filename == "EPUB/navigation/nav.xhtml":
                content = change(content)
            target.writestr(entry, content)
    output.seek(0)
    return output


def _assert_book(book):
    section, children = book.toc[0]
    assert len(book.toc) == 1
    assert (section.href, section.title) == ("text/chapter.xhtml#start", "Part")
    assert [(link.href, link.title) for link in children] == [("text/chapter.xhtml", "Chapter")]
    assert [(page.href, page.title) for page in book.pages] == [("text/chapter.xhtml#p1", "1")]
    chapter = book.get_item_with_id("chapter")
    assert [(page.href, page.title) for page in chapter.pages] == [("text/chapter.xhtml#p1", "1")]


def _assert_roundtrip(source):
    restored = epub.read_epub(source)
    _assert_book(restored)
    rewritten = io.BytesIO()
    epub.write_epub(rewritten, restored)
    rewritten.seek(0)
    _assert_book(epub.read_epub(rewritten))
    with zipfile.ZipFile(rewritten) as archive:
        nav = etree.fromstring(archive.read("EPUB/navigation/nav.xhtml"))
        assert [(a.get("href"), a.text) for a in nav.findall(f".//{XHTML}a")] == [
            ("../text/chapter.xhtml#start", "Part"),
            ("../text/chapter.xhtml", "Chapter"),
            ("../text/chapter.xhtml#p1", "1"),
        ]


@pytest.mark.parametrize("nav_type", ["toc", "page-list"])
@pytest.mark.parametrize(
    "value",
    [
        "{type}",
        " {type} ",
        "frontmatter {type}",
        "{type}\tother\nmore\r",
        "frontmatter\n{type}",
        "frontmatter\r{type}",
        "frontmatter&#x9;{type}",
        "frontmatter&#xA;{type}",
        "frontmatter&#xD;{type}",
    ],
)
def test_navigation_type_tokens_survive_roundtrip(nav_type, value):
    value = value.format(type=nav_type)
    source = _change_nav(
        lambda content: content.replace(f'epub:type="{nav_type}"'.encode(), f'epub:type="{value}"'.encode())
    )
    _assert_roundtrip(source)


@pytest.mark.parametrize(
    "attribute",
    [
        'class="{type}"',
        'id="{type}"',
        'type="{type}"',
        'epub:type="{type}-extra"',
        'epub:type="extra-{type}"',
        'epub:type="{type}\u00a0other"',
        'epub:type="{type}" xmlns:epub="https://example.invalid/wrong"',
        'custom:type="{type} other" xmlns:custom="https://example.invalid/custom"',
    ],
)
@pytest.mark.parametrize("nav_type", ["toc", "page-list"])
def test_unrelated_navigation_does_not_replace_semantic_navigation(attribute, nav_type):
    decoy = (
        f"<nav {attribute.format(type=nav_type)}><ol><li>"
        '<a href="../text/chapter.xhtml#wrong">Wrong menu</a></li></ol></nav>'
    ).encode()
    _assert_roundtrip(_change_nav(lambda content: content.replace(b"<body>", b"<body>" + decoy)))


@pytest.mark.parametrize("tokens", [False, True])
def test_alternative_namespace_prefix_survives_roundtrip(tokens):
    def change(content):
        content = content.replace(b"xmlns:epub=", b"xmlns:sem=").replace(b"epub:type=", b"sem:type=")
        if tokens:
            content = content.replace(b'sem:type="toc"', b'sem:type="frontmatter toc"')
            content = content.replace(b'sem:type="page-list"', b'sem:type="page-list other"')
        return content

    _assert_roundtrip(_change_nav(change))


def test_undeclared_epub_prefix_remains_tolerated():
    _assert_roundtrip(_change_nav(lambda content: content.replace(f' xmlns:epub="{EPUB_NS}"'.encode(), b"")))


def test_missing_page_list_remains_optional():
    source = _change_nav(lambda content: content.replace(b'epub:type="page-list"', b'epub:type="other"'))
    restored = epub.read_epub(source)
    assert restored.pages == []
    chapter = restored.get_item_with_id("chapter")
    assert isinstance(chapter, epub.EpubHtml)
    assert chapter.pages == []
    assert restored.toc[0][0].title == "Part"


def test_namespace_declaration_on_body_is_resolved():
    def change(content):
        content = content.replace(f' xmlns:epub="{EPUB_NS}"'.encode(), b"")
        return content.replace(b"<body>", f'<body xmlns:sem="{EPUB_NS}">'.encode()).replace(b"epub:type=", b"sem:type=")

    _assert_roundtrip(_change_nav(change))


@pytest.mark.parametrize("nav_type", ["toc", "page-list"])
@pytest.mark.parametrize("attribute", ["class", "id", "type"])
def test_legacy_unqualified_navigation_remains_tolerated(nav_type, attribute):
    source = _change_nav(
        lambda content: content.replace(f'epub:type="{nav_type}"'.encode(), f'{attribute}="{nav_type}"'.encode())
    )
    _assert_roundtrip(source)


def test_case_distinct_namespace_bindings_remain_readable():
    def change(content):
        content = content.replace(
            f'xmlns:epub="{EPUB_NS}"'.encode(),
            f'xmlns:S="https://example.invalid/other" xmlns:s="{EPUB_NS}"'.encode(),
        )
        return content.replace(b"epub:type=", b"s:type=")

    _assert_roundtrip(_change_nav(change))


def test_explicitly_prefixed_xhtml_navigation_survives_roundtrip():
    def change(content):
        root = etree.fromstring(content)
        replacement = etree.Element(root.tag, nsmap={"x": epub.NAMESPACES["XHTML"], "epub": EPUB_NS})
        replacement.attrib.update(root.attrib)
        replacement.extend(root)
        return etree.tostring(replacement, encoding="utf-8", xml_declaration=True)

    _assert_roundtrip(_change_nav(change))


def test_malformed_xml_keeps_legacy_html_fallback():
    source = _change_nav(lambda content: content.replace(b"<body>", b"<body>&nbsp;"))
    _assert_roundtrip(source)


def test_internal_entity_is_not_expanded():
    def change(content):
        content = content.replace(b"<!DOCTYPE html>", b'<!DOCTYPE html [<!ENTITY test "Expanded entity">]>')
        return content.replace(b">Part<", b">&test;<")

    restored = epub.read_epub(_change_nav(change))
    assert restored.toc[0][0].title == "&test;"


def test_external_entity_is_not_resolved():
    def change(content):
        content = content.replace(
            b"<!DOCTYPE html>",
            b'<!DOCTYPE html [<!ENTITY test SYSTEM "https://example.invalid/synthetic-entity">]>',
        )
        return content.replace(b">Part<", b">&test;<")

    restored = epub.read_epub(_change_nav(change))
    assert restored.toc[0][0].title == "&test;"
