# coding=utf-8
import sys
import os.path

from ebooklib import epub

from booki.editor import models


def export_booktype(bookid):    
    # Get Booktype Book

    try:
        booktype_book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        print 'NO SUCH BOOK'
        sys.exit(-1)
        
    book_version = booktype_book.getVersion(None)

    # START CREATING THE BOOK
    book = epub.EpubBook()
    
    # set basic info
    book.set_identifier('booktype:%s' % booktype_book.url_title)
    book.set_title(booktype_book.title)
    book.set_language('en')

    # set description
    if booktype_book.description != '':
        book.add_metadata('DC', 'description', booktype_book.description)


    # set license
    lic = booktype_book.license
    if lic:
        book.add_metadata('DC', 'rights', lic.name)

    # The Contributors for Booktype book

#    book.add_author('Thea von Harbou', role='aut', uid='author')
    book.add_author('Aleksandar Erkalovic', role='aut', uid='author')

    book.add_author('Aleksandar Erkalovic', file_as='Aleksandar Erkalovic', role='ill', uid='illustrator')

    # set cover image
    img = open('cover.jpg', 'r').read()
    book.set_cover("image.jpg", img)

    toc = []
    section = []
    spine = ['cover', 'nav']

    for chapter in book_version.getTOC():
        if chapter.chapter:
            c1 = epub.EpubHtml(title=chapter.chapter.title, file_name='%s.xhtml' % (chapter.chapter.url_title, ))
            c1.add_link(href="style/default.css", rel="stylesheet", type="text/css")

            if chapter.chapter.title == 'Arabic':
                c1.set_language('ar')
            if chapter.chapter.title == 'Japanase':
                c1.set_language('jp')

            cont = chapter.chapter.content

            c1.content=cont

            book.add_item(c1)
            spine.append(c1)

            if len(section) > 1:
                section[1].append(c1)
        else:
            if len(section) > 0:
                toc.append(section[:])
                section = []

            section = [epub.Section(chapter.name), []]
            # this is section

    if len(section) > 0:
        toc.append(section[:])

    for i, attachment in enumerate(models.Attachment.objects.filter(version=book_version)):
        try:
            f = open(attachment.attachment.name, "rb")
            blob = f.read()
            f.close()
        except (IOError, OSError), e:
            continue
        else:
            fn = os.path.basename(attachment.attachment.name.encode("utf-8"))
            itm = epub.EpubImage()
            itm.file_name = 'static/%s' % fn
            itm.content = blob
            book.add_item(itm)

    book.toc = toc
    print toc
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    style = '''
body {
    font-family: Cambria, Liberation Serif, Bitstream Vera Serif, Georgia, Times, Times New Roman, serif;
    text-align: justify;
    margin: 0;
    padding: 0;
}

p:last-child {
    padding-bottom: 2em;
}

p {
  text-indent: 1.5em;
}

p.image {
  text-indent: 0px;
}

P + P {
   margin-bottom: 5px;
}

h1 {
    margin-top: 0;
    text-transform: uppercase;
    font-weight: 200;

    border-bottom: 1px solid #808080;
}

img {
  max-width: 100%;
  max-height: 100%;
}

.highlight {
  font-size: 10px;
}

blockquote.quote {
	color: #66a;
	font-weight: normal;
	font-style: italic;
	margin: 1em 3em; }

blockquote.quote p:before {
	content: '"'; }
blockquote.quote p:after {
	content: '"'; }

'''
    default_css = epub.EpubItem(uid="style_default", file_name="style/default.css", media_type="text/css", content=style)
    book.add_item(default_css)

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


    code_style = open('code.css', 'r').read()
    code_css = epub.EpubItem(uid="style_code", file_name="style/code.css", media_type="text/css", content=code_style)
    book.add_item(code_css)


    # this probably is not correct. should be able to define other properties also
    book.spine = spine


    from ebooklib.plugins import booktype, sourcecode

    opts = {'plugins': [booktype.BooktypeLinks(booktype_book),
                        booktype.BooktypeFootnotes(booktype_book),
                        sourcecode.SourceHighlighter()
                        ]
            }

    # one plugin which looks for linked javascript
    # if available then add scripted propertie to the item


    # write book to the file    
    epub.write_epub('test.epub', book, opts)


if __name__ == '__main__':
    export_booktype(sys.argv[1])
