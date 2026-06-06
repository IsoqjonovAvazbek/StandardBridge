import markdown as _md
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name='render_md')
def render_md(value):
    """Markdown matnini xavfsiz HTML ga o'tkazadi."""
    if not value:
        return ''
    html = _md.markdown(
        value,
        extensions=['tables', 'fenced_code', 'nl2br', 'sane_lists'],
    )
    return mark_safe(html)
