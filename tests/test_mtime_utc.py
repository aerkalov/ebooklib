"""Tests for UTC handling of the dcterms:modified metadata and mtime option.

The EPUB 3 specification requires dcterms:modified to be a UTC timestamp
(https://www.w3.org/TR/epub-33/#sec-metadata-last-modified).
"""

import datetime
import io
import re
import zipfile
from typing import cast

from lxml import etree

from ebooklib import epub
from ebooklib.writer import EpubWriter

DCTERMS_MODIFIED_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _create_basic_book() -> epub.EpubBook:
    book = epub.EpubBook()
    book.set_identifier("test-mtime")
    book.set_title("Test book")
    book.set_language("en")

    doc = epub.EpubHtml(uid="chap_1", file_name="test.xhtml")
    doc.set_content("<body><h1>Title</h1><p>lorum ipsum.</p></body>")
    book.add_item(doc)

    book.add_item(epub.EpubNav())
    book.spine = ["nav", doc]
    book.toc = (doc,)

    return book


def _write_book(options: dict) -> io.BytesIO:
    f = io.BytesIO()
    epub.write_epub(f, _create_basic_book(), options)
    f.seek(0)
    return f


def _read_dcterms_modified(epub_file: io.BytesIO) -> str:
    with zipfile.ZipFile(epub_file) as zf:
        opf = zf.read("EPUB/content.opf")
    root = etree.fromstring(opf)
    elements = cast(
        "list[etree._Element]",
        root.xpath(
            "//opf:metadata/opf:meta[@property='dcterms:modified']",
            namespaces={"opf": "http://www.idpf.org/2007/opf"},
        ),
    )
    assert len(elements) == 1
    assert isinstance(elements[0], etree._Element)
    text = elements[0].text
    assert text is not None
    return text


class TestDefaultMtime:
    def test_default_mtime_is_timezone_aware_utc(self):
        mtime = EpubWriter.get_default_options()["mtime"]

        assert mtime.tzinfo is not None
        assert mtime.utcoffset() == datetime.timedelta(0)

    def test_default_mtime_is_close_to_now(self):
        before = datetime.datetime.now(datetime.timezone.utc)
        mtime = EpubWriter.get_default_options()["mtime"]
        after = datetime.datetime.now(datetime.timezone.utc)

        assert before <= mtime <= after


class TestDctermsModified:
    def test_written_timestamp_matches_required_format(self):
        value = _read_dcterms_modified(_write_book({}))

        assert DCTERMS_MODIFIED_RE.match(value), f"Invalid dcterms:modified format: {value}"

    def test_aware_mtime_is_converted_to_utc(self):
        # 2024-05-15 12:00:00 at UTC+2 must be written as 10:00:00 UTC.
        tz_plus2 = datetime.timezone(datetime.timedelta(hours=2))
        mtime = datetime.datetime(2024, 5, 15, 12, 0, 0, tzinfo=tz_plus2)

        value = _read_dcterms_modified(_write_book({"mtime": mtime}))

        assert value == "2024-05-15T10:00:00Z"

    def test_utc_mtime_is_written_unchanged(self):
        mtime = datetime.datetime(2024, 5, 15, 12, 0, 0, tzinfo=datetime.timezone.utc)

        value = _read_dcterms_modified(_write_book({"mtime": mtime}))

        assert value == "2024-05-15T12:00:00Z"

    def test_negative_offset_mtime_is_converted_to_utc(self):
        # 2024-05-15 08:30:00 at UTC-5 must be written as 13:30:00 UTC.
        tz_minus5 = datetime.timezone(datetime.timedelta(hours=-5))
        mtime = datetime.datetime(2024, 5, 15, 8, 30, 0, tzinfo=tz_minus5)

        value = _read_dcterms_modified(_write_book({"mtime": mtime}))

        assert value == "2024-05-15T13:30:00Z"

    def test_naive_mtime_is_treated_as_local_time(self):
        # A naive datetime must be interpreted as local time and converted to UTC.
        naive = datetime.datetime(2024, 5, 15, 12, 0, 0)
        expected = naive.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        value = _read_dcterms_modified(_write_book({"mtime": naive}))

        assert value == expected
        assert DCTERMS_MODIFIED_RE.match(value)

    def test_date_crossing_day_boundary(self):
        # 2024-05-15 01:00:00 at UTC+3 belongs to the previous day in UTC.
        tz_plus3 = datetime.timezone(datetime.timedelta(hours=3))
        mtime = datetime.datetime(2024, 5, 15, 1, 0, 0, tzinfo=tz_plus3)

        value = _read_dcterms_modified(_write_book({"mtime": mtime}))

        assert value == "2024-05-14T22:00:00Z"


class TestZipTimestamps:
    def test_zipinfo_uses_local_time_for_aware_mtime(self):
        # ZIP timestamps carry no timezone info and are conventionally local time.
        tz_plus2 = datetime.timezone(datetime.timedelta(hours=2))
        mtime = datetime.datetime(2024, 5, 15, 12, 0, 0, tzinfo=tz_plus2)
        expected_local = mtime.astimezone()

        result = EpubWriter.datetime_to_zipinfo_datetime(mtime)

        assert result == (
            expected_local.year,
            expected_local.month,
            expected_local.day,
            expected_local.hour,
            expected_local.minute,
            expected_local.second,
        )

    def test_zipinfo_keeps_naive_mtime_unchanged(self):
        naive = datetime.datetime(2024, 5, 15, 12, 0, 0)

        result = EpubWriter.datetime_to_zipinfo_datetime(naive)

        assert result == (2024, 5, 15, 12, 0, 0)
