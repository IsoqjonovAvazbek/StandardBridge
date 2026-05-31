def notifications_count(request):
    if request.user.is_authenticated:
        from experts.models import Notification
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return {'unread_notifications': count}
    return {'unread_notifications': 0}


def language_context(request):
    from core.translations import get_translation
    lang = request.session.get('lang', 'uz')
    return {
        'current_lang': lang,
        'T': get_translation(lang),
        'langs': [('uz', 'UZ'), ('ru', 'RU'), ('en', 'EN')],
    }
