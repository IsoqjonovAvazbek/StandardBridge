"""
Telegram bot webhook'ni avtomatik ro'yxatdan o'tkazadi.
start.sh da chaqiriladi — har deploy da idempotent ishlaydi.
"""
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Telegram bot webhook URL ni Telegram serveriga ro\'yxatdan o\'tkazadi'

    def handle(self, *args, **options):
        token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '').strip()
        secret = getattr(settings, 'TELEGRAM_WEBHOOK_SECRET', '')

        if not token:
            self.stdout.write(self.style.WARNING('TELEGRAM_BOT_TOKEN topilmadi — o\'tkazib yuborildi'))
            return

        # Webhook URL ni aniqlash: CSRF_TRUSTED_ORIGINS dan olish
        base_url = ''
        trusted = getattr(settings, 'CSRF_TRUSTED_ORIGINS', [])
        for origin in trusted:
            if 'railway.app' in origin or 'http' in origin:
                base_url = origin.rstrip('/')
                break

        if not base_url:
            self.stdout.write(self.style.WARNING(
                'CSRF_TRUSTED_ORIGINS ichida Railway URL topilmadi — webhook o\'rnatilmadi'
            ))
            return

        webhook_url = f'{base_url}/accounts/telegram/webhook/'

        import urllib.request
        import urllib.parse
        import json

        api_url = f'https://api.telegram.org/bot{token}/setWebhook'
        params = {'url': webhook_url, 'drop_pending_updates': True}
        if secret:
            params['secret_token'] = secret

        try:
            data = urllib.parse.urlencode(params).encode()
            req = urllib.request.Request(api_url, data=data, method='POST')
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read())
            if result.get('ok'):
                self.stdout.write(self.style.SUCCESS(
                    f'Telegram webhook o\'rnatildi: {webhook_url}'
                ))
            else:
                self.stdout.write(self.style.ERROR(
                    f'Telegram webhook xato: {result.get("description", result)}'
                ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Telegram webhook urinish xato: {e}'))
