import ebooklib
from ebooklib import epub


class TestEpubCover:
    def test_init_default(self):
        cover = epub.EpubCover()

        assert cover.get_id() == "cover-img"
        assert cover.get_type() == ebooklib.ITEM_COVER
