#!/usr/local/bin/python2.7
#coding:utf-8

import re
import logging
import HTMLParser

import misaka
import pygments
import docutils, docutils.core
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import DiffLexer, get_lexer_by_name, guess_lexer_for_filename

logger = logging.getLogger(__name__)

CODE_AREA = r'''<pre><code class="([0-9a-zA-Z._-]+)">(.+?)</code></pre>'''

RE_CHECKBOX_IN_HTML = re.compile('<li>\[[x\s]\].+</li>')
RE_CHECKBOX_IN_TEXT = re.compile('- (\[[x\s]\]).+')
CHECKED = '[x]'
UNCHECKED = '[ ]'

def render_diff(content):
    lexer = DiffLexer()
    content = content.replace("\ No newline at end of file\n", "")
    html = highlight(content, lexer,  HtmlFormatter(linenos=True, lineanchors='L', anchorlinenos=True))
    return html

def render_code(path, content):
    if path.rsplit('.', 1)[-1] in ['md', 'markdown', 'mkd']:
        return render_wrapper(render_checklist(render_markdown(path, content)))
    elif path.rsplit('.', 1)[-1] in ['rst', ]:
        return render_wrapper(render_rst(path, content))
    else:
        try:
            lexer = guess_lexer_for_filename(path, content)
        except pygments.util.ClassNotFound:
            lexer = get_lexer_by_name("text")
        html = highlight(content, lexer,  HtmlFormatter(linenos=True, lineanchors='L', anchorlinenos=True))

    return html

def render_markdown(path, content):
    html = misaka.html(content, extensions=\
            misaka.EXT_AUTOLINK|misaka.EXT_LAX_HTML_BLOCKS|misaka.EXT_SPACE_HEADERS|\
            misaka.EXT_SUPERSCRIPT|misaka.EXT_FENCED_CODE|misaka.EXT_NO_INTRA_EMPHASIS|\
            misaka.EXT_STRIKETHROUGH|misaka.EXT_TABLES)
    def _r(m):
        try:
            lexer_name = m.group(1)
            code = m.group(2)
            lexer = get_lexer_by_name(lexer_name)
            code = HTMLParser.HTMLParser().unescape(code)
            return highlight(code, lexer, HtmlFormatter())
        except pygments.util.ClassNotFound:
            return m.group()

    p = re.compile(CODE_AREA, re.DOTALL)
    html = p.sub(lambda m: _r(m), html)
    return html

def render_checklist(content):
    i = 0
    while 1:
        m = re.search(RE_CHECKBOX_IN_HTML, content)
        if not m:
            break
        t = m.group(0).lstrip('<li>').rstrip('</li>')
        if t.startswith(CHECKED):
            checked_idx = content.find(CHECKED)
            content = content[:checked_idx - len('<li>')] + \
                      '<li><label><input type="checkbox" data-item-index="%d" checked> ' % i + \
                      t.lstrip(CHECKED).strip() + '</label></li>' + \
                      content[checked_idx + len(t) + len('</li>'):]
        else:
            unchecked_idx = content.find(UNCHECKED)
            content = content[:unchecked_idx - len('<li>')] + \
                      '<li><label><input type="checkbox" data-item-index="%d"> ' % i + \
                      t.lstrip(UNCHECKED).strip() + '</label></li>' + \
                      content[unchecked_idx + len(t) + len('</li>'):]
        i += 1
    return content

def render_rst(path, content):
    try:
        return docutils.core.publish_parts(content, writer_name='html')['html_body']
    except docutils.ApplicationError:
        pass

    try:
        lexer = guess_lexer_for_filename(path, content)
    except pygments.util.ClassNotFound:
        lexer = get_lexer_by_name("python")
    html = highlight(content, lexer,  HtmlFormatter(linenos=True, lineanchors='L', anchorlinenos=True))
    return html

def render_wrapper(content, c="markdown"):
    content = content.replace("<script>", " <script>")
    return r'''<div class="%s">%s</div>''' % (c, content)

