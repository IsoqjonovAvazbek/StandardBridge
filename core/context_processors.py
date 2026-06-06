def profile_completeness(request):
    if not request.user.is_authenticated:
        return {'profile_pct': 100}
    user = request.user
    if user.role == 'entrepreneur':
        fields = [user.first_name, user.last_name, user.email, user.company_name, user.phone, user.region, user.industry]
        try:
            ep = user.entrepreneur_profile
            fields += [ep.company_description]
        except Exception:
            pass
    elif user.role == 'expert':
        fields = [user.first_name, user.last_name, user.email, user.phone]
        try:
            xp = user.expert_profile
            fields += [xp.bio, xp.specializations, xp.region]
        except Exception:
            pass
    else:
        return {'profile_pct': 100}
    filled = sum(1 for f in fields if f)
    pct = int(filled / len(fields) * 100) if fields else 100
    return {'profile_pct': pct}


def notifications_count(request):
    if request.user.is_authenticated:
        from experts.models import Notification
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return {'unread_notifications': count}
    return {'unread_notifications': 0}


def language_context(request):
    from core.translations import get_translation
    from django.conf import settings as _s
    lang = request.session.get('lang', 'uz')
    return {
        'current_lang': lang,
        'T': get_translation(lang),
        'langs': [('uz', 'UZ'), ('ru', 'RU'), ('en', 'EN')],
        'GOOGLE_ANALYTICS_ID': _s.GOOGLE_ANALYTICS_ID,
    }
