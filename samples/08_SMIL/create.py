# coding=utf-8

from ebooklib import epub

if __name__ == '__main__':
    book = epub.EpubBook()

    # add metadata
    book.set_identifier('sample123456')
    book.set_title('Sample book')
    book.set_language('en')

    book.add_metadata(None, 'meta', 'Naro Narrator', {'property': 'media:narrator'})
    book.add_metadata(None, 'meta', '0:10:10.500', {'property': 'media:duration'}) 

    book.add_metadata(None, 'meta', '0:05:00.500', {'property': 'media:duration', 'refines': '#intro_overlay'}) 
    book.add_metadata(None, 'meta', '-epub-media-overlay-active', {'property': 'media:active-class'})
    book.add_author('Aleksandar Erkalovic')

    # intro chapter
    c1 = epub.EpubHtml(title='Introduction', file_name='intro.xhtml', lang='en', media_overlay='intro_overlay')
    c1.content=u'<html><head></head><body><section epub:type="frontmatter colophon"><h1><span id="header_1">Introduction</span></h1><p><span id="para_1">Introduction paragraph where i explain what is happening.</span></p></section></body></html>'

    s1 = epub.EpubSMIL(uid='intro_overlay', file_name='test.smil', content=open('test.smil', 'rt').read())

    a1 = epub.EpubItem(file_name='chapter1_audio.mp3', content=open('chapter1_audio.mp3', 'rb').read(), media_type='audio/mpeg')
    # add chapters to the book
    book.add_item(c1)
    book.add_item(s1)
    book.add_item(a1)
    
    book.toc = [epub.Link('intro.xhtml', 'Introduction', 'intro')]

    # add navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # create spine
    book.spine = ['nav', c1]

    # create epub file
    epub.write_epub('test.epub', book, {})

