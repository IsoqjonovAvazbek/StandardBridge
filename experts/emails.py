import threading
import logging
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger('standardbridge')


def _send_sync(subject, message, to_email):
    """Haqiqiy SMTP yuborish (background threadda chaqiriladi)."""
    from django.db import close_old_connections
    close_old_connections()
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=True,
        )
    except Exception as e:
        logger.warning('Email yuborilmadi (%s): %s', to_email, e)


def _send(subject, message, to_email):
    """Emailni FON threadda yuboradi — foydalanuvchi SMTP javobini kutmaydi.

    Avval sinxron edi: Gmail SMTP sekin javob bersa sahifa 30-60s qotardi.
    Endi so'rov darrov qaytadi, email orqada yuboriladi.
    """
    if not to_email or not settings.EMAIL_HOST_USER:
        return
    thread = threading.Thread(
        target=_send_sync,
        args=(subject, message, to_email),
        daemon=True,
    )
    thread.start()


def send_welcome_email(user):
    role = "Mutaxassis" if user.role == "expert" else "Tadbirkor"
    if user.role == "expert":
        next_step = "Endi siz tahlillarni korib, narx belgilab, loyihalarni boshqarishingiz mumkin."
    else:
        next_step = "Endi siz gap-analiz otkazib, mutaxassislar bilan ishlashingiz mumkin."
    _send(
        subject="StandartBridge ga xush kelibsiz!",
        message=f"""Assalomu alaykum, {user.get_full_name()}!

StandartBridge platformasiga {role} sifatida muvaffaqiyatli royxatdan otdingiz.

{next_step}

Platforma: http://standartbridge.uz

Hurmat bilan,
StandartBridge jamoasi""",
        to_email=user.email,
    )


def send_project_to_expert(project):
    expert = project.expert
    entrepreneur = project.entrepreneur
    _send(
        subject=f"Yangi loyiha #{project.pk} — StandartBridge",
        message=f"""Assalomu alaykum, {expert.get_full_name()}!

{entrepreneur.get_full_name()} ({entrepreneur.company_name}) sizga yangi tahlil yubordi.

Loyiha: #{project.pk}
Sanoat: {project.analysis.industry}
Standart: {project.analysis.target_standard}

Narx belgilash uchun platformaga kiring:
http://standartbridge.uz/experts/projects/{project.pk}/price/

Hurmat bilan,
StandartBridge jamoasi""",
        to_email=expert.email,
    )


def send_price_set_to_entrepreneur(project):
    entrepreneur = project.entrepreneur
    _send(
        subject=f"Mutaxassis narx belgiladi — Loyiha #{project.pk}",
        message=f"""Assalomu alaykum, {entrepreneur.get_full_name()}!

{project.expert.get_full_name()} loyiha #{project.pk} uchun narx belgiladi:

Narx: ${project.expert_price}
Muddat: {project.expert_days} kun
Xabar: {project.expert_message or 'Yo\'q'}

Narxni qabul qilish uchun:
http://standartbridge.uz/experts/projects/{project.pk}/

Hurmat bilan,
StandartBridge jamoasi""",
        to_email=entrepreneur.email,
    )


def send_payment_confirmed_to_expert(project, payment):
    expert = project.expert
    _send(
        subject=f"To'lov amalga oshirildi — Loyiha #{project.pk}",
        message=f"""Assalomu alaykum, {expert.get_full_name()}!

Loyiha #{project.pk} uchun to'lov muvaffaqiyatli amalga oshirildi.

To'lov miqdori: ${payment.amount}
Sizga (80%%): ${payment.expert_amount}
Ish boshlashingiz mumkin!

Loyiha sahifasi:
http://standartbridge.uz/experts/projects/{project.pk}/

Hurmat bilan,
StandartBridge jamoasi""",
        to_email=expert.email,
    )


def send_project_completed_to_entrepreneur(project, payment):
    entrepreneur = project.entrepreneur
    _send(
        subject=f"Loyiha yakunlandi — #{project.pk}",
        message=f"""Assalomu alaykum, {entrepreneur.get_full_name()}!

Loyiha #{project.pk} muvaffaqiyatli yakunlandi.

Mutaxassis: {project.expert.get_full_name()}
To'langan: ${payment.amount}

Iltimos, mutaxassisga baho bering:
http://standartbridge.uz/experts/projects/{project.pk}/review/

Hurmat bilan,
StandartBridge jamoasi""",
        to_email=entrepreneur.email,
    )


def send_expert_verified(expert_user):
    _send(
        subject="Profilingiz tasdiqlandi — StandartBridge",
        message=f"""Assalomu alaykum, {expert_user.get_full_name()}!

Profilingiz StandartBridge administrator tomonidan tasdiqlandi.

Endi siz platformada ko'rinasiz va tadbirkorlardan loyihalar qabul qila olasiz.

Profilingiz: http://standartbridge.uz/experts/profile/

Hurmat bilan,
StandartBridge jamoasi""",
        to_email=expert_user.email,
    )


def send_withdrawal_approved(wr):
    """Admin pul yechish so'rovini tasdiqlaganda expertga xabar."""
    user = wr.wallet.user
    plain = wr.card_number_plain
    card_display = f'*{plain[-4:]}' if plain and plain.isdigit() and len(plain) >= 4 else '—'
    _send(
        subject=f"Pul yechish tasdiqlandi — StandartBridge",
        message=f"""Assalomu alaykum, {user.get_full_name()}!

${wr.amount} yechish so'rovingiz tasdiqlandi.

Karta: {card_display}
{f"Admin izohi: {wr.admin_note}" if wr.admin_note else ""}

Mablag' 1-3 ish kuni ichida kartangizga o'tkaziladi.

Hurmat bilan,
StandartBridge jamoasi""",
        to_email=user.email,
    )


def send_withdrawal_rejected(wr):
    """Admin pul yechish so'rovini rad etganda expertga xabar."""
    user = wr.wallet.user
    _send(
        subject=f"Pul yechish rad etildi — StandartBridge",
        message=f"""Assalomu alaykum, {user.get_full_name()}!

${wr.amount} yechish so'rovingiz rad etildi.

Sabab: {wr.admin_note or "Ko'rsatilmadi"}

${wr.amount} hamyoningizga qaytarildi.

Hamyon: http://standartbridge.uz/experts/wallet/

Hurmat bilan,
StandartBridge jamoasi""",
        to_email=user.email,
    )


def send_dispute_opened(dispute):
    """Tadbirkor nizo ochganda expertga xabar."""
    project = dispute.project
    if not project.expert:
        return
    _send(
        subject=f"Loyiha #{project.pk} bo'yicha nizo ochildi — StandartBridge",
        message=f"""Assalomu alaykum, {project.expert.get_full_name()}!

Tadbirkor {dispute.opened_by.get_full_name()} loyiha #{project.pk} bo'yicha nizo ochdi.

Sabab: {dispute.reason[:300]}

Administrator nizoni ko'rib chiqadi. Loyiha sahifasi:
http://standartbridge.uz/experts/projects/{project.pk}/

Hurmat bilan,
StandartBridge jamoasi""",
        to_email=project.expert.email,
    )


def send_analysis_ready_email(analysis):
    """Gap-tahlil tayyor bo'lganda tadbirkorga email."""
    user = analysis.entrepreneur
    gap_count = analysis.gaps.count()
    std = analysis.target_standard.code if analysis.target_standard else '—'
    readiness_line = ''
    if analysis.ai_result:
        total_days = analysis.ai_result.get('total_days', 0)
        if total_days:
            readiness_line = f"\nTaxminiy tayyorgarlik muddati: {total_days} kun"
    _send(
        subject=f"Gap-tahlil tayyor — {std} | StandartBridge",
        message=f"""Assalomu alaykum, {user.get_full_name()}!

{std} standarti bo'yicha gap-tahlilingiz tayyor.

Natijalar:
- Aniqlangan gaplar: {gap_count} ta{readiness_line}

To'liq hisobot va yo'l-xaritani ko'rish uchun:
http://standartbridge.up.railway.app/analysis/{analysis.pk}/

Keyingi qadam — mos mutaxassis topib, loyiha boshlash.

Hurmat bilan,
StandartBridge jamoasi""",
        to_email=user.email,
    )


def send_dispute_resolved(dispute, decision):
    """Admin nizoni hal qilganda ikki tomonga ham xabar."""
    project = dispute.project
    msg = f"""Assalomu alaykum!

Loyiha #{project.pk} bo'yicha nizo hal qilindi.

Admin qarori: {decision[:300]}

Loyiha sahifasi:
http://standartbridge.uz/experts/projects/{project.pk}/

Hurmat bilan,
StandartBridge jamoasi"""
    _send(
        subject=f"Nizo hal qilindi — Loyiha #{project.pk}",
        message=msg,
        to_email=dispute.opened_by.email,
    )
    if project.expert:
        _send(
            subject=f"Nizo hal qilindi — Loyiha #{project.pk}",
            message=msg,
            to_email=project.expert.email,
        )
