# coding=utf-8

from ebooklib import epub



if __name__ == '__main__':
    book = epub.EpubBook()

    book.set_identifier('id123456')
    book.set_title('This is my book')
    book.set_language('fi')

    book.add_metadata('DC', 'title', 'Naslov', {'id': 't1'})
    book.add_metadata(None, 'meta', 'main', {'refines': '#t1', 'property': 'title-type'})
    book.add_metadata('DC', 'title', 'Naslov', {'id': 't2'})
    book.add_metadata(None, 'meta', 'edition', {'refines': '#t2', 'property': 'title-type'})

    book.add_author('Mirko Bulaja')
    book.add_author('Danko Bananko', file_as='Gospodin Danko Bananko', role='ill', uid='coauthor')

    img = open('image.jpg', 'r').read()
    book.set_cover("image.jpg", img)

    # create chapters
    c1 = epub.EpubHtml(title='Intro 1', file_name='chap_01.xhtml', lang='hr')
    c1.set_content(u'<html><head></head><body><h1>This is I!</h1><p>This is something i am writing.</p><p>Šime Đodan ima puno posla.</p></body></html>')

    c2 = epub.EpubHtml(title='Intro 2', file_name=u'chap_02_đšž.xhtml')
    c2.set_content('<h1>This is I!</h1><p>Helou, helou!</p><p><a href="http://ajme/">Ovo je link</a></p>')
    c2.properties.append('rendition:layout-pre-paginated rendition:orientation-landscape rendition:spread-none')

    # add all the items
    book.add_item(c1)
    book.add_item(c2)
    
    book.toc = ( (epub.Section('Languages'),
                    (c1, c2)),
                )


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

    # this should be maybe add by default or something
    book.add_item(epub.EpubNcx())
    nav = epub.EpubNav()
    nav.add_item(nav_css)
    book.add_item(nav)

    # this probably is not correct. should be able to define other properties also
    book.spine = ['cover', 'nav', c1, c2]

    # write book to the file
    epub.write_epub('test.epub', book)

    print '------------'
    for x in nav.get_links_of_type('text/css'):
        print x

