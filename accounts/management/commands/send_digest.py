"""
Management command: send_digest

Foydalanuvchilarga haftalik email digest yuboradi.

Tadbirkorlar uchun:
  - Faol loyihalar ro'yxati
  - Bu hafta yangi expert javoblari

Mutaxassislar uchun:
  - Kutilayotgan loyihalar
  - O'qilmagan bildirishnomalar soni
  - Hamyon balansi

Foydalanish:
    python manage.py send_digest
    python manage.py send_digest --role entrepreneur
    python manage.py send_digest --role expert
    python manage.py send_digest --dry-run
    python manage.py send_digest --role entrepreneur --dry-run
"""

import logging
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from accounts.models import CustomUser

logger = logging.getLogger('standardbridge')

SITE_URL = settings.SITE_URL


def _get_entrepreneur_digest(user):
    """Returns (subject, html_body) for an entrepreneur."""
    from experts.models import Project, Notification

    week_ago = timezone.now() - timedelta(days=7)

    active_projects = Project.objects.filter(
        entrepreneur=user,
    ).exclude(status__in=['completed', 'cancelled']).select_related('analysis', 'expert')

    # New expert responses this week: projects that moved from pending to a later status
    new_responses = Project.objects.filter(
        entrepreneur=user,
        updated_at__gte=week_ago,
    ).exclude(status='pending').exclude(status__in=['completed', 'cancelled']).select_related('expert')

    name = user.get_full_name() or user.username
    subject = f"StandardBridge: Haftalik hisobot — {name}"

    # Build project rows HTML
    project_rows = ''
    for p in active_projects:
        std = p.analysis.target_standard if p.analysis and p.analysis.target_standard else '—'
        expert_name = p.expert.get_full_name() if p.expert else 'Belgilanmagan'
        status_display = p.get_status_display()
        project_rows += (
            f'<tr>'
            f'<td style="padding:6px 10px;border-bottom:1px solid #eee;">Loyiha #{p.pk}</td>'
            f'<td style="padding:6px 10px;border-bottom:1px solid #eee;">{std}</td>'
            f'<td style="padding:6px 10px;border-bottom:1px solid #eee;">{expert_name}</td>'
            f'<td style="padding:6px 10px;border-bottom:1px solid #eee;">{status_display}</td>'
            f'</tr>'
        )

    if not project_rows:
        project_rows = '<tr><td colspan="4" style="padding:10px;color:#888;">Faol loyihalar yo\'q</td></tr>'

    response_rows = ''
    for p in new_responses:
        expert_name = p.expert.get_full_name() if p.expert else '—'
        response_rows += (
            f'<tr>'
            f'<td style="padding:6px 10px;border-bottom:1px solid #eee;">Loyiha #{p.pk}</td>'
            f'<td style="padding:6px 10px;border-bottom:1px solid #eee;">{expert_name}</td>'
            f'<td style="padding:6px 10px;border-bottom:1px solid #eee;">{p.get_status_display()}</td>'
            f'</tr>'
        )

    if not response_rows:
        response_rows = '<tr><td colspan="3" style="padding:10px;color:#888;">Bu hafta yangi javob yo\'q</td></tr>'

    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:Arial,sans-serif;color:#333;max-width:600px;margin:0 auto;padding:20px;">

<h2 style="color:#1d4ed8;">StandardBridge — Haftalik Hisobot</h2>
<p>Assalomu alaykum, <strong>{name}</strong>!</p>
<p>Ushbu haftalik hisobot sizning faoliyatingiz bo'yicha qisqacha ma'lumot beradi.</p>

<h3 style="color:#374151;border-bottom:2px solid #e5e7eb;padding-bottom:6px;">Faol Loyihalar ({active_projects.count()} ta)</h3>
<table style="width:100%;border-collapse:collapse;font-size:14px;">
  <thead>
    <tr style="background:#f3f4f6;">
      <th style="padding:8px 10px;text-align:left;">Loyiha</th>
      <th style="padding:8px 10px;text-align:left;">Standart</th>
      <th style="padding:8px 10px;text-align:left;">Mutaxassis</th>
      <th style="padding:8px 10px;text-align:left;">Status</th>
    </tr>
  </thead>
  <tbody>{project_rows}</tbody>
</table>

<h3 style="color:#374151;border-bottom:2px solid #e5e7eb;padding-bottom:6px;margin-top:24px;">
  Bu Hafta Yangi Expert Javoblari ({new_responses.count()} ta)
</h3>
<table style="width:100%;border-collapse:collapse;font-size:14px;">
  <thead>
    <tr style="background:#f3f4f6;">
      <th style="padding:8px 10px;text-align:left;">Loyiha</th>
      <th style="padding:8px 10px;text-align:left;">Mutaxassis</th>
      <th style="padding:8px 10px;text-align:left;">Yangi status</th>
    </tr>
  </thead>
  <tbody>{response_rows}</tbody>
</table>

<div style="margin-top:28px;text-align:center;">
  <a href="{SITE_URL}/analysis/"
     style="background:#1d4ed8;color:#fff;padding:12px 28px;border-radius:8px;
            text-decoration:none;font-weight:bold;display:inline-block;">
    Loyihalarimga o'tish
  </a>
</div>

<hr style="border:none;border-top:1px solid #e5e7eb;margin:28px 0;">
<p style="color:#9ca3af;font-size:12px;">
  Ushbu xabar StandardBridge tomonidan avtomatik yuborildi.<br>
  Sayt: <a href="{SITE_URL}" style="color:#1d4ed8;">{SITE_URL}</a>
</p>

</body>
</html>
""".strip()

    return subject, html


def _get_expert_digest(user):
    """Returns (subject, html_body) for an expert."""
    from experts.models import Project, Notification, Wallet

    pending_projects = Project.objects.filter(
        expert=user,
        status='pending',
    ).select_related('entrepreneur', 'analysis')

    unread_count = Notification.objects.filter(user=user, is_read=False).count()

    try:
        wallet = Wallet.objects.get(user=user)
        balance = wallet.balance
    except Wallet.DoesNotExist:
        balance = 0

    name = user.get_full_name() or user.username
    subject = f"StandardBridge: Mutaxassis haftalik hisoboti — {name}"

    project_rows = ''
    for p in pending_projects:
        entrepreneur_name = p.entrepreneur.get_full_name() or p.entrepreneur.username
        company = p.entrepreneur.company_name or '—'
        std = p.analysis.target_standard if p.analysis and p.analysis.target_standard else '—'
        project_rows += (
            f'<tr>'
            f'<td style="padding:6px 10px;border-bottom:1px solid #eee;">Loyiha #{p.pk}</td>'
            f'<td style="padding:6px 10px;border-bottom:1px solid #eee;">{entrepreneur_name}</td>'
            f'<td style="padding:6px 10px;border-bottom:1px solid #eee;">{company}</td>'
            f'<td style="padding:6px 10px;border-bottom:1px solid #eee;">{std}</td>'
            f'</tr>'
        )

    if not project_rows:
        project_rows = '<tr><td colspan="4" style="padding:10px;color:#888;">Kutilayotgan loyihalar yo\'q</td></tr>'

    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:Arial,sans-serif;color:#333;max-width:600px;margin:0 auto;padding:20px;">

<h2 style="color:#1d4ed8;">StandardBridge — Mutaxassis Haftalik Hisoboti</h2>
<p>Assalomu alaykum, <strong>{name}</strong>!</p>

<div style="display:flex;gap:16px;margin:20px 0;">
  <div style="flex:1;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:16px;text-align:center;">
    <div style="font-size:28px;font-weight:bold;color:#16a34a;">${balance}</div>
    <div style="color:#374151;font-size:13px;margin-top:4px;">Hamyon balansi</div>
  </div>
  <div style="flex:1;background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:16px;text-align:center;">
    <div style="font-size:28px;font-weight:bold;color:#ea580c;">{unread_count}</div>
    <div style="color:#374151;font-size:13px;margin-top:4px;">O'qilmagan bildirishnomalar</div>
  </div>
  <div style="flex:1;background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:16px;text-align:center;">
    <div style="font-size:28px;font-weight:bold;color:#1d4ed8;">{pending_projects.count()}</div>
    <div style="color:#374151;font-size:13px;margin-top:4px;">Kutilayotgan loyihalar</div>
  </div>
</div>

<h3 style="color:#374151;border-bottom:2px solid #e5e7eb;padding-bottom:6px;">
  Javob Kutayotgan Loyihalar ({pending_projects.count()} ta)
</h3>
<table style="width:100%;border-collapse:collapse;font-size:14px;">
  <thead>
    <tr style="background:#f3f4f6;">
      <th style="padding:8px 10px;text-align:left;">Loyiha</th>
      <th style="padding:8px 10px;text-align:left;">Tadbirkor</th>
      <th style="padding:8px 10px;text-align:left;">Kompaniya</th>
      <th style="padding:8px 10px;text-align:left;">Standart</th>
    </tr>
  </thead>
  <tbody>{project_rows}</tbody>
</table>

<div style="margin-top:28px;text-align:center;">
  <a href="{SITE_URL}/experts/dashboard/"
     style="background:#1d4ed8;color:#fff;padding:12px 28px;border-radius:8px;
            text-decoration:none;font-weight:bold;display:inline-block;">
    Dashboard ga o'tish
  </a>
</div>

<hr style="border:none;border-top:1px solid #e5e7eb;margin:28px 0;">
<p style="color:#9ca3af;font-size:12px;">
  Ushbu xabar StandardBridge tomonidan avtomatik yuborildi.<br>
  Sayt: <a href="{SITE_URL}" style="color:#1d4ed8;">{SITE_URL}</a>
</p>

</body>
</html>
""".strip()

    return subject, html


def _send_digest_email(subject, html_body, to_email, dry_run=False, stdout=None):
    """Send (or print) a single digest email."""
    if dry_run:
        if stdout:
            stdout.write(f'\n--- DRY RUN: would send to {to_email} ---')
            stdout.write(f'Subject: {subject}')
            stdout.write(f'Body length: {len(html_body)} chars\n')
        return True

    if not settings.EMAIL_HOST_USER:
        if stdout:
            stdout.write(f'  [SKIP] EMAIL_HOST_USER sozlanmagan — {to_email}')
        return False

    try:
        send_mail(
            subject=subject,
            message='',  # plain text empty; HTML provided below
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            html_message=html_body,
            fail_silently=False,
        )
        return True
    except Exception as exc:
        logger.warning('send_digest: email yuborilmadi (%s): %s', to_email, exc)
        if stdout:
            stdout.write(f'  [ERROR] {to_email}: {exc}')
        return False


class Command(BaseCommand):
    help = (
        'Foydalanuvchilarga haftalik email digest yuboradi.\n'
        'Tadbirkorlar: faol loyihalar + bu haftagi yangi expert javoblari.\n'
        'Mutaxassislar: kutilayotgan loyihalar + o\'qilmagan bildirishnomalar + hamyon balansi.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--role',
            choices=['entrepreneur', 'expert', 'both'],
            default='both',
            help='Qaysi roldagi foydalanuvchilarga yuborish (default: both)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help='Haqiqatda yubormaydi — stdout ga chiqaradi',
        )

    def handle(self, *args, **options):
        role = options['role']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN rejimi — email yuborilyapti emas.'))

        sent = 0
        skipped = 0
        errors = 0

        # ── Entrepreneurs ──────────────────────────────────────────
        if role in ('entrepreneur', 'both'):
            self.stdout.write('\n[Tadbirkorlar]')
            entrepreneurs = CustomUser.objects.filter(
                role='entrepreneur',
                is_active=True,
                is_email_verified=True,
            ).exclude(email='')

            self.stdout.write(f'  Topildi: {entrepreneurs.count()} ta tadbirkor')

            for user in entrepreneurs:
                try:
                    subject, html_body = _get_entrepreneur_digest(user)
                    ok = _send_digest_email(
                        subject, html_body, user.email,
                        dry_run=dry_run, stdout=self.stdout,
                    )
                    if ok:
                        sent += 1
                        if not dry_run:
                            self.stdout.write(f'  [OK] {user.email}')
                    else:
                        errors += 1
                except Exception as exc:
                    errors += 1
                    logger.exception('send_digest entrepreneur error user=%s: %s', user.pk, exc)
                    self.stdout.write(self.style.ERROR(f'  [FAIL] user #{user.pk} — {exc}'))

        # ── Experts ────────────────────────────────────────────────
        if role in ('expert', 'both'):
            self.stdout.write('\n[Mutaxassislar]')
            experts = CustomUser.objects.filter(
                role='expert',
                is_active=True,
                is_email_verified=True,
            ).exclude(email='')

            self.stdout.write(f'  Topildi: {experts.count()} ta mutaxassis')

            for user in experts:
                try:
                    subject, html_body = _get_expert_digest(user)
                    ok = _send_digest_email(
                        subject, html_body, user.email,
                        dry_run=dry_run, stdout=self.stdout,
                    )
                    if ok:
                        sent += 1
                        if not dry_run:
                            self.stdout.write(f'  [OK] {user.email}')
                    else:
                        errors += 1
                except Exception as exc:
                    errors += 1
                    logger.exception('send_digest expert error user=%s: %s', user.pk, exc)
                    self.stdout.write(self.style.ERROR(f'  [FAIL] user #{user.pk} — {exc}'))

        # ── Summary ────────────────────────────────────────────────
        self.stdout.write('')
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'DRY RUN natija: {sent} ta email yuborilar edi. Xato: {errors}.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'Digest yuborildi: {sent} ta. Xato: {errors}.'
            ))
