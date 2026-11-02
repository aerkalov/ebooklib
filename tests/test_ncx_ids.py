import io
import zipfile
from typing import cast

import pytest
from lxml import etree

from ebooklib import epub

NCX = {"n": epub.NAMESPACES["DAISY"]}


def make_book():
    book = epub.EpubBook()
    book.set_identifier("synthetic-ncx-ids")
    book.set_title("NCX ID regression")
    book.set_language("en")
    chapter = epub.EpubHtml(uid="chapter", file_name="chapter.xhtml", title="Chapter")
    chapter.content = '<h1 id="first">First</h1><p id="second">Second</p>'
    book.add_item(chapter)
    book.add_item(epub.EpubNav())
    book.add_item(epub.EpubNcx())
    book.spine = ["nav", chapter]
    return book, chapter


def ncx_tree(book):
    output = io.BytesIO()
    assert epub.write_epub(output, book, {"raise_exceptions": True})
    with zipfile.ZipFile(output) as archive:
        return etree.fromstring(archive.read("EPUB/toc.ncx"))


def navpoint_ids(tree):
    return cast("list[str]", tree.xpath("//n:navPoint/@id", namespaces=NCX))


@pytest.mark.parametrize("missing", [None, ""])
def test_missing_link_ids_are_unique_without_mutating_toc(missing):
    book, _ = make_book()
    link = epub.Link("chapter.xhtml#first", "First", missing)
    second = epub.Link("chapter.xhtml#second", "Second", missing)
    book.toc = [link, second, link]
    tree = ncx_tree(book)
    ids = navpoint_ids(tree)
    assert len(ids) == 3
    assert all(ids)
    assert len(set(ids)) == 3
    assert navpoint_ids(ncx_tree(book)) == ids
    assert link.uid == missing
    assert second.uid == missing
    assert tree.xpath("//n:content/@src", namespaces=NCX) == [
        "chapter.xhtml#first",
        "chapter.xhtml#second",
        "chapter.xhtml#first",
    ]


def test_nested_missing_ids_keep_sections_html_and_later_explicit_ids():
    book, chapter = make_book()
    missing_html = epub.EpubHtml(file_name="chapter.xhtml", title="HTML without ID")
    missing_section = epub.EpubHtml(file_name="chapter.xhtml", title="HTML section without ID")
    book.toc = [
        (
            epub.Section("Part", "chapter.xhtml"),
            [
                epub.Link("chapter.xhtml#first", "Missing"),
                (missing_section, [missing_html]),
                (epub.Section("Nested", "chapter.xhtml"), [epub.Link("chapter.xhtml#second", "Later", "navpoint_0")]),
            ],
        ),
        chapter,
    ]
    tree = ncx_tree(book)
    ids = navpoint_ids(tree)
    assert all(ids)
    assert len(ids) == len(set(ids))
    assert ids[0] == "sep_0"
    assert ids[-2:] == ["navpoint_0", "chapter"]
    assert missing_html.id is None
    assert missing_section.id is None
    assert tree.xpath("//n:navLabel/n:text/text()", namespaces=NCX) == [
        "Part",
        "Missing",
        "HTML section without ID",
        "HTML without ID",
        "Nested",
        "Later",
        "Chapter",
    ]


def test_fallback_ids_reserve_all_completed_tree_ids():
    book, _ = make_book()
    template = book.get_template("ncx")
    assert template is not None
    root = etree.fromstring(template)
    root.set("id", "navpoint_0")
    book.set_template("ncx", etree.tostring(root))
    book.toc = [epub.Link("chapter.xhtml#first", "Missing"), epub.Link("chapter.xhtml#second", "Later", "navpoint_1")]
    tree = ncx_tree(book)
    ids = navpoint_ids(tree)
    assert tree.get("id") == "navpoint_0"
    assert ids[0] not in {"navpoint_0", "navpoint_1"}
    assert ids[1] == "navpoint_1"
    assert all(ids)


def test_existing_valid_ids_and_play_order_are_unchanged():
    book, chapter = make_book()
    book.toc = [(epub.Section("Part", "chapter.xhtml"), [epub.Link("chapter.xhtml#first", "First", "first"), chapter])]
    tree = etree.fromstring(epub.EpubWriter(io.BytesIO(), book, {"play_order": {"enabled": True}})._get_ncx())
    assert navpoint_ids(tree) == ["sep_0", "first", "chapter"]
    assert tree.xpath("//n:navPoint/@playOrder", namespaces=NCX) == ["1", "2", "3"]


@pytest.mark.parametrize("explicit", ["duplicate", "not an XML name"])
def test_nonempty_user_ids_are_not_normalized(explicit):
    book, _ = make_book()
    book.toc = [
        epub.Link("chapter.xhtml#first", "First", explicit),
        epub.Link("chapter.xhtml#second", "Second", explicit),
    ]
    assert navpoint_ids(ncx_tree(book)) == [explicit, explicit]
