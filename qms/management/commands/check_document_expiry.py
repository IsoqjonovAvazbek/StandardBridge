"""
Management command: check_document_expiry

Finds QMS documents whose expiry_date is within 30 days (or already expired)
and sends a one-time Notification (+ email) to the owning company.

Run periodically (e.g. daily cron / Windows Task Scheduler):
    python manage.py check_document_expiry

Use --days N to change the warning window (default 30).
Use --reset to clear the notified flag (for testing).
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from qms.models import QMSDocument
from experts.models import Notification
from experts.emails import _send
from core.translations import notif_text as _nl


class Command(BaseCommand):
    help = 'QMS hujjatlari muddati tugashidan oldin eslatma yuboradi'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=30)
        parser.add_argument('--reset', action='store_true')

    def handle(self, *args, **options):
        if options['reset']:
            n = QMSDocument.objects.filter(expiry_notified=True).update(expiry_notified=False)
            self.stdout.write(self.style.WARNING(f'{n} ta hujjat flagi tozalandi.'))
            return

        days = options['days']
        today = timezone.now().date()
        deadline = today + timedelta(days=days)

        docs = QMSDocument.objects.filter(
            is_active=True,
            expiry_notified=False,
            expiry_date__isnull=False,
            expiry_date__lte=deadline,
        )

        sent = 0
        for doc in docs:
            left = (doc.expiry_date - today).days
            if left < 0:
                title = _nl(doc.company,
                    'QMS hujjat muddati tugagan',
                    'Срок действия документа QMS истёк',
                    'QMS document expired')
                msg = _nl(doc.company,
                    f'"{doc.title}" (v{doc.version}) hujjatining amal qilish muddati {abs(left)} kun oldin tugagan. Yangilang.',
                    f'Срок действия документа "{doc.title}" (v{doc.version}) истёк {abs(left)} дней назад. Обновите его.',
                    f'Document "{doc.title}" (v{doc.version}) expired {abs(left)} days ago. Please renew.')
            else:
                title = _nl(doc.company,
                    'QMS hujjat muddati tugayapti',
                    'Срок действия документа QMS истекает',
                    'QMS document expiry approaching')
                msg = _nl(doc.company,
                    f'"{doc.title}" (v{doc.version}) hujjatining muddati {left} kundan keyin tugaydi ({doc.expiry_date:%d.%m.%Y}).',
                    f'Срок действия документа "{doc.title}" (v{doc.version}) истекает через {left} дней ({doc.expiry_date:%d.%m.%Y}).',
                    f'Document "{doc.title}" (v{doc.version}) expires in {left} days ({doc.expiry_date:%d.%m.%Y}).')

            Notification.objects.create(user=doc.company, title=title, message=msg)

            _send(
                subject=f'[StandardBridge] {title}',
                message=msg,
                to_email=getattr(doc.company, 'email', ''),
            )

            doc.expiry_notified = True
            doc.save(update_fields=['expiry_notified'])
            sent += 1
            self.stdout.write(f'  → {doc.company} : {doc.title} ({left} kun)')

        self.stdout.write(self.style.SUCCESS(f'{sent} ta eslatma yuborildi.'))
