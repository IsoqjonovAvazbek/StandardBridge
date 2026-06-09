"""Model choices kodlarini joriy tilga tarjima qiluvchi simple_tag.

Ishlatish:
    {% load labels %}
    {% label nc.severity %}        — joriy til (request session) bo'yicha
    {% label project.status %}
    {{ text|render_md }}           — AI/markdown matnini HTML ga o'tkazish
"""
from django import template
from django.utils.safestring import mark_safe
from django.utils import timezone
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


@register.filter(name='time_ago')
def time_ago(dt):
    """{{ expert.user.last_login|time_ago }} → '3 kun oldin', '2 soat oldin', etc."""
    if not dt:
        return ''
    now = timezone.now()
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    diff = now - dt
    seconds = int(diff.total_seconds())
    if seconds < 60:
        return 'Hozirgina'
    if seconds < 3600:
        m = seconds // 60
        return f'{m} daqiqa oldin'
    if seconds < 86400:
        h = seconds // 3600
        return f'{h} soat oldin'
    days = diff.days
    if days < 7:
        return f'{days} kun oldin'
    if days < 30:
        w = days // 7
        return f'{w} hafta oldin'
    if days < 365:
        mo = days // 30
        return f'{mo} oy oldin'
    yr = days // 365
    return f'{yr} yil oldin'


@register.filter(name='hours_since')
def hours_since(dt):
    """{{ project.created_at|hours_since }} → 51.3  (soatlar soni, float)."""
    if not dt:
        return 0
    now = timezone.now()
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    return (now - dt).total_seconds() / 3600


@register.filter(name='days_left')
def days_left(dt):
    """{{ project.work_deadline|days_left }} → 5  (musbat = qolgan kunlar, manfiy = o'tgan)."""
    if not dt:
        return None
    now = timezone.now()
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    return (dt - now).days


@register.filter(name='uz_date')
def uz_date(dt):
    """{{ analysis.created_at|uz_date }} → '8 iyun 2026' (o'zbek tilida sana)."""
    if not dt:
        return ''
    _MONTHS = ['yanvar', 'fevral', 'mart', 'aprel', 'may', 'iyun',
               'iyul', 'avgust', 'sentabr', 'oktabr', 'noyabr', 'dekabr']
    d = dt.date() if hasattr(dt, 'date') else dt
    return f'{d.day} {_MONTHS[d.month - 1]} {d.year}'


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
