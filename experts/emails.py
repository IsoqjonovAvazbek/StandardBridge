import threading
import logging
import html as _html
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger('standardbridge')


def _e(value) -> str:
    """HTML entity escape — user-supplied string'larni Telegram HTML modeda himoyalaydi."""
    return _html.escape(str(value))


def send_telegram(chat_id: str, text: str) -> None:
    """Telegram orqali xabar yuboradi (fon thread, xato bo'lsa loglaydi)."""
    if not chat_id:
        return
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    if not token:
        return

    def _send_tg():
        try:
            import requests as _req
            _req.post(
                f'https://api.telegram.org/bot{token}/sendMessage',
                json={'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'},
                timeout=8,
            )
        except Exception as e:
            logger.warning('Telegram xabar yuborilmadi (%s): %s', chat_id, e)

    threading.Thread(target=_send_tg, daemon=True).start()


def _tg(user, text: str) -> None:
    """User'ga Telegram xabari yuborish — chat_id mavjud bo'lsa."""
    chat_id = getattr(user, 'telegram_chat_id', '')
    if chat_id:
        send_telegram(chat_id, text)

from django.conf import settings as _django_settings
SITE_URL = getattr(_django_settings, 'SITE_URL', 'https://standardbridge.uz')

# Email content by language
_CONTENT = {
    'welcome': {
        'uz': {
            'subject': "StandardBridge ga xush kelibsiz!",
            'role_expert': "Mutaxassis",
            'role_ent': "Tadbirkor",
            'next_expert': "Endi siz tahlillarni ko'rib, narx belgilab, loyihalarni boshqarishingiz mumkin.",
            'next_ent': "Endi siz gap-analiz o'tkazib, mutaxassislar bilan ishlashingiz mumkin.",
            'body': "StandardBridge platformasiga {role} sifatida muvaffaqiyatli ro'yxatdan o'tdingiz.\n\n{next_step}\n\nPlatforma: {url}",
        },
        'ru': {
            'subject': "Добро пожаловать на StandardBridge!",
            'role_expert': "Эксперт",
            'role_ent': "Предприниматель",
            'next_expert': "Теперь вы можете просматривать анализы, устанавливать цены и управлять проектами.",
            'next_ent': "Теперь вы можете проводить гэп-анализ и работать с экспертами.",
            'body': "Вы успешно зарегистрировались на платформе StandardBridge как {role}.\n\n{next_step}\n\nПлатформа: {url}",
        },
        'en': {
            'subject': "Welcome to StandardBridge!",
            'role_expert': "Expert",
            'role_ent': "Entrepreneur",
            'next_expert': "You can now review analyses, set prices, and manage projects.",
            'next_ent': "You can now run gap analyses and work with certified experts.",
            'body': "You have successfully registered on StandardBridge as {role}.\n\n{next_step}\n\nPlatform: {url}",
        },
    },
    'project_to_expert': {
        'uz': {
            'subject': "Yangi loyiha #{pk} — StandardBridge",
            'body': "{entrepreneur} ({company}) sizga yangi tahlil yubordi.\n\nLoyiha: #{pk}\nSanoat: {industry}\nStandart: {standard}\n\nNarx belgilash uchun:\n{url}",
        },
        'ru': {
            'subject': "Новый проект #{pk} — StandardBridge",
            'body': "{entrepreneur} ({company}) отправил вам новый анализ.\n\nПроект: #{pk}\nОтрасль: {industry}\nСтандарт: {standard}\n\nУстановить цену:\n{url}",
        },
        'en': {
            'subject': "New project #{pk} — StandardBridge",
            'body': "{entrepreneur} ({company}) sent you a new analysis.\n\nProject: #{pk}\nIndustry: {industry}\nStandard: {standard}\n\nSet your price:\n{url}",
        },
    },
    'price_set': {
        'uz': {
            'subject': "Mutaxassis narx belgiladi — Loyiha #{pk}",
            'body': "{expert} loyiha #{pk} uchun narx belgiladi:\n\nNarx: ${price}\nMuddat: {days} kun\nXabar: {message}\n\nNarxni qabul qilish uchun:\n{url}",
        },
        'ru': {
            'subject': "Эксперт установил цену — Проект #{pk}",
            'body': "{expert} установил цену для проекта #{pk}:\n\nЦена: ${price}\nСрок: {days} дней\nСообщение: {message}\n\nПринять цену:\n{url}",
        },
        'en': {
            'subject': "Expert set a price — Project #{pk}",
            'body': "{expert} set a price for project #{pk}:\n\nPrice: ${price}\nDuration: {days} days\nMessage: {message}\n\nAccept the price:\n{url}",
        },
    },
    'payment_confirmed': {
        'uz': {
            'subject': "To'lov amalga oshirildi — Loyiha #{pk}",
            'body': "Loyiha #{pk} uchun to'lov muvaffaqiyatli amalga oshirildi.\n\nTo'lov miqdori: ${amount}\nSizga (80%%): ${expert_amount}\n\nIsh boshlashingiz mumkin!\n\nLoyiha sahifasi:\n{url}",
        },
        'ru': {
            'subject': "Оплата произведена — Проект #{pk}",
            'body': "Оплата по проекту #{pk} прошла успешно.\n\nСумма: ${amount}\nВам (80%%): ${expert_amount}\n\nМожете приступать к работе!\n\nСтраница проекта:\n{url}",
        },
        'en': {
            'subject': "Payment received — Project #{pk}",
            'body': "Payment for project #{pk} was successful.\n\nAmount: ${amount}\nYour share (80%%): ${expert_amount}\n\nYou may start work!\n\nProject page:\n{url}",
        },
    },
    'project_completed': {
        'uz': {
            'subject': "Loyiha yakunlandi — #{pk}",
            'body': "Loyiha #{pk} muvaffaqiyatli yakunlandi.\n\nMutaxassis: {expert}\nTo'langan: ${amount}\n\nIltimos, mutaxassisga baho bering:\n{url}",
        },
        'ru': {
            'subject': "Проект завершён — #{pk}",
            'body': "Проект #{pk} успешно завершён.\n\nЭксперт: {expert}\nОплачено: ${amount}\n\nПожалуйста, оцените эксперта:\n{url}",
        },
        'en': {
            'subject': "Project completed — #{pk}",
            'body': "Project #{pk} has been successfully completed.\n\nExpert: {expert}\nPaid: ${amount}\n\nPlease leave a review:\n{url}",
        },
    },
    'expert_verified': {
        'uz': {
            'subject': "Profilingiz tasdiqlandi — StandardBridge",
            'body': "Profilingiz StandardBridge administrator tomonidan tasdiqlandi.\n\nEndi siz platformada ko'rinasiz va tadbirkorlardan loyihalar qabul qila olasiz.\n\nProfilingiz: {url}",
        },
        'ru': {
            'subject': "Ваш профиль подтверждён — StandardBridge",
            'body': "Ваш профиль был подтверждён администратором StandardBridge.\n\nТеперь вы отображаетесь на платформе и можете получать заявки от предпринимателей.\n\nВаш профиль: {url}",
        },
        'en': {
            'subject': "Your profile is verified — StandardBridge",
            'body': "Your profile has been verified by a StandardBridge administrator.\n\nYou are now visible on the platform and can receive project requests.\n\nYour profile: {url}",
        },
    },
    'withdrawal_approved': {
        'uz': {
            'subject': "Pul yechish tasdiqlandi — StandardBridge",
            'body': "${amount} yechish so'rovingiz tasdiqlandi.\n\nKarta: {card}\n{note}\n\nMablag' 1-3 ish kuni ichida kartangizga o'tkaziladi.\n\nHamyon: {url}",
        },
        'ru': {
            'subject': "Вывод средств подтверждён — StandardBridge",
            'body': "Ваша заявка на вывод ${amount} подтверждена.\n\nКарта: {card}\n{note}\n\nСредства поступят на карту в течение 1-3 рабочих дней.\n\nКошелёк: {url}",
        },
        'en': {
            'subject': "Withdrawal approved — StandardBridge",
            'body': "Your withdrawal request of ${amount} has been approved.\n\nCard: {card}\n{note}\n\nFunds will arrive within 1-3 business days.\n\nWallet: {url}",
        },
    },
    'withdrawal_rejected': {
        'uz': {
            'subject': "Pul yechish rad etildi — StandardBridge",
            'body': "${amount} yechish so'rovingiz rad etildi.\n\nSabab: {reason}\n\n${amount} hamyoningizga qaytarildi.\n\nHamyon: {url}",
        },
        'ru': {
            'subject': "Вывод средств отклонён — StandardBridge",
            'body': "Ваша заявка на вывод ${amount} была отклонена.\n\nПричина: {reason}\n\n${amount} возвращены на ваш кошелёк.\n\nКошелёк: {url}",
        },
        'en': {
            'subject': "Withdrawal rejected — StandardBridge",
            'body': "Your withdrawal request of ${amount} was rejected.\n\nReason: {reason}\n\n${amount} has been returned to your wallet.\n\nWallet: {url}",
        },
    },
    'dispute_opened': {
        'uz': {
            'subject': "Loyiha #{pk} bo'yicha nizo ochildi — StandardBridge",
            'body': "Tadbirkor {opener} loyiha #{pk} bo'yicha nizo ochdi.\n\nSabab: {reason}\n\nAdministrator nizoni ko'rib chiqadi.\n\nLoyiha sahifasi:\n{url}",
        },
        'ru': {
            'subject': "По проекту #{pk} открыт спор — StandardBridge",
            'body': "Предприниматель {opener} открыл спор по проекту #{pk}.\n\nПричина: {reason}\n\nАдминистратор рассмотрит спор.\n\nСтраница проекта:\n{url}",
        },
        'en': {
            'subject': "Dispute opened for project #{pk} — StandardBridge",
            'body': "Entrepreneur {opener} opened a dispute for project #{pk}.\n\nReason: {reason}\n\nAn administrator will review the dispute.\n\nProject page:\n{url}",
        },
    },
    'dispute_resolved': {
        'uz': {
            'subject': "Nizo hal qilindi — Loyiha #{pk}",
            'body': "Loyiha #{pk} bo'yicha nizo hal qilindi.\n\nAdmin qarori: {decision}\n\nLoyiha sahifasi:\n{url}",
        },
        'ru': {
            'subject': "Спор урегулирован — Проект #{pk}",
            'body': "Спор по проекту #{pk} урегулирован.\n\nРешение администратора: {decision}\n\nСтраница проекта:\n{url}",
        },
        'en': {
            'subject': "Dispute resolved — Project #{pk}",
            'body': "The dispute for project #{pk} has been resolved.\n\nAdmin decision: {decision}\n\nProject page:\n{url}",
        },
    },
    'analysis_ready': {
        'uz': {
            'subject': "Gap-tahlil tayyor — {std} | StandardBridge",
            'body': "{std} standarti bo'yicha gap-tahlilingiz tayyor.\n\nNatijalar:\n- Aniqlangan gaplar: {gaps} ta{time_line}\n\nTo'liq hisobot va yo'l-xaritani ko'rish uchun:\n{url}\n\nKeyingi qadam — mos mutaxassis topib, loyiha boshlash.",
        },
        'ru': {
            'subject': "Гэп-анализ готов — {std} | StandardBridge",
            'body': "Ваш гэп-анализ по стандарту {std} готов.\n\nРезультаты:\n- Выявленных несоответствий: {gaps}{time_line}\n\nПолный отчёт и дорожная карта:\n{url}\n\nСледующий шаг — найти подходящего эксперта и начать проект.",
        },
        'en': {
            'subject': "Gap analysis ready — {std} | StandardBridge",
            'body': "Your gap analysis for {std} is ready.\n\nResults:\n- Gaps identified: {gaps}{time_line}\n\nFull report and roadmap:\n{url}\n\nNext step — find a qualified expert and start the project.",
        },
    },
}

GREETING = {
    'uz': "Assalomu alaykum, {name}!",
    'ru': "Здравствуйте, {name}!",
    'en': "Hello, {name}!",
}
REGARDS = {
    'uz': "Hurmat bilan,\nStandardBridge jamoasi",
    'ru': "С уважением,\nКоманда StandardBridge",
    'en': "Best regards,\nThe StandardBridge Team",
}


def _get_lang(user):
    return getattr(user, 'preferred_language', None) or 'uz'


def _build(key, user, **kwargs):
    lang = _get_lang(user)
    if lang not in ('uz', 'ru', 'en'):
        lang = 'uz'
    c = _CONTENT[key][lang]
    greeting = GREETING[lang].format(name=user.get_full_name())
    body = c['body'].format(**kwargs)
    regards = REGARDS[lang]
    return c['subject'].format(**kwargs), f"{greeting}\n\n{body}\n\n{regards}"


def _send_sync(subject, message, to_email):
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
    if not to_email or not settings.EMAIL_HOST_USER:
        return
    threading.Thread(target=_send_sync, args=(subject, message, to_email), daemon=True).start()


def send_welcome_email(user):
    lang = _get_lang(user)
    c = _CONTENT['welcome'][lang]
    if user.role == 'expert':
        role = c['role_expert']
        next_step = c['next_expert']
    else:
        role = c['role_ent']
        next_step = c['next_ent']
    greeting = GREETING[lang].format(name=user.get_full_name())
    body = c['body'].format(role=role, next_step=next_step, url=SITE_URL)
    regards = REGARDS[lang]
    _send(c['subject'], f"{greeting}\n\n{body}\n\n{regards}", user.email)


def send_project_to_expert(project):
    expert = project.expert
    entrepreneur = project.entrepreneur
    subject, body = _build(
        'project_to_expert', expert,
        pk=project.pk,
        entrepreneur=entrepreneur.get_full_name(),
        company=entrepreneur.company_name or entrepreneur.username,
        industry=project.analysis.industry,
        standard=project.analysis.target_standard,
        url=f"{SITE_URL}/experts/projects/{project.pk}/price/",
    )
    _send(subject, body, expert.email)
    _tg(expert, (
        f"📋 <b>Yangi loyiha #{project.pk}!</b>\n"
        f"👤 {_e(entrepreneur.get_full_name())} ({_e(entrepreneur.company_name or entrepreneur.username)})\n"
        f"📌 {_e(project.analysis.industry)} · {_e(project.analysis.target_standard)}\n"
        f"🔗 {SITE_URL}/experts/projects/{project.pk}/price/"
    ))


def send_price_set_to_entrepreneur(project):
    entrepreneur = project.entrepreneur
    subject, body = _build(
        'price_set', entrepreneur,
        pk=project.pk,
        expert=project.expert.get_full_name(),
        price=project.expert_price,
        days=project.expert_days,
        message=project.expert_message or '—',
        url=f"{SITE_URL}/experts/projects/{project.pk}/",
    )
    _send(subject, body, entrepreneur.email)
    _tg(entrepreneur, (
        f"💰 <b>Mutaxassis narx belgiladi — Loyiha #{project.pk}</b>\n"
        f"👤 {_e(project.expert.get_full_name())}\n"
        f"💵 ${_e(project.expert_price)} · {_e(project.expert_days)} kun\n"
        f"🔗 {SITE_URL}/experts/projects/{project.pk}/"
    ))


def send_payment_confirmed_to_expert(project, payment):
    expert = project.expert
    subject, body = _build(
        'payment_confirmed', expert,
        pk=project.pk,
        amount=payment.amount,
        expert_amount=payment.expert_amount,
        url=f"{SITE_URL}/experts/projects/{project.pk}/",
    )
    _send(subject, body, expert.email)
    _tg(expert, (
        f"✅ <b>To'lov amalga oshirildi — Loyiha #{project.pk}</b>\n"
        f"💵 Jami: ${_e(payment.amount)} · Sizga (80%): ${_e(payment.expert_amount)}\n"
        f"🚀 Ish boshlashingiz mumkin!\n"
        f"🔗 {SITE_URL}/experts/projects/{project.pk}/"
    ))


def send_project_completed_to_entrepreneur(project, payment):
    entrepreneur = project.entrepreneur
    subject, body = _build(
        'project_completed', entrepreneur,
        pk=project.pk,
        expert=project.expert.get_full_name(),
        amount=payment.amount,
        url=f"{SITE_URL}/experts/projects/{project.pk}/review/",
    )
    _send(subject, body, entrepreneur.email)
    _tg(entrepreneur, (
        f"🎉 <b>Loyiha #{project.pk} yakunlandi!</b>\n"
        f"👤 Mutaxassis: {_e(project.expert.get_full_name())}\n"
        f"💵 To'langan: ${_e(payment.amount)}\n"
        f"⭐ Iltimos, baho bering:\n{SITE_URL}/experts/projects/{project.pk}/review/"
    ))


def send_expert_verified(expert_user):
    subject, body = _build(
        'expert_verified', expert_user,
        url=f"{SITE_URL}/experts/profile/",
    )
    _send(subject, body, expert_user.email)
    _tg(expert_user, (
        f"✅ <b>Profilingiz tasdiqlandi!</b>\n"
        f"Endi siz StandardBridge platformasida ko'rinasiz va loyihalar qabul qila olasiz.\n"
        f"🔗 {SITE_URL}/experts/profile/"
    ))


def send_withdrawal_approved(wr):
    user = wr.wallet.user
    plain = wr.card_number_plain
    card_display = f'*{plain[-4:]}' if plain and plain.isdigit() and len(plain) >= 4 else '—'
    lang = _get_lang(user)
    note_prefix = {'uz': 'Admin izohi', 'ru': 'Комментарий', 'en': 'Note'}.get(lang, 'Note')
    note = f"{note_prefix}: {wr.admin_note}" if wr.admin_note else ''
    subject, body = _build(
        'withdrawal_approved', user,
        amount=wr.amount,
        card=card_display,
        note=note,
        url=f"{SITE_URL}/experts/wallet/",
    )
    _send(subject, body, user.email)
    last4 = plain[-4:] if plain and len(plain) >= 4 else '??'
    _tg(user, (
        f"✅ <b>Pul yechish tasdiqlandi!</b>\n"
        f"💵 ${_e(wr.amount)} kartangizga o'tkazildi (*{_e(last4)})\n"
        f"🔗 {SITE_URL}/experts/wallet/"
    ))


def send_withdrawal_rejected(wr):
    user = wr.wallet.user
    lang = _get_lang(user)
    no_reason = {'uz': "Ko'rsatilmadi", 'ru': 'Не указана', 'en': 'Not provided'}.get(lang, '—')
    subject, body = _build(
        'withdrawal_rejected', user,
        amount=wr.amount,
        reason=wr.admin_note or no_reason,
        url=f"{SITE_URL}/experts/wallet/",
    )
    _send(subject, body, user.email)
    _tg(user, (
        f"❌ <b>Pul yechish rad etildi</b>\n"
        f"💵 ${_e(wr.amount)} hamyoningizga qaytarildi.\n"
        f"📝 Sabab: {_e(wr.admin_note or no_reason)}\n"
        f"🔗 {SITE_URL}/experts/wallet/"
    ))


def send_dispute_opened(dispute):
    project = dispute.project
    if not project.expert:
        return
    subject, body = _build(
        'dispute_opened', project.expert,
        pk=project.pk,
        opener=dispute.opened_by.get_full_name(),
        reason=dispute.reason[:300],
        url=f"{SITE_URL}/experts/projects/{project.pk}/",
    )
    _send(subject, body, project.expert.email)
    _tg(project.expert, (
        f"⚠️ <b>Loyiha #{project.pk} bo'yicha nizo ochildi</b>\n"
        f"👤 {_e(dispute.opened_by.get_full_name())}\n"
        f"📝 Sabab: {_e(dispute.reason[:120])}\n"
        f"Admin ko'rib chiqadi.\n"
        f"🔗 {SITE_URL}/experts/projects/{project.pk}/"
    ))


def send_analysis_ready_email(analysis):
    user = analysis.entrepreneur
    gap_count = analysis.gaps.count()
    std = analysis.target_standard.code if analysis.target_standard else '—'
    lang = _get_lang(user)
    total_days = analysis.ai_result.get('total_days', 0) if analysis.ai_result else 0
    if total_days:
        tl_tmpl = {
            'uz': f"\n- Taxminiy tayyorgarlik muddati: {total_days} kun",
            'ru': f"\n- Примерный срок подготовки: {total_days} дней",
            'en': f"\n- Estimated preparation time: {total_days} days",
        }
        time_line = tl_tmpl.get(lang, '')
    else:
        time_line = ''
    subject, body = _build(
        'analysis_ready', user,
        std=std,
        gaps=gap_count,
        time_line=time_line,
        url=f"{SITE_URL}/analysis/{analysis.pk}/",
    )
    _send(subject, body, user.email)
    _tg(user, (
        f"🤖 <b>Gap-tahlil tayyor — {_e(std)}</b>\n"
        f"📊 Aniqlangan bo'shliqlar: {_e(gap_count)} ta"
        + (f" · {_e(total_days)} kun" if total_days else "") + "\n"
        f"🔗 {SITE_URL}/analysis/{analysis.pk}/"
    ))


def send_counter_offer_to_expert(project):
    """Tadbirkor qarshi taklif yuborganda expertga email."""
    expert = project.expert
    if not expert or not expert.email:
        return
    url = f"{SITE_URL}/experts/projects/{project.pk}/"
    subject = f"StandardBridge: Loyiha #{project.pk} — qarshi taklif"
    body = (
        f"Salom {expert.get_full_name()},\n\n"
        f"Tadbirkor loyiha #{project.pk} uchun qarshi taklif yubordi:\n"
        f"  Yangi narx taklifi: ${project.counter_price}\n"
        f"  Izoh: {project.counter_message or '—'}\n\n"
        f"Qabul qilish yoki rad etish uchun:\n{url}\n\n"
        "StandardBridge jamoasi"
    )
    _send(subject, body, expert.email)
    _tg(expert, (
        f"🔄 <b>Qarshi taklif — Loyiha #{project.pk}</b>\n"
        f"💵 Yangi taklif: ${_e(project.counter_price)}\n"
        f"💬 {_e(project.counter_message or '—')}\n"
        f"🔗 {url}"
    ))


def send_scope_request_to_entrepreneur(scope_req):
    """Mutaxassis qo'shimcha ish so'rovi yuborganda tadbirkorga email."""
    project = scope_req.project
    ent = project.entrepreneur
    if not ent or not ent.email:
        return
    url = f"{SITE_URL}/experts/projects/{project.pk}/"
    subject = f"StandardBridge: Loyiha #{project.pk} — qo'shimcha ish so'rovi"
    body = (
        f"Salom {ent.get_full_name()},\n\n"
        f"Mutaxassis {scope_req.expert.get_full_name()} loyiha #{project.pk} uchun "
        f"qo'shimcha ish so'rovi yubordi:\n\n"
        f"  Qo'shimcha narx: +${scope_req.extra_price}\n"
        f"  Sabab: {scope_req.reason}\n\n"
        f"Qabul qilish yoki rad etish uchun:\n{url}\n\n"
        "StandardBridge jamoasi"
    )
    _send(subject, body, ent.email)
    _tg(ent, (
        f"➕ <b>Qo'shimcha ish so'rovi — Loyiha #{project.pk}</b>\n"
        f"👤 {_e(scope_req.expert.get_full_name())}\n"
        f"💵 +${_e(scope_req.extra_price)} · {_e(scope_req.reason[:100])}\n"
        f"🔗 {url}"
    ))


def send_scope_request_response_to_expert(scope_req):
    """Tadbirkor qo'shimcha so'rovga javob berganda mutaxassisga email."""
    expert = scope_req.expert
    if not expert or not expert.email:
        return
    project = scope_req.project
    url = f"{SITE_URL}/experts/projects/{project.pk}/"
    if scope_req.status == 'accepted':
        status_text = "QABUL QILINDI ✓"
        detail = f"Qo'shimcha ${scope_req.extra_price} escrow'ga qo'shilishi uchun tadbirkordan to'lov kutiladi."
    else:
        status_text = "RAD ETILDI ✗"
        detail = "Dastlabki narx bo'yicha ishni davom ettiring."
    subject = f"StandardBridge: Loyiha #{project.pk} — so'rovingizga javob"
    body = (
        f"Salom {expert.get_full_name()},\n\n"
        f"Loyiha #{project.pk} bo'yicha qo'shimcha ish so'rovingiz: {status_text}\n\n"
        f"{detail}\n\n"
        f"Loyiha sahifasi:\n{url}\n\n"
        "StandardBridge jamoasi"
    )
    _send(subject, body, expert.email)
    if scope_req.status == 'accepted':
        _tg_icon, _tg_status, _tg_detail = (
            "✅", "qabul qilindi",
            "💵 Tadbirkordan qoʻshimcha toʻlov keladi."
        )
    else:
        _tg_icon, _tg_status, _tg_detail = (
            "❌", "rad etildi",
            "📌 Dastlabki narx boʻyicha davom eting."
        )
    _tg(expert, (
        f"{_tg_icon} <b>Qoʻshimcha soʻrovi {_tg_status} — Loyiha #{project.pk}</b>\n"
        f"{_tg_detail}\n"
        f"🔗 {url}"
    ))


def send_dispute_resolved(dispute, decision):
    project = dispute.project
    pk = project.pk
    project_url = f"{SITE_URL}/experts/projects/{pk}/"

    for recipient in [dispute.opened_by, project.expert]:
        if not recipient:
            continue
        subject, body = _build(
            'dispute_resolved', recipient,
            pk=pk,
            decision=decision[:300],
            url=project_url,
        )
        _send(subject, body, recipient.email)
        _tg(recipient, (
            f"⚖️ <b>Nizo hal qilindi — Loyiha #{pk}</b>\n"
            f"📝 Admin qarori: {_e(decision[:150])}\n"
            f"🔗 {project_url}"
        ))
