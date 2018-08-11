Plugins
=======

Plugins can be used to automate some of the workflow. For instance :mod:`ebooklib.plugins.tidyhtml` plugins automatically cleans HTML
output for you. FootnotePlugin for instance rewrites custom footnotes into EPUB3 kind of footnotes. Without these plugins you would
need to do wanted transformations before setting or getting content from your chapters.

There is a :class:`ebooklib.plugins.base.BasePlugin` class which you need to extend. These are the methods you can override.

=================  =============  ==================================
Method             Arguments      Description
=================  =============  ==================================
before_write       book           Processing before book save
after_write        book           Processing after book save
before_read        book           Processing before book read
after_read         book           Processing after book read
item_after_read    book, item     Process general item after read
item_before_write  book, item     Process general item before write
html_after_read    book, chapter  Processing HTML before read
html_before_write  book, chapter  Processing HTML before save
=================  =============  ==================================


Custom plugin
-------------

This is our use case. We have online WYSIWYG editing system for editing content of our books. In the editor to link
to our other page we use this syntax *<a href="../page/">Our page</a>* but in the EPUB book we would need to link
to *page.xhtml* file for instance.

We could do the transformations manually or we could write a plugin which does all of the work for us. We override *html_before_write*
method. We parse the content of our chapter, find all links, replace them with new href and finally set new
content to the chapter.

::

    try:
        from urlparse import urlparse, urljoin
    except ImportError:
        from urllib.parse import urlparse, urljoin

    from lxml import  etree

    from ebooklib.plugins.base import BasePlugin
    from ebooklib.utils import parse_html_string

    class MyeLinks(BasePlugin):
        NAME = 'My Links'

        def html_before_write(self, book, chapter):
            try:
                tree = parse_html_string(chapter.content)
            except:
                return

            root = tree.getroottree()

            if len(root.find('body')) != 0:
                body = tree.find('body')

                for _link in body.xpath('//a'):
                    _u = urlparse(_link.get('href', ''))

                    # Let us care only for internal links at the moment
                    if _u.scheme == '':
                        if _u.path != '':
                            _link.set('href', '%s.xhtml' % _u.path)

                        if _u.fragment != '':
                            _link.set('href', urljoin(_link.get('href'), '#%s' % _u.fragment))

                        if _link.get('name') != None:
                            _link.set('id', _link.get('name'))
                            etree.strip_attributes(_link, 'name')

            chapter.content = etree.tostring(tree, pretty_print=True, encoding='utf-8')


When you want to use it just pass the list of plugins you want to use as extra option to the write_epub method
(also to read_epub method). Plugins will be executed in the order they are defined in the list.

::

    epub.write_epub('test.epub', book, {"plugins": [MyLinks()]})
