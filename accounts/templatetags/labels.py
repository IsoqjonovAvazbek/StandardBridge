"""Template filtri: model choices kodlarini joriy tilga tarjima qiladi.

Ishlatish:
    {% load labels %}
    {{ nc.severity|label }}        — joriy til (request session) bo'yicha
    {{ project.status|label }}
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
