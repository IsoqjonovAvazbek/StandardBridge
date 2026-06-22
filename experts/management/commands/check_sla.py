"""
Management command: check_sla

Run this periodically (e.g. every hour via cron or Windows Task Scheduler):
    python manage.py check_sla

What it does:
  1. Finds pending projects whose sla_deadline has passed → marks sla_status='breached'
  2. Finds pending projects with < 24 h left → marks sla_status='warning'
  3. Sends email notification to entrepreneur on breach
  4. Auto-refunds payment if one exists (sets Payment.status='refunded')
  5. Marks the project 'cancelled' so it leaves the expert's queue
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from experts.models import Project, Payment, Notification

SITE_URL = settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'https://standardbridge.uz'
from core.translations import notif_text as _nl


class Command(BaseCommand):
    help = 'Check SLA deadlines for pending projects'

    def handle(self, *args, **options):
        now = timezone.now()
        checked = 0
        warned = 0
        breached = 0

        pending_projects = Project.objects.filter(
            status='pending',
            sla_deadline__isnull=False,
        ).select_related('entrepreneur', 'expert', 'analysis__local_standard', 'analysis__target_standard')

        for project in pending_projects:
            hours_left = (project.sla_deadline - now).total_seconds() / 3600
            checked += 1

            # ── WARNING (< 24 h left, not yet breached) ──────────────────────
            if 0 < hours_left <= 24 and project.sla_status != 'warning':
                project.sla_status = 'warning'
                project.save(update_fields=['sla_status'])
                warned += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'  [WARNING] Loyiha #{project.pk} — {hours_left:.1f} soat qoldi'
                    )
                )
                # Notify entrepreneur
                self._notify(
                    user=project.entrepreneur,
                    title=_nl(project.entrepreneur,
                        f'SLA ogohlantirish — Loyiha #{project.pk}',
                        f'Предупреждение SLA — Проект #{project.pk}',
                        f'SLA warning — Project #{project.pk}'),
                    message=_nl(project.entrepreneur,
                        f'Loyiha #{project.pk} uchun mutaxassis {hours_left:.0f} soat ichida javob bermasa, loyiha bekor qilinadi va to\'lov qaytariladi.',
                        f'Если эксперт не ответит на проект #{project.pk} в течение {hours_left:.0f} ч., проект будет отменён и оплата возвращена.',
                        f'If the expert does not respond to project #{project.pk} within {hours_left:.0f} hours, it will be cancelled and payment refunded.'),
                )
                self._send_email(
                    to=project.entrepreneur.email,
                    subject=f'[StandardBridge] SLA ogohlantirish — Loyiha #{project.pk}',
                    body=(
                        f'Assalomu alaykum, {project.entrepreneur.get_full_name()}!\n\n'
                        f'Loyiha #{project.pk} '
                        f'({project.analysis.local_standard.code} → {project.analysis.target_standard.code}) '
                        f'uchun mutaxassis hali javob bermadi.\n\n'
                        f'Qolgan vaqt: {hours_left:.0f} soat\n'
                        f'Muddat: {project.sla_deadline.strftime("%d.%m.%Y %H:%M")}\n\n'
                        f'Agar mutaxassis belgilangan muddatda javob bermasa, '
                        f'to\'lov avtomatik qaytariladi.\n\n'
                        f'Hurmat bilan,\nStandardBridge jamoasi'
                    ),
                )

            # ── BREACHED (deadline passed) ────────────────────────────────────
            elif hours_left <= 0 and project.sla_status != 'breached':
                project.sla_status = 'breached'
                project.status = 'cancelled'
                project.save(update_fields=['sla_status', 'status'])
                breached += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'  [BREACHED] Loyiha #{project.pk} — muddat o\'tdi, bekor qilindi'
                    )
                )

                # Auto-refund payment if exists
                try:
                    payment = project.payment
                    if payment.status == 'held':
                        payment.status = 'refunded'
                        payment.save(update_fields=['status'])
                        self.stdout.write(
                            f'    To\'lov #{payment.pk} qaytarildi (${payment.amount})'
                        )
                except Payment.DoesNotExist:
                    pass

                # Notify entrepreneur
                self._notify(
                    user=project.entrepreneur,
                    title=_nl(project.entrepreneur,
                        f'Loyiha #{project.pk} bekor qilindi',
                        f'Проект #{project.pk} отменён',
                        f'Project #{project.pk} cancelled'),
                    message=_nl(project.entrepreneur,
                        f'Mutaxassis belgilangan muddat ichida javob bermadi. Loyiha bekor qilindi. To\'lov qaytariladi.',
                        f'Эксперт не ответил в установленный срок. Проект отменён. Оплата будет возвращена.',
                        f'The expert did not respond in time. Project cancelled. Payment will be refunded.'),
                )
                self._send_email(
                    to=project.entrepreneur.email,
                    subject=f'[StandardBridge] Loyiha #{project.pk} bekor qilindi',
                    body=(
                        f'Assalomu alaykum, {project.entrepreneur.get_full_name()}!\n\n'
                        f'Afsuski, loyiha #{project.pk} '
                        f'({project.analysis.local_standard.code} → {project.analysis.target_standard.code}) '
                        f'uchun mutaxassis belgilangan muddat ({project.sla_hours} soat) ichida '
                        f'javob bermadi.\n\n'
                        f'Loyiha avtomatik ravishda bekor qilindi.\n'
                        f'Agar to\'lov amalga oshirilgan bo\'lsa, u qaytariladi.\n\n'
                        f'Boshqa mutaxassis tanlash uchun:\n'
                        f'{SITE_URL}/experts/\n\n'
                        f'Hurmat bilan,\nStandardBridge jamoasi'
                    ),
                )

                # Notify expert if assigned
                if project.expert:
                    self._notify(
                        user=project.expert,
                        title=_nl(project.expert,
                            f'Loyiha #{project.pk} SLA muddati o\'tdi',
                            f'По проекту #{project.pk} истёк срок SLA',
                            f'Project #{project.pk} SLA deadline breached'),
                        message=_nl(project.expert,
                            f'SLA muddati o\'tganligi sababli loyiha bekor qilindi. Keyingi safar vaqtida javob bering.',
                            f'Проект отменён в связи с нарушением срока SLA. В следующий раз отвечайте вовремя.',
                            f'Project cancelled due to SLA breach. Please respond on time in the future.'),
                    )

        # ── F-5: in_progress loyihalarda work_deadline o'tdi ────────────────
        from datetime import timedelta
        overdue_work = Project.objects.filter(
            status='in_progress',
            work_deadline__isnull=False,
            work_deadline__lt=now,
        ).select_related('entrepreneur', 'expert')

        for project in overdue_work:
            notif_title = f'Ish muddati o\'tdi — Loyiha #{project.pk}'
            already = Notification.objects.filter(
                user=project.entrepreneur, title=notif_title
            ).exists()
            if not already:
                self._notify(
                    user=project.entrepreneur,
                    title=_nl(project.entrepreneur,
                        f'Ish muddati o\'tdi — Loyiha #{project.pk}',
                        f'Срок работы истёк — Проект #{project.pk}',
                        f'Work deadline overdue — Project #{project.pk}'),
                    message=_nl(project.entrepreneur,
                        f'Loyiha #{project.pk} uchun ish muddati ({project.work_deadline.strftime("%d.%m.%Y")}) o\'tib ketdi. Mutaxassis bilan bog\'laning yoki nizo oching.',
                        f'Срок работы по проекту #{project.pk} ({project.work_deadline.strftime("%d.%m.%Y")}) истёк. Свяжитесь с экспертом или откройте спор.',
                        f'Work deadline for project #{project.pk} ({project.work_deadline.strftime("%d.%m.%Y")}) has passed. Contact the expert or open a dispute.'),
                )
                self.stdout.write(
                    self.style.WARNING(f'  [WORK OVERDUE] Loyiha #{project.pk}')
                )

        # ── F-7: review statusda > 2 kun tadbirkorga eslatma ────────────────
        review_stale = Project.objects.filter(
            status='review',
        ).select_related('entrepreneur', 'expert')

        for project in review_stale:
            # review_at maydoni bor bo'lsa shu bo'yicha, yo'q bo'lsa updated_at fallback
            review_ts = project.review_at or project.updated_at
            if review_ts and (now - review_ts).days >= 2:
                notif_title = f'Ishni qabul qilmadingiz — Loyiha #{project.pk}'
                already = Notification.objects.filter(
                    user=project.entrepreneur, title=notif_title
                ).exists()
                if not already:
                    self._notify(
                        user=project.entrepreneur,
                        title=_nl(project.entrepreneur,
                            f'Ishni qabul qilmadingiz — Loyiha #{project.pk}',
                            f'Вы не приняли работу — Проект #{project.pk}',
                            f'Work not accepted — Project #{project.pk}'),
                        message=_nl(project.entrepreneur,
                            f'Mutaxassis ishni {review_ts.strftime("%d.%m.%Y")} da tekshiruvga topshirdi. Ishni ko\'rib chiqing va qabul qiling yoki qayta ishlashni so\'rang.',
                            f'Эксперт передал работу на проверку {review_ts.strftime("%d.%m.%Y")}. Проверьте и примите или запросите доработку.',
                            f'Expert submitted work for review on {review_ts.strftime("%d.%m.%Y")}. Check and accept it or request revision.'),
                    )
                    self.stdout.write(
                        self.style.WARNING(f'  [REVIEW STALE] Loyiha #{project.pk}')
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\ncheck_sla tugadi: {checked} tekshirildi, '
                f'{warned} ogohlantirish, {breached} muddati o\'tdi.'
            )
        )

    # ─── helpers ─────────────────────────────────────────────────────────────

    def _notify(self, user, title, message):
        """Create in-app Notification."""
        Notification.objects.create(user=user, title=title, message=message)

    def _send_email(self, to, subject, body):
        """Send email, silently ignore failures."""
        if not to or not getattr(settings, 'EMAIL_HOST_USER', None):
            return
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to],
                fail_silently=True,
            )
        except Exception as e:
            import logging
            logging.getLogger('standardbridge').warning('SLA email yuborilmadi (%s): %s', to, e)
