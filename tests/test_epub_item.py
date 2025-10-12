import six

import ebooklib
from ebooklib import epub

FILENAME_TYPES = [
    ("images/image_my_123.jpg", ebooklib.ITEM_IMAGE, "image/jpeg"),
    ("images/image%20my%20123.jpeg", ebooklib.ITEM_IMAGE, "image/jpeg"),
    ("images/image%20my%20123.png", ebooklib.ITEM_IMAGE, "image/png"),
    ("style/image.css", ebooklib.ITEM_STYLE, "text/css"),
    ("image/image.svg", ebooklib.ITEM_VECTOR, "image/svg+xml"),
    ("scripts/image.js", ebooklib.ITEM_SCRIPT, "application/javascript"),
    ("fonts/font.otf", ebooklib.ITEM_FONT, "application/vnd.ms-opentype"),
    ("fonts/font.woff", ebooklib.ITEM_FONT, "application/font-woff"),
    ("video/video.mov", ebooklib.ITEM_VIDEO, "video/quicktime"),
    ("video/video.mp4", ebooklib.ITEM_VIDEO, "video/mp4"),
    ("audio/audio.mp3", ebooklib.ITEM_AUDIO, "audio/mpeg"),
    ("audio/audio.ogg", ebooklib.ITEM_AUDIO, "audio/ogg"),
    ("smil/document.smil", ebooklib.ITEM_SMIL, "application/smil+xml"),
]


class TestEpubItemInitialization:
    def test_init_default(self):
        item = epub.EpubItem()

        assert item.id is None
        assert item.file_name == ""
        assert item.media_type == ""
        assert item.content == six.b("")
        assert item.is_linear is True
        assert item.manifest is True
        assert item.book is None

    def test_init_arguments(self):
        item = epub.EpubItem(
            uid="my_uid",
            file_name="Document/index.xhtml",
            content=six.b("THIS IS CONTENT"),
        )

        assert item.get_id() == "my_uid"
        assert item.get_name() == "Document/index.xhtml"
        assert item.get_content() == six.b("THIS IS CONTENT")

    def test_content(self):
        item = epub.EpubItem(
            content=six.b("THIS IS CONTENT"),
        )

        assert item.get_content() == six.b("THIS IS CONTENT")

        item.set_content(six.b("NEW CONTENT"))
        assert item.get_content() == six.b("NEW CONTENT")

    def test_get_type(self):
        """Test item.get_type() method."""

        for file_name, file_type, _ in FILENAME_TYPES:
            item = epub.EpubItem(file_name=file_name)
            assert item.get_type() == file_type

    def test_get_items_created_book(self):
        book = epub.EpubBook()

        for file_name, _, media_type in FILENAME_TYPES:
            item = epub.EpubItem(
                uid="id-{file_name}".format(file_name=file_name),  # noqa: UP032
                file_name=file_name,
                media_type=media_type,
            )
            book.add_item(item)
            assert book.get_item_with_id("id-{file_name}".format(file_name=file_name)) == item  # noqa: UP032
            assert book.get_item_with_href(file_name) == item

        assert len(list(book.get_items_of_type(ebooklib.ITEM_IMAGE))) == 3
        assert len(list(book.get_items_of_media_type("image/jpeg"))) == 2
        assert len(list(book.get_items())) == len(FILENAME_TYPES)
