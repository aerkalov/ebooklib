# coding=utf-8

from ebooklib import epub
from tempfile import TemporaryFile


if __name__ == '__main__':
    book = epub.EpubBook()

    # add metadata
    book.set_identifier('sample123456')
    book.set_title('Sample book')
    book.set_language('en')

    book.add_author('Aleksandar Erkalovic')

    # intro chapter
    c1 = epub.EpubHtml(title='Introduction', file_name='intro.xhtml', lang='en')
    c1.set_content(u'<html><head></head><body><h1>Introduction</h1><p>Introduction paragraph where i explain what is happening.</p></body></html>')

    # about chapter
    c2 = epub.EpubHtml(title='About this book', file_name='about.xhtml', content=TemporaryFile())
    c2.write('<h1>About this book</h1>')
    for i in range(1024):
        c2.write('<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Proin rutrum erat ipsum, at fringilla sem sodales ut. Donec rutrum condimentum leo, non convallis ipsum sodales vel. Sed vulputate, quam dapibus pharetra viverra, nunc magna fermentum ligula, sed placerat enim diam id nisi. Sed justo nunc, placerat vel rutrum eget, lacinia quis ante. Maecenas semper turpis lectus, sed sollicitudin diam feugiat vitae. Mauris massa felis, cursus non enim a, consequat pulvinar mauris. Proin scelerisque neque felis, in fringilla ligula tristique ac. Phasellus interdum lacus neque, ac efficitur nibh consequat a. Donec enim enim, commodo sed finibus in, dignissim sit amet arcu. Nam mollis eu ipsum sed ornare. Maecenas non ipsum molestie, volutpat nulla quis, accumsan arcu. Cras imperdiet augue interdum ipsum laoreet malesuada vitae consectetur ipsum. Quisque vitae tortor augue.</p>')

    # add chapters to the book
    book.add_item(c1)
    book.add_item(c2)
    
    # create table of contents
    # - add section
    # - add auto created links to chapters

    book.toc = (epub.Link('intro.xhtml', 'Introduction', 'intro'),
                 (epub.Section('Languages'),
                 (c1, c2))
                )

    # add navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # define css style
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

    # add css file
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    # create spine
    book.spine = ['nav', c1, c2]

    # create epub file
    epub.write_epub('test.epub', book, {})

