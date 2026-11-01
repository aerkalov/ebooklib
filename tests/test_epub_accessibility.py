import io
import zipfile

from lxml import etree

from ebooklib import epub

OPF_NS = "http://www.idpf.org/2007/opf"


def _create_book_with_accessibility_metadata():
    book = epub.EpubBook()
    book.set_identifier("a11y123456")
    book.set_title("Accessible test book")
    book.set_language("en")
    book.add_author("Test Author")

    book.set_conforms_to("EPUB Accessibility 1.1 - WCAG 2.2 Level AA")
    book.add_access_mode("textual")
    book.add_access_mode("visual")
    book.add_access_mode_sufficient("textual")
    book.add_access_mode_sufficient(["textual", "visual"])
    book.add_accessibility_feature("alternativeText")
    book.add_accessibility_feature("readingOrder")
    book.add_accessibility_hazard("none")
    book.add_accessibility_api("ARIA")
    book.add_accessibility_control("fullKeyboardControl")
    book.set_accessibility_summary("All content is available in a linear reading order.")

    doc = epub.EpubHtml(uid="chap_1", file_name="test.xhtml")
    doc.set_content("<body><h1>Title</h1><p>lorum ipsum.</p></body>")
    book.add_item(doc)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav", doc]

    return book


def _opf_meta_properties(epub_bytes):
    with zipfile.ZipFile(io.BytesIO(epub_bytes)) as archive:
        opf_name = [name for name in archive.namelist() if name.endswith("content.opf")][0]
        root = etree.fromstring(archive.read(opf_name))

    properties = {}
    for meta in root.iter(f"{{{OPF_NS}}}meta"):
        prop = meta.get("property")
        if prop:
            properties.setdefault(prop, []).append(meta.text)
    return properties


def test_accessibility_metadata_is_written_to_the_package_document():
    book = _create_book_with_accessibility_metadata()

    f = io.BytesIO()
    epub.write_epub(f, book, {})

    properties = _opf_meta_properties(f.getvalue())
    properties.pop("dcterms:modified")
    assert properties == {
        "dcterms:conformsTo": ["EPUB Accessibility 1.1 - WCAG 2.2 Level AA"],
        "schema:accessMode": ["textual", "visual"],
        "schema:accessModeSufficient": ["textual", "textual,visual"],
        "schema:accessibilityFeature": ["alternativeText", "readingOrder"],
        "schema:accessibilityHazard": ["none"],
        "schema:accessibilityAPI": ["ARIA"],
        "schema:accessibilityControl": ["fullKeyboardControl"],
        "schema:accessibilitySummary": ["All content is available in a linear reading order."],
    }


def test_get_accessibility_metadata():
    book = _create_book_with_accessibility_metadata()

    assert book.get_accessibility_metadata() == {
        "dcterms:conformsTo": ["EPUB Accessibility 1.1 - WCAG 2.2 Level AA"],
        "schema:accessMode": ["textual", "visual"],
        "schema:accessModeSufficient": ["textual", "textual,visual"],
        "schema:accessibilityFeature": ["alternativeText", "readingOrder"],
        "schema:accessibilityHazard": ["none"],
        "schema:accessibilityAPI": ["ARIA"],
        "schema:accessibilityControl": ["fullKeyboardControl"],
        "schema:accessibilitySummary": ["All content is available in a linear reading order."],
    }


def test_accessibility_metadata_survives_a_write_read_round_trip():
    book = _create_book_with_accessibility_metadata()

    f = io.BytesIO()
    epub.write_epub(f, book, {})
    f.seek(0)

    read_book = epub.read_epub(f)
    metadata = read_book.get_accessibility_metadata()

    assert metadata["schema:accessibilityFeature"] == ["alternativeText", "readingOrder"]
    assert metadata["schema:accessModeSufficient"] == ["textual", "textual,visual"]
    assert metadata["dcterms:conformsTo"] == ["EPUB Accessibility 1.1 - WCAG 2.2 Level AA"]


def test_unique_accessibility_properties_replace_instead_of_duplicating():
    book = epub.EpubBook()
    # a <meta name="cover"> entry shares the ("meta") storage with the
    # accessibility properties and must not be removed by a replacement
    book.set_cover("image.jpg", b"fake image data")

    book.set_accessibility_summary("First summary.")
    book.set_accessibility_summary("Second summary.")
    book.set_conforms_to("EPUB Accessibility 1.1 - WCAG 2.0 Level A")
    book.set_conforms_to("EPUB Accessibility 1.1 - WCAG 2.2 Level AA")

    assert book.get_accessibility_metadata()["schema:accessibilitySummary"] == ["Second summary."]
    assert book.get_accessibility_metadata()["dcterms:conformsTo"] == ["EPUB Accessibility 1.1 - WCAG 2.2 Level AA"]
    assert ("", {"name": "cover", "content": "cover-img"}) in book.get_metadata(None, "meta")
