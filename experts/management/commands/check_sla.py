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
                    title=f'SLA ogohlantirish — Loyiha #{project.pk}',
                    message=(
                        f'Loyiha #{project.pk} uchun mutaxassis '
                        f'{hours_left:.0f} soat ichida javob bermasa, '
                        f'loyiha bekor qilinadi va to\'lov qaytariladi.'
                    ),
                )
                self._send_email(
                    to=project.entrepreneur.email,
                    subject=f'[StandartBridge] SLA ogohlantirish — Loyiha #{project.pk}',
                    body=(
                        f'Assalomu alaykum, {project.entrepreneur.get_full_name()}!\n\n'
                        f'Loyiha #{project.pk} '
                        f'({project.analysis.local_standard.code} → {project.analysis.target_standard.code}) '
                        f'uchun mutaxassis hali javob bermadi.\n\n'
                        f'Qolgan vaqt: {hours_left:.0f} soat\n'
                        f'Muddat: {project.sla_deadline.strftime("%d.%m.%Y %H:%M")}\n\n'
                        f'Agar mutaxassis belgilangan muddatda javob bermasa, '
                        f'to\'lov avtomatik qaytariladi.\n\n'
                        f'Hurmat bilan,\nStandartBridge jamoasi'
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
                    title=f'Loyiha #{project.pk} bekor qilindi',
                    message=(
                        f'Mutaxassis belgilangan muddat ichida javob bermadi. '
                        f'Loyiha bekor qilindi. To\'lov qaytariladi.'
                    ),
                )
                self._send_email(
                    to=project.entrepreneur.email,
                    subject=f'[StandartBridge] Loyiha #{project.pk} bekor qilindi',
                    body=(
                        f'Assalomu alaykum, {project.entrepreneur.get_full_name()}!\n\n'
                        f'Afsuski, loyiha #{project.pk} '
                        f'({project.analysis.local_standard.code} → {project.analysis.target_standard.code}) '
                        f'uchun mutaxassis belgilangan muddat ({project.sla_hours} soat) ichida '
                        f'javob bermadi.\n\n'
                        f'Loyiha avtomatik ravishda bekor qilindi.\n'
                        f'Agar to\'lov amalga oshirilgan bo\'lsa, u qaytariladi.\n\n'
                        f'Boshqa mutaxassis tanlash uchun:\n'
                        f'https://standartbridge.uz/experts/\n\n'
                        f'Hurmat bilan,\nStandartBridge jamoasi'
                    ),
                )

                # Notify expert if assigned
                if project.expert:
                    self._notify(
                        user=project.expert,
                        title=f'Loyiha #{project.pk} SLA muddati o\'tdi',
                        message=(
                            f'SLA muddati o\'tganligi sababli loyiha bekor qilindi. '
                            f'Keyingi safar vaqtida javob bering.'
                        ),
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
                    title=notif_title,
                    message=(
                        f'Loyiha #{project.pk} uchun ish muddati '
                        f'({project.work_deadline.strftime("%d.%m.%Y")}) o\'tib ketdi. '
                        f'Mutaxassis bilan bog\'laning yoki nizo oching.'
                    ),
                )
                self.stdout.write(
                    self.style.WARNING(f'  [WORK OVERDUE] Loyiha #{project.pk}')
                )

        # ── F-7: review statusda > 2 kun tadbirkorga eslatma ────────────────
        review_stale = Project.objects.filter(
            status='review',
        ).select_related('entrepreneur', 'expert')

        for project in review_stale:
            # Only notify if in review for more than 2 days
            if project.updated_at and (now - project.updated_at).days >= 2:
                notif_title = f'Ishni qabul qilmadingiz — Loyiha #{project.pk}'
                already = Notification.objects.filter(
                    user=project.entrepreneur, title=notif_title
                ).exists()
                if not already:
                    self._notify(
                        user=project.entrepreneur,
                        title=notif_title,
                        message=(
                            f'Mutaxassis ishni {project.updated_at.strftime("%d.%m.%Y")} da '
                            f'tekshiruvga topshirdi. Ishni ko\'rib chiqing va qabul qiling yoki '
                            f'qayta ishlashni so\'rang.'
                        ),
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
