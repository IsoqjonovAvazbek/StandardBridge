import threading
import logging
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger('standardbridge')

SITE_URL = 'http://standardbridge.up.railway.app'

# Email content by language
_CONTENT = {
    'welcome': {
        'uz': {
            'subject': "StandartBridge ga xush kelibsiz!",
            'role_expert': "Mutaxassis",
            'role_ent': "Tadbirkor",
            'next_expert': "Endi siz tahlillarni ko'rib, narx belgilab, loyihalarni boshqarishingiz mumkin.",
            'next_ent': "Endi siz gap-analiz o'tkazib, mutaxassislar bilan ishlashingiz mumkin.",
            'body': "StandartBridge platformasiga {role} sifatida muvaffaqiyatli ro'yxatdan o'tdingiz.\n\n{next_step}\n\nPlatforma: {url}",
        },
        'ru': {
            'subject': "Добро пожаловать на StandartBridge!",
            'role_expert': "Эксперт",
            'role_ent': "Предприниматель",
            'next_expert': "Теперь вы можете просматривать анализы, устанавливать цены и управлять проектами.",
            'next_ent': "Теперь вы можете проводить гэп-анализ и работать с экспертами.",
            'body': "Вы успешно зарегистрировались на платформе StandartBridge как {role}.\n\n{next_step}\n\nПлатформа: {url}",
        },
        'en': {
            'subject': "Welcome to StandartBridge!",
            'role_expert': "Expert",
            'role_ent': "Entrepreneur",
            'next_expert': "You can now review analyses, set prices, and manage projects.",
            'next_ent': "You can now run gap analyses and work with certified experts.",
            'body': "You have successfully registered on StandartBridge as {role}.\n\n{next_step}\n\nPlatform: {url}",
        },
    },
    'project_to_expert': {
        'uz': {
            'subject': "Yangi loyiha #{pk} — StandartBridge",
            'body': "{entrepreneur} ({company}) sizga yangi tahlil yubordi.\n\nLoyiha: #{pk}\nSanoat: {industry}\nStandart: {standard}\n\nNarx belgilash uchun:\n{url}",
        },
        'ru': {
            'subject': "Новый проект #{pk} — StandartBridge",
            'body': "{entrepreneur} ({company}) отправил вам новый анализ.\n\nПроект: #{pk}\nОтрасль: {industry}\nСтандарт: {standard}\n\nУстановить цену:\n{url}",
        },
        'en': {
            'subject': "New project #{pk} — StandartBridge",
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
            'subject': "Profilingiz tasdiqlandi — StandartBridge",
            'body': "Profilingiz StandartBridge administrator tomonidan tasdiqlandi.\n\nEndi siz platformada ko'rinasiz va tadbirkorlardan loyihalar qabul qila olasiz.\n\nProfilingiz: {url}",
        },
        'ru': {
            'subject': "Ваш профиль подтверждён — StandartBridge",
            'body': "Ваш профиль был подтверждён администратором StandartBridge.\n\nТеперь вы отображаетесь на платформе и можете получать заявки от предпринимателей.\n\nВаш профиль: {url}",
        },
        'en': {
            'subject': "Your profile is verified — StandartBridge",
            'body': "Your profile has been verified by a StandartBridge administrator.\n\nYou are now visible on the platform and can receive project requests.\n\nYour profile: {url}",
        },
    },
    'withdrawal_approved': {
        'uz': {
            'subject': "Pul yechish tasdiqlandi — StandartBridge",
            'body': "${amount} yechish so'rovingiz tasdiqlandi.\n\nKarta: {card}\n{note}\n\nMablag' 1-3 ish kuni ichida kartangizga o'tkaziladi.\n\nHamyon: {url}",
        },
        'ru': {
            'subject': "Вывод средств подтверждён — StandartBridge",
            'body': "Ваша заявка на вывод ${amount} подтверждена.\n\nКарта: {card}\n{note}\n\nСредства поступят на карту в течение 1-3 рабочих дней.\n\nКошелёк: {url}",
        },
        'en': {
            'subject': "Withdrawal approved — StandartBridge",
            'body': "Your withdrawal request of ${amount} has been approved.\n\nCard: {card}\n{note}\n\nFunds will arrive within 1-3 business days.\n\nWallet: {url}",
        },
    },
    'withdrawal_rejected': {
        'uz': {
            'subject': "Pul yechish rad etildi — StandartBridge",
            'body': "${amount} yechish so'rovingiz rad etildi.\n\nSabab: {reason}\n\n${amount} hamyoningizga qaytarildi.\n\nHamyon: {url}",
        },
        'ru': {
            'subject': "Вывод средств отклонён — StandartBridge",
            'body': "Ваша заявка на вывод ${amount} была отклонена.\n\nПричина: {reason}\n\n${amount} возвращены на ваш кошелёк.\n\nКошелёк: {url}",
        },
        'en': {
            'subject': "Withdrawal rejected — StandartBridge",
            'body': "Your withdrawal request of ${amount} was rejected.\n\nReason: {reason}\n\n${amount} has been returned to your wallet.\n\nWallet: {url}",
        },
    },
    'dispute_opened': {
        'uz': {
            'subject': "Loyiha #{pk} bo'yicha nizo ochildi — StandartBridge",
            'body': "Tadbirkor {opener} loyiha #{pk} bo'yicha nizo ochdi.\n\nSabab: {reason}\n\nAdministrator nizoni ko'rib chiqadi.\n\nLoyiha sahifasi:\n{url}",
        },
        'ru': {
            'subject': "По проекту #{pk} открыт спор — StandartBridge",
            'body': "Предприниматель {opener} открыл спор по проекту #{pk}.\n\nПричина: {reason}\n\nАдминистратор рассмотрит спор.\n\nСтраница проекта:\n{url}",
        },
        'en': {
            'subject': "Dispute opened for project #{pk} — StandartBridge",
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
            'subject': "Gap-tahlil tayyor — {std} | StandartBridge",
            'body': "{std} standarti bo'yicha gap-tahlilingiz tayyor.\n\nNatijalar:\n- Aniqlangan gaplar: {gaps} ta{time_line}\n\nTo'liq hisobot va yo'l-xaritani ko'rish uchun:\n{url}\n\nKeyingi qadam — mos mutaxassis topib, loyiha boshlash.",
        },
        'ru': {
            'subject': "Гэп-анализ готов — {std} | StandartBridge",
            'body': "Ваш гэп-анализ по стандарту {std} готов.\n\nРезультаты:\n- Выявленных несоответствий: {gaps}{time_line}\n\nПолный отчёт и дорожная карта:\n{url}\n\nСледующий шаг — найти подходящего эксперта и начать проект.",
        },
        'en': {
            'subject': "Gap analysis ready — {std} | StandartBridge",
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
    'uz': "Hurmat bilan,\nStandartBridge jamoasi",
    'ru': "С уважением,\nКоманда StandartBridge",
    'en': "Best regards,\nThe StandartBridge Team",
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


def send_expert_verified(expert_user):
    subject, body = _build(
        'expert_verified', expert_user,
        url=f"{SITE_URL}/experts/profile/",
    )
    _send(subject, body, expert_user.email)


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


def send_counter_offer_to_expert(project):
    """Tadbirkor qarshi taklif yuborganda expertga email."""
    expert = project.expert
    if not expert or not expert.email:
        return
    url = f"{SITE_URL}/experts/projects/{project.pk}/"
    subject = f"StandartBridge: Loyiha #{project.pk} — qarshi taklif"
    body = (
        f"Salom {expert.get_full_name()},\n\n"
        f"Tadbirkor loyiha #{project.pk} uchun qarshi taklif yubordi:\n"
        f"  Yangi narx taklifi: ${project.counter_price}\n"
        f"  Izoh: {project.counter_message or '—'}\n\n"
        f"Qabul qilish yoki rad etish uchun:\n{url}\n\n"
        "StandartBridge jamoasi"
    )
    _send(subject, body, expert.email)


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
