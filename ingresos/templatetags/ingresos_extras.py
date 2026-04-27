import re

from django import template

register = template.Library()

_PCT = re.compile(r'\b\d+(?:[.,]\d+)?\s*%')


@register.filter
def sin_porcentaje(text):
    """Quita patrones tipo '70%', '0.7 %', '6,2%' del texto."""
    if not text:
        return ''
    return _PCT.sub('', str(text)).strip(' -–—,;:')
