"""
Custom filters for Jinja.

linebreaks(br) code is based on an example from Jinja docs.

"""
import re
from jinja2 import evalcontextfilter, Markup, escape

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

@evalcontextfilter
def linebreaksbr(eval_ctx, value):
    result = escape(value).replace('\n', Markup('<br>\n'))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result

@evalcontextfilter
def linebreaks(eval_ctx, value):
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', Markup('<br>\n'))
                          for p in _paragraph_re.split(escape(value)))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result
