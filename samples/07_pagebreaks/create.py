# coding=utf-8

from ebooklib import epub
from ebooklib.plugins import standard
from ebooklib.utils import create_pagebreak


if __name__ == '__main__':
    book = epub.EpubBook()

    # add metadata
    book.set_identifier('sample123456')
    book.set_title('Sample book')
    book.set_language('en')

    book.add_author('Aleksandar Erkalovic')

    # build the chapter HTML and add the page break
    c1 = epub.EpubHtml(title='Introduction', file_name='intro.xhtml', lang='en')
    c1.content = u'<h1>Introduction</h1><p><span id="page1" epub:type="pagebreak">1</span>This chapter has a visible page number.</p><p><span id="page2" epub:type="pagebreak">2</span>Something else now.</p>'

    c2 = epub.EpubHtml(title='Chapter the Second', file_name='chap02.xhtml', lang='en')
    c2.content = u'<html><head></head><body><h1>Chapter the Second</h1><p>This chapter has two page breaks, both with invisible page numbers.</p>'

    # Add invisible page numbers that match the printed text, for accessibility
    c2.content += create_pagebreak("2")

    # You can add more content  after the page break
    c2.content += u'<p>This is the second page in the second chapter, after the invisible page break.</p>'

    # Add invisible page numbers that match the printed text, for accessibility
    c2.content += create_pagebreak("3", label="Page 3")

    # close the chapter
    c2.content += u'</body></html>'

    # add chapters to the book
    book.add_item(c1)
    book.add_item(c2)
    
    # create table of contents
    # - add manual link
    # - add section
    # - add auto created links to chapters

    book.toc = ((c1, c2, ))

    # add navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # create spine
    book.spine = ['nav', c1, c2, ]

    # create epub file
    opts = {'plugins': [standard.SyntaxPlugin()]}
    epub.write_epub('test.epub', book, opts)

