"""Model choices kodlarini joriy tilga tarjima qiluvchi simple_tag.

Ishlatish:
    {% load labels %}
    {% label nc.severity %}        — joriy til (request session) bo'yicha
    {% label project.status %}
    {{ text|render_md }}           — AI/markdown matnini HTML ga o'tkazish
"""
from django import template
from django.utils.safestring import mark_safe
from core.translations import get_choice_label

register = template.Library()


@register.simple_tag(takes_context=True)
def label(context, code):
    """{% label nc.severity %} — joriy tilga tarjima."""
    request = context.get('request')
    lang = 'uz'
    if request is not None:
        lang = request.session.get('lang', 'uz')
    return get_choice_label(code, lang)


@register.filter(name='render_md')
def render_md(value):
    """AI markdown matnini xavfsiz HTML ga o'tkazadi.
    Ishlatish: {{ post.content|render_md }}  yoki  {{ summary|render_md }}
    """
    if not value:
        return ''
    import markdown as _md
    html = _md.markdown(
        str(value),
        extensions=['tables', 'fenced_code', 'nl2br', 'sane_lists'],
    )
    return mark_safe(html)
