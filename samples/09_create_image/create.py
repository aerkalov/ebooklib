# coding=utf-8

from ebooklib import epub


if __name__ == '__main__':
    book = epub.EpubBook()

    # add metadata
    book.set_identifier('image123')
    book.set_title('Simple book with image')
    book.set_language('en')

    book.add_author('Aleksandar Erkalovic')

    # chapter with image
    c1 = epub.EpubHtml(title='Chapter with image', file_name='chapter_image.xhtml', lang='en')
    c1.content=u'''<html>
  <head></head>
  <body>
    <h1>The world famous chapter</h1>
    <p>Yes, this is the world famous chapter with image!</p>
    <img src="static/ebooklib.gif"/>
  </body>
</html>'''

    image_content = open('ebooklib.gif', 'rb').read()
    img = epub.EpubImage(uid='image_1', file_name='static/ebooklib.gif', media_type='image/gif', content=image_content)

    # add chapters to the book
    book.add_item(c1)
    book.add_item(img)
    
    # create table of contents
    # - add section
    # - add auto created links to chapters

    book.toc = (c1, )

    # add navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # create spine
    book.spine = ['nav', c1]

    # create epub file
    epub.write_epub('test.epub', book, {})

