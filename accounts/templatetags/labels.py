"""Model choices kodlarini joriy tilga tarjima qiluvchi simple_tag.

Ishlatish:
    {% load labels %}
    {% label nc.severity %}        — joriy til (request session) bo'yicha
    {% label project.status %}
"""
from django import template
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
