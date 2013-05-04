# coding=utf-8

from ebooklib import epub



if __name__ == '__main__':
    book = epub.EpubBook()

    book.set_identifier('id123456')
    book.set_title('This is my book')
    book.set_language('fi')

    book.add_author('Mirko Bulaja')
    book.add_author('Danko Bananko', file_as='Gospodin Danko Bananko', role='ill', uid='coauthor')

    img = open('cover.jpg', 'r').read()
    book.set_cover("image.jpg", img)

    # create chapters
    c1 = epub.EpubHtml(title='Intro 1', file_name='chap_01.xhtml', lang='hr')
    c1.content=u'<html><head></head><body><h1>This is I!</h1><p>This is something i am writing.</p><p>Šime Đodan ima puno posla.</p></body></html>'

    c2 = epub.EpubHtml(title='Intro 2', file_name='chap_02.xhtml')
#    c2.content='<html><head></head><body><h1>This is I!</h1><p>Helou, helou!</p><p><img src="static/image.jpg"/><a href="http://ajme/">Ovo je link</a></body></html>'
    c2.content='<h1>This is I!</h1><p>Helou, helou!</p><p><img src="image.jpg"/><a href="http://ajme/">Ovo je link</a></p>'
    c2.properties.append('rendition:layout-pre-paginated rendition:orientation-landscape rendition:spread-none')

    # add all the items
    book.add_item(c1)
    book.add_item(c2)
    
#    book.toc = (epub.Link('cover.xhtml', 'Cover', 'cover'),
    book.toc = (epub.Link('chap_02.xhtml', 'Introduction', 'intro'),
                (epub.Section('Languages'),
                 (c1, c2))
                )

    # this should be maybe add by default or something
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    style = '''
@namespace epub "http://www.idpf.org/2007/ops";

body {
    font-family: Cambria, Liberation Serif, Bitstream Vera Serif, Georgia, Times, Times New Roman, serif;
}

h2 {
     text-align: left;
     text-transform: uppercase;
     font-weight: 200;     
}

ol {
        list-style-type: none;
}

ol > li:first-child {
        margin-top: 0.3em;
}


nav[epub|type~='toc'] > ol > li > ol  {
    list-style-type:square;
}


nav[epub|type~='toc'] > ol > li > ol > li {
        margin-top: 0.3em;
}

'''
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    # this probably is not correct. should be able to define other properties also
    book.spine = ['cover', 'nav', c1, c2]

    # write book to the file
    epub.writeEPUB('test.epub', book, {})

