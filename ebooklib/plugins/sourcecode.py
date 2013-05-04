from ebooklib.plugins.base import BasePlugin

class SourceHighlighter(BasePlugin):    
    def __init__(self):
        pass

    def process_html(self, book, chapter):
        from lxml import html, etree

        from pygments import highlight
        from pygments.formatters import HtmlFormatter

        from ebooklib import epub

        utf8_parser = html.HTMLParser(encoding='utf-8')
        tree = html.document_fromstring(chapter.content, parser=utf8_parser)
#        tree = html.document_fromstring(chapter.content)
        root = tree.getroottree()

        had_source = False

        if len(root.find('body')) != 0:
            body = tree.find('body')
            # check for embeded source
            for source in body.xpath('//pre[contains(@class,"source-")]'):
                css_class = source.get('class')

                source_text = (source.text or '') + ''.join([html.tostring(child) for child in source.iterchildren()])

                if 'source-python' in css_class:
                    from pygments.lexers import PythonLexer

#                    _text =  highlight(source_text, PythonLexer(), HtmlFormatter(linenos="inline"))
                    _text =  highlight(source_text, PythonLexer(), HtmlFormatter())

                if 'source-css' in css_class:
                    from pygments.lexers import CssLexer

                    _text =  highlight(source_text, CssLexer(), HtmlFormatter())

                _parent = source.getparent()
                _parent.replace(source, etree.XML(_text))

                had_source = True

        if had_source:
            chapter.add_link(href="style/code.css", rel="stylesheet", type="text/css")
            chapter.content = etree.tostring(tree, pretty_print=True, encoding='utf-8')        

