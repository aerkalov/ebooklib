# This file is part of EbookLib.
# Copyright (c) 2013 Aleksandar Erkalovic <aerkalov@gmail.com>
#
# EbookLib is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# EbookLib is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with EbookLib.  If not, see <http://www.gnu.org/licenses/>.

from ebooklib.plugins.base import BasePlugin
from ebooklib.utils import parse_html_string

class SourceHighlighter(BasePlugin):    
    def __init__(self):
        pass

    def html_before_write(self, book, chapter):
        from lxml import etree, html

        from pygments import highlight
        from pygments.formatters import HtmlFormatter

        from ebooklib import epub

        try:
            tree = parse_html_string(chapter.content)
        except:
            return

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

