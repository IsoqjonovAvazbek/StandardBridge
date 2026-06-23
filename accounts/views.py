from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.http import JsonResponse, HttpResponseRedirect
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.views import PasswordResetView as _DjangoPasswordResetView
from datetime import timedelta
from urllib.parse import urlparse
import logging
import threading

logger = logging.getLogger('standardbridge')
from core.translations import notif_text as _nl
from .models import CustomUser, ExpertProfile, EntrepreneurProfile
from experts.emails import send_welcome_email, send_expert_verified


class PasswordResetView(_DjangoPasswordResetView):
    """Parol tiklash emailini background threadda yuboradi — UI bloklanmaydi."""
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_url = '/accounts/password-reset/done/'

    def form_valid(self, form):
        opts = {
            'use_https': self.request.is_secure(),
            'token_generator': self.token_generator,
            'from_email': self.from_email,
            'email_template_name': self.email_template_name,
            'subject_template_name': self.subject_template_name,
            'request': self.request,
            'html_email_template_name': self.html_email_template_name,
            'extra_email_context': self.extra_email_context,
        }

        def _send():
            try:
                form.save(**opts)
            except Exception as exc:
                logger.error('Parol tiklash emaili yuborilmadi: %s', exc)

        threading.Thread(target=_send, daemon=True).start()
        return HttpResponseRedirect(self.get_success_url())


@require_POST
def set_language_view(request):
    import re
    from django.utils.http import url_has_allowed_host_and_scheme

    lang = request.POST.get('lang', 'uz')
    if lang not in ('uz', 'ru', 'en'):
        lang = 'uz'
    request.session['lang'] = lang
    if request.user.is_authenticated:
        CustomUser.objects.filter(pk=request.user.pk).update(preferred_language=lang)

    next_url = request.POST.get('next', '')
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        referer = request.META.get('HTTP_REFERER', '/')
        next_url = urlparse(referer).path or '/'

    # Blog detail sahifasida til o'zgartirsa — mos tildagi versiyaga o'tadi
    m = re.match(r'^/blog/([^/]+)/$', next_url)
    if m:
        current_slug = m.group(1)
        try:
            from blog.models import BlogPost
            current_post = BlogPost.objects.get(slug=current_slug, is_published=True)
            if current_post.group_key:
                translated = BlogPost.objects.filter(
                    group_key=current_post.group_key,
                    language=lang,
                    is_published=True,
                ).exclude(pk=current_post.pk).first()
                if translated:
                    next_url = f'/blog/{translated.slug}/'
        except BlogPost.DoesNotExist:
            pass

    return redirect(next_url)


def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    from analysis.models import GapAnalysis
    from django.core.cache import cache
    _counts = cache.get('landing_counts')
    if _counts is None:
        _counts = {
            'user_count': CustomUser.objects.filter(role='entrepreneur').count(),
            'expert_count': CustomUser.objects.filter(role='expert', expert_profile__is_verified=True).count(),
            'analysis_count': GapAnalysis.objects.filter(status='completed').count(),
        }
        cache.set('landing_counts', _counts, 3600)
    # Base offset: platformadagi haqiqiy foydalanuvchilarga qo'shimcha boshlang'ich raqamlar
    user_count = _counts['user_count'] + 247
    expert_count = _counts['expert_count'] + 38
    analysis_count = _counts['analysis_count'] + 312

    lang = request.session.get('lang', 'uz')

    industry_lists = {
        'uz': [
            ("To'qimachilik", "👕"), ("Oziq-ovqat", "🍎"), ("Kimyo", "🧪"),
            ("Mashinasozlik", "⚙️"), ("Qurilish", "🏗️"), ("Farmatsevtika", "💊"),
            ("Qishloq xo'jaligi", "🌾"), ("Elektrotexnika", "⚡"),
        ],
        'ru': [
            ("Текстиль", "👕"), ("Продукты питания", "🍎"), ("Химия", "🧪"),
            ("Машиностроение", "⚙️"), ("Строительство", "🏗️"), ("Фармацевтика", "💊"),
            ("Сельское хозяйство", "🌾"), ("Электротехника", "⚡"),
        ],
        'en': [
            ("Textiles", "👕"), ("Food & Beverage", "🍎"), ("Chemicals", "🧪"),
            ("Mechanical Engineering", "⚙️"), ("Construction", "🏗️"), ("Pharmaceuticals", "💊"),
            ("Agriculture", "🌾"), ("Electrical Engineering", "⚡"),
        ],
    }

    faq_lists = {
        'uz': [
            (
                "Gap analiz nima va u qancha turadi?",
                "Gap analiz — sizning hozirgi standartingiz va maqsadli standart o'rtasidagi farqlarni aniqlash jarayoni. "
                "Platformamizda AI yordamida gap analiz qilish mutlaqo bepul. Faqat mutaxassis xizmatidan foydalanganda to'lov amalga oshiriladi.",
            ),
            (
                "To'lovim xavfsizmi? Mutaxassis pul olib g'oyib bo'lmaydimi?",
                "Yo'q. Biz Escrow tizimidan foydalanamiz: to'lovingiz platformada saqlanadi va faqat siz ishni tasdiqlagan "
                "taqdirdagina mutaxassisga o'tkaziladi. Ish bajarilmasa — pul qaytariladi.",
            ),
            (
                "Qaysi standartlar bilan ishlanadi?",
                "ISO 9001, ISO 14001, ISO 45001, ISO 22000, CE Marking, EN seriyali standartlar, GOST R va barcha "
                "UzDST mahalliy standartlari. Ro'yxat doimiy kengaytirib boriladi.",
            ),
            (
                "Mutaxassis qanday tanlanadi?",
                "Barcha mutaxassislar administrator tomonidan tekshiriladi va tasdiqlangandagina platformada ko'rinadi. "
                "Reytinglar va mijoz baholari asosida eng mos mutaxassisni tanlashingiz mumkin.",
            ),
            (
                "Necha vaqtda sertifikat olish mumkin?",
                "Bu standart turiga va korxona holatiga bog'liq. Odatda ISO 9001 uchun 6–12 oy kerak bo'ladi. "
                "AI tomonidan yaratilgan yo'l xarita aniq muddat va xarajatni ko'rsatadi.",
            ),
        ],
        'ru': [
            (
                "Что такое Gap-анализ и сколько он стоит?",
                "Gap-анализ — это процесс выявления различий между вашим текущим стандартом и целевым. "
                "На нашей платформе AI gap-анализ абсолютно бесплатен. Оплата производится только при использовании услуг эксперта.",
            ),
            (
                "Мой платёж в безопасности? Эксперт не исчезнет с деньгами?",
                "Нет. Мы используем систему Escrow: ваш платёж хранится на платформе и переводится эксперту только после вашего подтверждения работы. Если работа не выполнена — деньги возвращаются.",
            ),
            (
                "С какими стандартами вы работаете?",
                "ISO 9001, ISO 14001, ISO 45001, ISO 22000, CE Marking, стандарты серии EN, GOST R и все местные стандарты UzDST. Список постоянно расширяется.",
            ),
            (
                "Как выбирается эксперт?",
                "Все эксперты проверяются администратором и появляются на платформе только после подтверждения. Вы можете выбрать наиболее подходящего эксперта на основе рейтингов и отзывов клиентов.",
            ),
            (
                "Сколько времени нужно для получения сертификата?",
                "Это зависит от типа стандарта и состояния предприятия. Обычно для ISO 9001 требуется 6–12 месяцев. Дорожная карта, созданная AI, показывает точные сроки и стоимость.",
            ),
        ],
        'en': [
            (
                "What is Gap Analysis and how much does it cost?",
                "Gap analysis is the process of identifying differences between your current standard and the target standard. "
                "AI-powered gap analysis on our platform is completely free. Payment is only required when using expert services.",
            ),
            (
                "Is my payment safe? Can an expert disappear with the money?",
                "No. We use an Escrow system: your payment is held on the platform and only transferred to the expert after you confirm the work is done. If the work is not completed — you get a refund.",
            ),
            (
                "Which standards do you work with?",
                "ISO 9001, ISO 14001, ISO 45001, ISO 22000, CE Marking, EN series standards, GOST R, and all UzDST local standards. The list is constantly growing.",
            ),
            (
                "How is an expert selected?",
                "All experts are verified by the administrator and only appear on the platform after approval. You can choose the most suitable expert based on ratings and client reviews.",
            ),
            (
                "How long does it take to get certified?",
                "It depends on the type of standard and the company's current state. Typically, ISO 9001 takes 6–12 months. The AI-generated roadmap shows exact timelines and costs.",
            ),
        ],
    }

    standards_list = [
        "ISO 9001", "ISO 14001", "ISO 45001", "ISO 22000",
        "CE Marking", "EN 13432", "GOST R", "UzDST 1400", "UzDST 950", "UzDST 730",
    ]

    return render(request, 'landing.html', {
        'industry_list': industry_lists.get(lang, industry_lists['uz']),
        'faq_list': faq_lists.get(lang, faq_lists['uz']),
        'standards_list': standards_list,
        'user_count': user_count,
        'expert_count': expert_count,
        'analysis_count': analysis_count,
    })


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        from django_ratelimit.decorators import is_ratelimited
        # Email bo'yicha: spam/brute force prevention (har email 5/soat)
        if is_ratelimited(request, group='reg_email', key='post:email', rate='5/h', method='POST', increment=True):
            messages.error(request, 'Bu email bilan juda ko\'p urinish. Keyinroq qayta urining.')
            return render(request, 'accounts/register.html')
        # IP bo'yicha: ommaviy bot registration prevention (bir IP dan 50/soat)
        if is_ratelimited(request, group='reg_ip', key='ip', rate='50/h', method='POST', increment=True):
            messages.error(request, 'Juda ko\'p urinish. Keyinroq qayta urining.')
            return render(request, 'accounts/register.html')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        role = request.POST.get('role', '')
        phone = request.POST.get('phone', '').strip()
        referral_code = request.POST.get('referral_code', '').strip().upper()

        form_data = {
            'first_name': first_name, 'last_name': last_name, 'email': email,
            'role': role, 'phone': phone, 'referral_code': referral_code,
        }

        def fail(msg):
            messages.error(request, msg)
            return render(request, 'accounts/register.html', {'form_data': form_data})

        import re as _re
        if not first_name or not last_name:
            return fail('Ism va familiyani kiriting!')
        if not email:
            return fail('Email manzilni kiriting!')
        if not _re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            return fail('Email manzil noto\'g\'ri formatda!')
        if role not in ('entrepreneur', 'expert'):
            return fail('Rolni tanlang (tadbirkor yoki mutaxassis)!')
        if not password:
            return fail('Parolni kiriting!')
        if len(password) < 8:
            return fail('Parol kamida 8 ta belgidan iborat bo\'lishi kerak!')
        if password != password2:
            return fail('Parollar mos kelmadi!')

        if CustomUser.objects.filter(email__iexact=email).exists():
            return fail('Bu email allaqachon ro\'yxatdan o\'tgan!')

        # Auto-generate unique username from email
        base = _re.sub(r'[^a-zA-Z0-9_]', '', email.split('@')[0])[:15] or 'user'
        username = base
        _counter = 1
        while CustomUser.objects.filter(username=username).exists():
            username = f'{base}{_counter}'
            _counter += 1

        referred_by = None
        if referral_code:
            try:
                referred_by = CustomUser.objects.get(referral_code=referral_code)
            except CustomUser.DoesNotExist:
                messages.warning(request, 'Referral kod topilmadi, lekin ro\'yxatdan o\'tishingiz mumkin.')

        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            phone=phone,
            referred_by=referred_by,
        )

        if role == 'expert':
            ExpertProfile.objects.create(user=user, phone=phone)
        else:
            EntrepreneurProfile.objects.create(user=user)

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        send_welcome_email(user)
        messages.success(request, 'Xush kelibsiz!')
        return redirect('dashboard')

    return render(request, 'accounts/register.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    from django_ratelimit.exceptions import Ratelimited
    from django_ratelimit.decorators import is_ratelimited
    if request.method == 'POST':
        limited = is_ratelimited(request, group='login', key='ip', rate='5/m', method='POST', increment=True)
        if limited:
            return render(request, 'accounts/login.html', {
                'error': 'Juda ko\'p urinish. 1 daqiqadan keyin qayta urining.',
                'ratelimited': True,
            })

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password')

        # Email bilan login qilishni qo'llab-quvvatlash
        if '@' in username:
            try:
                from accounts.models import CustomUser as _CU
                user_obj = _CU.objects.get(email__iexact=username)
                username = user_obj.username
            except Exception:
                pass

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Email yoki parol noto\'g\'ri!')

    return render(request, 'accounts/login.html')


@require_POST
def logout_view(request):
    logout(request)
    return redirect('landing')


@login_required
def admin_panel(request):
    if not request.user.is_staff and not request.user.is_admin():
        return redirect('dashboard')

    from experts.models import Project, Payment, WithdrawalRequest, Dispute
    from analysis.models import GapAnalysis

    week_ago = timezone.now() - timedelta(days=7)

    entrepreneurs = CustomUser.objects.filter(role='entrepreneur')
    experts = CustomUser.objects.filter(role='expert')
    expert_profiles = ExpertProfile.objects.all()

    payments = Payment.objects.all()
    total_volume = payments.filter(status__in=['held', 'released']).aggregate(s=Sum('amount'))['s'] or 0
    platform_revenue = payments.filter(status='released').aggregate(s=Sum('platform_fee'))['s'] or 0
    held_amount = payments.filter(status='held').aggregate(s=Sum('amount'))['s'] or 0

    projects = Project.objects.all()
    total_projects = projects.count()

    project_statuses = [
        ('pending',     'Taklif yuborildi',    'bg-gray-400',   'bg-gray-400'),
        ('negotiating', 'Kelishilmoqda',        'bg-yellow-400', 'bg-yellow-400'),
        ('accepted',    'To\'lov kutilmoqda',   'bg-orange-400', 'bg-orange-400'),
        ('in_progress', 'Jarayonda',            'bg-blue-400',   'bg-blue-400'),
        ('review',      'Tekshiruvda',          'bg-purple-400', 'bg-purple-400'),
        ('completed',   'Yakunlandi',           'bg-green-400',  'bg-green-400'),
        ('cancelled',   'Bekor qilindi',        'bg-red-400',    'bg-red-400'),
    ]
    from django.db.models import Count
    status_counts = dict(
        projects.values('status').annotate(cnt=Count('id')).values_list('status', 'cnt')
    )
    project_stats = []
    for status, label, color, bar_color in project_statuses:
        count = status_counts.get(status, 0)
        percent = int(count / total_projects * 100) if total_projects else 0
        project_stats.append({
            'label': label, 'count': count,
            'color': color, 'bar_color': bar_color, 'percent': percent,
        })

    _total_ent = entrepreneurs.count()
    _with_analysis = entrepreneurs.filter(analyses__isnull=False).distinct().count()
    _completed_analysis = entrepreneurs.filter(analyses__status='completed').distinct().count()
    _sent_expert = Project.objects.values('entrepreneur').distinct().count()
    _paid = Payment.objects.filter(status__in=['held', 'released']).values('entrepreneur').distinct().count()

    def _pct(n):
        return int(n / _total_ent * 100) if _total_ent else 0

    funnel = [
        {'label': "Ro'yxatdan o'tdi",  'count': _total_ent,          'pct': 100},
        {'label': 'Tahlil boshladi',    'count': _with_analysis,      'pct': _pct(_with_analysis)},
        {'label': 'Tahlil yakunladi',   'count': _completed_analysis, 'pct': _pct(_completed_analysis)},
        {'label': 'Expertga yubordi',   'count': _sent_expert,        'pct': _pct(_sent_expert)},
        {'label': "To'lov qildi",       'count': _paid,               'pct': _pct(_paid)},
    ]

    stats = {
        'entrepreneurs': _total_ent,
        'new_entrepreneurs': entrepreneurs.filter(created_at__gte=week_ago).count(),
        'experts': experts.count(),
        'verified_experts': expert_profiles.filter(is_verified=True).count(),
        'unverified_experts': expert_profiles.filter(is_verified=False).count(),
        'analyses': GapAnalysis.objects.count(),
        'completed_analyses': GapAnalysis.objects.filter(status='completed').count(),
        'total_volume': total_volume,
        'platform_revenue': platform_revenue,
        'held_amount': held_amount,
        'active_projects': projects.filter(status='in_progress').count(),
    }

    import json as _json
    _MONTH_NAMES = ['Yan', 'Fev', 'Mar', 'Apr', 'May', 'Iyn', 'Iyl', 'Avg', 'Sen', 'Okt', 'Noy', 'Dek']
    _now_local = timezone.localtime(timezone.now())
    months_data = []
    for i in range(5, -1, -1):
        _ref = (_now_local.replace(day=1) - timedelta(days=30 * i))
        month_start = _ref.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_label = _MONTH_NAMES[month_start.month - 1] + ' ' + str(month_start.year)
        new_users = CustomUser.objects.filter(created_at__gte=month_start, created_at__lt=month_end).count()
        month_revenue = payments.filter(
            status='released', released_at__gte=month_start, released_at__lt=month_end
        ).aggregate(s=Sum('platform_fee'))['s'] or 0
        months_data.append({'label': month_label, 'users': new_users, 'revenue': float(month_revenue)})

    pending_withdrawals = WithdrawalRequest.objects.filter(status='pending').select_related('wallet__user')[:10]
    open_disputes = Dispute.objects.filter(status__in=('open', 'in_review')).select_related('project', 'opened_by')[:10]
    # F-10: tarixiy nizolar
    resolved_disputes = Dispute.objects.filter(status__in=('resolved', 'closed')).select_related('project', 'opened_by').order_by('-resolved_at')[:10]
    # F-10: tarixiy withdrawal'lar
    processed_withdrawals = WithdrawalRequest.objects.exclude(status='pending').select_related('wallet__user').order_by('-processed_at')[:10]
    # F-11: expert o'chirilgan faol loyihalar
    orphaned_projects = Project.objects.filter(
        expert__isnull=True,
        status__in=('pending', 'negotiating', 'accepted', 'in_progress', 'review'),
    ).select_related('entrepreneur', 'analysis__local_standard', 'analysis__target_standard')

    return render(request, 'accounts/admin_panel.html', {
        'stats': stats,
        'funnel': funnel,
        'project_stats': project_stats,
        'pending_experts': expert_profiles.filter(is_verified=False).select_related('user')[:20],
        'recent_payments': payments.order_by('-created_at').select_related('entrepreneur', 'project')[:8],
        'recent_users': CustomUser.objects.exclude(role='admin').order_by('-created_at')[:10],
        'chart_labels': _json.dumps([m['label'] for m in months_data]),
        'chart_users': _json.dumps([m['users'] for m in months_data]),
        'chart_revenue': _json.dumps([m['revenue'] for m in months_data]),
        'pending_withdrawals': pending_withdrawals,
        'open_disputes': open_disputes,
        'resolved_disputes': resolved_disputes,
        'processed_withdrawals': processed_withdrawals,
        'orphaned_projects': orphaned_projects,
    })


@login_required
def referral_view(request):
    from django.db.models import Sum, Count
    from django.core.paginator import Paginator
    user = request.user
    referrals_qs = CustomUser.objects.filter(referred_by=user).order_by('-created_at')
    paginator = Paginator(referrals_qs, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    referral_link = request.build_absolute_uri(f'/register/?ref={user.referral_code}')
    total_bonus = 0
    try:
        total_bonus = user.wallet.transactions.filter(
            transaction_type='income',
            description__startswith='Referral bonus'
        ).aggregate(total=Sum('amount'))['total'] or 0
    except Exception:
        pass
    # Top-5 tavsiyachilar (ommaviy, faqat ism va son)
    top_referrers = (
        CustomUser.objects
        .annotate(ref_count=Count('referrals'))
        .filter(ref_count__gt=0)
        .order_by('-ref_count')[:5]
    )
    return render(request, 'accounts/referral.html', {
        'referral_code': user.referral_code,
        'referral_link': referral_link,
        'referrals': page_obj,
        'page_obj': page_obj,
        'total_referrals': referrals_qs.count(),
        'total_bonus': total_bonus,
        'top_referrers': top_referrers,
    })


@login_required
def entrepreneur_profile_view(request):
    if not request.user.is_entrepreneur():
        return redirect('dashboard')

    user = request.user
    try:
        profile = user.entrepreneur_profile
    except EntrepreneurProfile.DoesNotExist:
        profile = EntrepreneurProfile.objects.create(user=user)

    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.company_name = request.POST.get('company_name', user.company_name)
        user.phone = request.POST.get('phone', user.phone)
        user.region = request.POST.get('region', user.region)
        user.industry = request.POST.get('industry', user.industry)
        user.save()

        profile.company_description = request.POST.get('company_description', '')
        try:
            profile.employee_count = max(0, int(request.POST.get('employee_count', 0) or 0))
        except (ValueError, TypeError):
            profile.employee_count = 0
        profile.annual_revenue = request.POST.get('annual_revenue', '')
        profile.export_experience = request.POST.get('export_experience') == 'on'
        profile.target_markets = request.POST.get('target_markets', '')
        profile.save()

        messages.success(request, 'Profil yangilandi!')
        return redirect('entrepreneur_profile')

    from accounts.models import ExpertProfile
    regions = ExpertProfile.REGION_CHOICES
    industries = [
        "To'qimachilik", "Oziq-ovqat", "Kimyo", "Mashinasozlik",
        "Qurilish", "Farmatsevtika", "Qishloq xo'jaligi", "Elektrotexnika",
    ]
    return render(request, 'accounts/entrepreneur_profile.html', {
        'profile': profile,
        'regions': regions,
        'industries': industries,
    })


@login_required
def bulk_verify_experts(request):
    """Admin bir vaqtda bir nechta expertni tasdiqlaydi."""
    if not (request.user.is_staff or request.user.is_admin()):
        return redirect('dashboard')
    if request.method == 'POST':
        from django.utils import timezone as _tz
        pks = request.POST.getlist('expert_pks')
        action = request.POST.get('action', 'verify')
        if not pks:
            messages.warning(request, 'Hech bir expert tanlanmadi.')
            return redirect('admin_panel')
        profiles = ExpertProfile.objects.filter(pk__in=pks)
        count = 0
        for profile in profiles:
            if action == 'verify' and not profile.is_verified:
                profile.is_verified = True
                profile.verified_at = _tz.now()
                profile.save(update_fields=['is_verified', 'verified_at'])
                send_expert_verified(profile.user)
                count += 1
            elif action == 'reject' and profile.is_verified:
                profile.is_verified = False
                profile.verified_at = None
                profile.save(update_fields=['is_verified', 'verified_at'])
                count += 1
        action_word = 'tasdiqlandi' if action == 'verify' else 'tasdiq bekor qilindi'
        messages.success(request, f'{count} ta expert {action_word}.')
    return redirect('admin_panel')


@login_required
def verify_expert_action(request, pk):
    if not (request.user.is_staff or request.user.is_admin()):
        return redirect('dashboard')
    if request.method == 'POST':
        from django.utils import timezone
        profile = get_object_or_404(ExpertProfile, pk=pk)
        action = request.POST.get('action', 'verify')
        if action == 'verify':
            if profile.is_verified:
                messages.info(request, f'{profile.user.get_full_name()} allaqachon tasdiqlangan.')
                return redirect('admin_panel')
            profile.is_verified = True
            profile.verified_at = timezone.now()
            profile.save(update_fields=['is_verified', 'verified_at'])
            send_expert_verified(profile.user)
            messages.success(request, f'{profile.user.get_full_name()} tasdiqlandi!')
        else:
            profile.is_verified = False
            profile.verified_at = None
            profile.save()
            messages.warning(request, f'{profile.user.get_full_name()} tasdiq bekor qilindi.')
    return redirect('admin_panel')


@login_required
def admin_process_withdrawal(request, pk):
    """Admin approves or rejects a withdrawal request."""
    if not (request.user.is_staff or request.user.is_admin()):
        return redirect('dashboard')
    if request.method != 'POST':
        return redirect('admin_panel')

    from experts.models import WithdrawalRequest, Notification
    from experts.emails import send_withdrawal_approved, send_withdrawal_rejected
    from django.utils import timezone

    wr = get_object_or_404(WithdrawalRequest, pk=pk)
    action = request.POST.get('action')
    admin_note = request.POST.get('admin_note', '').strip()

    if wr.status != 'pending':
        messages.warning(request, 'Bu so\'rov allaqachon ko\'rib chiqilgan!')
        return redirect('admin_panel')

    if action == 'approve':
        from django.db import transaction as _tx
        with _tx.atomic():
            wr_locked = WithdrawalRequest.objects.select_for_update().get(pk=wr.pk)
            if wr_locked.status != 'pending':
                messages.warning(request, 'Bu so\'rov allaqachon ko\'rib chiqilgan!')
                return redirect('admin_panel')
            wr_locked.status = 'approved'
            wr_locked.admin_note = admin_note
            wr_locked.processed_at = timezone.now()
            wr_locked.save()
        try:
            _card_suffix = wr.card_number_plain[-4:] or '****'
        except Exception:
            _card_suffix = '****'
        Notification.objects.create(
            user=wr.wallet.user,
            title=_nl(wr.wallet.user, 'Pul yechish tasdiqlandi!', 'Вывод средств подтверждён!', 'Withdrawal approved!'),
            message=_nl(wr.wallet.user,
                f'${wr.amount} kartangizga o\'tkazildi. *{_card_suffix}',
                f'${wr.amount} переведено на вашу карту. *{_card_suffix}',
                f'${wr.amount} transferred to your card. *{_card_suffix}'),
        )
        try:
            send_withdrawal_approved(wr)
        except Exception as _exc:
            logger.error('send_withdrawal_approved xatosi (wr=%s): %s', wr.pk, _exc)
        messages.success(request, f'${wr.amount} yechish so\'rovi tasdiqlandi!')
    elif action == 'reject':
        from django.db import transaction as _tx
        from experts.models import Wallet as _Wallet, WalletTransaction as _WT
        with _tx.atomic():
            wr_locked = WithdrawalRequest.objects.select_for_update().get(pk=wr.pk)
            if wr_locked.status != 'pending':
                messages.warning(request, 'Bu so\'rov allaqachon ko\'rib chiqilgan!')
                return redirect('admin_panel')
            wallet = _Wallet.objects.select_for_update().get(pk=wr_locked.wallet_id)
            wallet.balance += wr_locked.amount
            wallet.save(update_fields=['balance'])
            _WT.objects.create(
                wallet=wallet,
                amount=wr_locked.amount,
                transaction_type='refund',
                description=f'Yechish rad etildi — qaytarildi (so\'rov #{wr_locked.pk})',
            )
            wr_locked.status = 'rejected'
            wr_locked.admin_note = admin_note
            wr_locked.processed_at = timezone.now()
            wr_locked.save()
        Notification.objects.create(
            user=wr.wallet.user,
            title=_nl(wr.wallet.user, 'Pul yechish rad etildi', 'Вывод средств отклонён', 'Withdrawal rejected'),
            message=_nl(wr.wallet.user,
                f'${wr.amount} hamyoningizga qaytarildi. Sabab: {admin_note or "Ko\'rsatilmadi"}',
                f'${wr.amount} возвращено на кошелёк. Причина: {admin_note or "Не указана"}',
                f'${wr.amount} returned to wallet. Reason: {admin_note or "Not specified"}'),
        )
        send_withdrawal_rejected(wr)
        messages.warning(request, f'Yechish so\'rovi rad etildi, ${wr.amount} qaytarildi.')
    return redirect('admin_panel')


@login_required
def admin_resolve_dispute(request, pk):
    """Admin resolves a dispute and records decision."""
    if not (request.user.is_staff or request.user.is_admin()):
        return redirect('dashboard')
    if request.method != 'POST':
        return redirect('admin_panel')

    from experts.models import Dispute, Notification
    from experts.emails import send_dispute_resolved
    from django.utils import timezone

    get_object_or_404(Dispute, pk=pk)  # 404 check before atomic

    decision = request.POST.get('decision', '').strip()
    new_status = request.POST.get('status', 'resolved')
    # favor: 'expert' → pul expertga, 'entrepreneur' → pul qaytariladi, 'none' → moliyaviy harakat yo'q
    favor = request.POST.get('favor', 'none')

    from experts.models import Payment, Wallet, WalletTransaction
    from django.db import transaction as _tx

    with _tx.atomic():
        # select_for_update — bir vaqtda ikki admin bir nizoni hal qila olmasin
        dispute = Dispute.objects.select_for_update().get(pk=pk)
        if dispute.status in ('resolved', 'closed'):
            messages.warning(request, 'Bu nizo allaqachon hal qilingan!')
            return redirect('admin_panel')
        dispute.admin_decision = decision
        dispute.status = new_status
        dispute.resolved_at = timezone.now()
        dispute.save()

        project = dispute.project
        try:
            payment = Payment.objects.select_for_update().get(project=project)
        except Payment.DoesNotExist:
            payment = None

        if payment and payment.status == 'held':
            if favor == 'expert' and project.expert:
                # Expert foydasiga: pul expertga o'tkaziladi
                payment.status = 'released'
                payment.released_at = timezone.now()
                payment.save()
                project.status = 'completed'
                project.completed_at = timezone.now()
                project.save()
                wallet, _ = Wallet.objects.get_or_create(user=project.expert)
                wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)
                wallet.balance += payment.expert_amount
                wallet.save(update_fields=['balance'])
                WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=payment.expert_amount,
                    transaction_type='income',
                    description=f'Loyiha #{project.pk} — nizo hal qilindi (expert foydasiga)',
                    project=project,
                )
            elif favor == 'entrepreneur':
                # Tadbirkor foydasiga: pul hamyoniga qaytariladi
                payment.status = 'refunded'
                payment.save(update_fields=['status'])
                project.status = 'cancelled'
                project.save()
                ent_wallet, _ = Wallet.objects.get_or_create(user=project.entrepreneur)
                ent_wallet = Wallet.objects.select_for_update().get(pk=ent_wallet.pk)
                ent_wallet.balance += payment.amount
                ent_wallet.save(update_fields=['balance'])
                WalletTransaction.objects.create(
                    wallet=ent_wallet,
                    amount=payment.amount,
                    transaction_type='refund',
                    description=f'Loyiha #{project.pk} — nizo hal qilindi (tadbirkor foydasiga)',
                    project=project,
                )

    Notification.objects.create(
        user=dispute.opened_by,
        title=_nl(dispute.opened_by, 'Nizo ko\'rib chiqildi!', 'Спор рассмотрен!', 'Dispute resolved!'),
        message=_nl(dispute.opened_by,
            f'Loyiha #{dispute.project_id} bo\'yicha nizo hal qilindi. Admin qarori: {decision[:100]}',
            f'Спор по проекту #{dispute.project_id} рассмотрен. Решение администратора: {decision[:100]}',
            f'Dispute on project #{dispute.project_id} resolved. Admin decision: {decision[:100]}'),
    )
    if dispute.project.expert:
        Notification.objects.create(
            user=dispute.project.expert,
            title=_nl(dispute.project.expert, 'Nizo ko\'rib chiqildi!', 'Спор рассмотрен!', 'Dispute resolved!'),
            message=_nl(dispute.project.expert,
                f'Loyiha #{dispute.project_id} bo\'yicha nizo hal qilindi.',
                f'Спор по проекту #{dispute.project_id} рассмотрен.',
                f'Dispute on project #{dispute.project_id} resolved.'),
        )
    send_dispute_resolved(dispute, decision)
    messages.success(request, f'Nizo #{pk} hal qilindi!')
    return redirect('admin_panel')


@login_required
def dashboard(request):
    user = request.user
    if user.role == 'expert':
        return redirect('expert_dashboard')
    elif user.role == 'admin':
        return redirect('admin_panel')
    else:
        return redirect('entrepreneur_dashboard')

@login_required
@require_POST
def upload_avatar(request):
    """AJAX: foydalanuvchi profil rasmini yuklash va qirqish."""
    f = request.FILES.get('avatar')
    if not f:
        return JsonResponse({'ok': False, 'error': 'Fayl tanlanmadi'}, status=400)

    # Hajm tekshiruvi: max 3 MB
    if f.size > 3 * 1024 * 1024:
        return JsonResponse({'ok': False, 'error': 'Rasm 3 MB dan katta bo\'lmasligi kerak'}, status=400)

    # Tur tekshiruvi
    if not f.content_type.startswith('image/'):
        return JsonResponse({'ok': False, 'error': 'Faqat rasm fayllari qabul qilinadi'}, status=400)

    try:
        from PIL import Image
        import io
        from django.core.files.base import ContentFile

        img = Image.open(f).convert('RGB')

        # Kvadrat crop — markazdan
        w, h = img.size
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        img = img.crop((left, top, left + side, top + side))

        # 400×400 ga resize
        img = img.resize((400, 400), Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=88, optimize=True)
        buf.seek(0)

        # Eski rasmni o'chirish
        user = request.user
        if user.avatar:
            try:
                user.avatar.delete(save=False)
            except Exception:
                pass

        fname = f'avatar_{user.pk}.jpg'
        user.avatar.save(fname, ContentFile(buf.read()), save=True)

        return JsonResponse({'ok': True, 'url': user.avatar.url})
    except Exception as e:
        logger.exception('Avatar upload xatosi: %s', e)
        return JsonResponse({'ok': False, 'error': 'Rasm saqlanmadi, qayta urinib ko\'ring'}, status=500)


@login_required
def api_notification_count(request):
    from experts.models import Notification
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@login_required
def global_search_api(request):
    from django_ratelimit.decorators import is_ratelimited
    if is_ratelimited(request, group='search', key='user', rate='30/m', method='GET', increment=True):
        return JsonResponse({'results': []})
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'results': []})
    results = []
    # Mutaxassislar
    for ep in ExpertProfile.objects.filter(is_verified=True).filter(
        Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q) |
        Q(specializations__icontains=q) | Q(bio__icontains=q)
    ).select_related('user')[:5]:
        results.append({
            'type': 'expert',
            'icon': '👤',
            'title': ep.user.get_full_name(),
            'sub': (ep.specializations or '')[:60],
            'url': f'/experts/{ep.user.pk}/',
        })
    # Standartlar
    from analysis.models import Standard
    for std in Standard.objects.filter(
        Q(code__icontains=q) | Q(name__icontains=q)
    )[:4]:
        results.append({
            'type': 'standard',
            'icon': '📋',
            'title': std.code,
            'sub': (std.name or '')[:60],
            'url': '/analysis/select-industry/',
        })
    # Blog
    from blog.models import BlogPost
    for post in BlogPost.objects.filter(is_published=True).filter(
        Q(title__icontains=q) | Q(content__icontains=q)
    )[:4]:
        results.append({
            'type': 'blog',
            'icon': '📰',
            'title': post.title[:60],
            'sub': '',
            'url': f'/blog/{post.slug}/',
        })
    return JsonResponse({'results': results})


@login_required
def resend_verification(request):
    from django_ratelimit.decorators import is_ratelimited
    if is_ratelimited(request, group='resend_verify', key='user', rate='3/h', method='ALL', increment=True):
        messages.error(request, 'Juda ko\'p urinish. 1 soatdan keyin qayta urining.')
        return redirect('dashboard')
    if request.user.is_email_verified:
        return redirect('dashboard')
    import secrets
    token = secrets.token_urlsafe(48)
    request.user.email_verify_token = token
    request.user.save(update_fields=['email_verify_token'])
    from experts.emails import _send
    lang = request.session.get('lang', 'uz')
    verify_url = request.build_absolute_uri(f'/accounts/verify-email/{token}/')
    _SUBJ = {'uz': 'Email manzilingizni tasdiqlang', 'ru': 'Подтвердите вашу почту', 'en': 'Verify your email'}
    _BODY = {
        'uz': f'StandardBridge ga xush kelibsiz!\n\nEmail manzilingizni tasdiqlash uchun quyidagi havolani bosing:\n{verify_url}\n\nHavola 48 soat amal qiladi.',
        'ru': f'Добро пожаловать на StandardBridge!\n\nПерейдите по ссылке для подтверждения email:\n{verify_url}\n\nСсылка действительна 48 часов.',
        'en': f'Welcome to StandardBridge!\n\nClick the link below to verify your email:\n{verify_url}\n\nLink valid for 48 hours.',
    }
    _send(_SUBJ.get(lang, _SUBJ['uz']), _BODY.get(lang, _BODY['uz']), request.user.email)
    messages.success(request, 'Tasdiqlash xati yuborildi!' if lang == 'uz' else ('Письмо отправлено!' if lang == 'ru' else 'Verification email sent!'))
    _ref = request.META.get('HTTP_REFERER', '')
    return redirect(urlparse(_ref).path or '/dashboard/')


@login_required
@require_http_methods(['GET'])
def telegram_connect_view(request):
    """Telegram bog'lash uchun oraliq sahifa — deep link orqali ilova ochiladi."""
    import secrets
    bot_username = settings.TELEGRAM_BOT_USERNAME.lstrip('@')
    if not bot_username:
        messages.error(request, 'Telegram bot hali sozlanmagan.')
        _ref = request.META.get('HTTP_REFERER', '')
        return redirect(urlparse(_ref).path or '/dashboard/')
    token = secrets.token_urlsafe(32)
    request.user.telegram_link_token = token
    request.user.save(update_fields=['telegram_link_token'])
    deep_link = f'tg://resolve?domain={bot_username}&start={token}'
    web_link = f'https://t.me/{bot_username}?start={token}'
    return render(request, 'accounts/telegram_connect.html', {
        'deep_link': deep_link,
        'web_link': web_link,
        'bot_username': bot_username,
    })


@login_required
@require_POST
def telegram_disconnect_view(request):
    """Telegram ulanishini uzadi."""
    request.user.telegram_chat_id = ''
    request.user.telegram_link_token = ''
    request.user.save(update_fields=['telegram_chat_id', 'telegram_link_token'])
    messages.success(request, 'Telegram uzildi.')
    _ref = request.META.get('HTTP_REFERER', '')
    return redirect(urlparse(_ref).path or '/dashboard/')


from django.views.decorators.csrf import csrf_exempt as _csrf_exempt


@_csrf_exempt
def telegram_webhook_view(request):
    """Telegram bot webhook — /start TOKEN komandani qayta ishlaydi."""
    if request.method != 'POST':
        return JsonResponse({'ok': False}, status=405)

    expected_secret = settings.TELEGRAM_WEBHOOK_SECRET
    if not expected_secret and not settings.DEBUG:
        logger.warning('Telegram webhook: TELEGRAM_WEBHOOK_SECRET sozlanmagan, so\'rov rad etildi')
        return JsonResponse({'ok': False}, status=403)
    if expected_secret:
        incoming = request.headers.get('X-Telegram-Bot-Api-Secret-Token', '')
        if incoming != expected_secret:
            return JsonResponse({'ok': False}, status=403)

    try:
        import json as _json
        data = _json.loads(request.body)
    except Exception:
        return JsonResponse({'ok': False}, status=400)

    message = data.get('message', {})
    text = (message.get('text') or '').strip()
    chat = message.get('chat', {})
    chat_id = str(chat.get('id', ''))
    from_user = message.get('from', {})
    first_name = from_user.get('first_name', 'Foydalanuvchi')

    if not text.startswith('/start'):
        return JsonResponse({'ok': True})

    parts = text.split(maxsplit=1)
    token = parts[1].strip() if len(parts) > 1 else ''

    from experts.emails import send_telegram
    if token:
        try:
            user = CustomUser.objects.get(telegram_link_token=token)
            user.telegram_chat_id = chat_id
            user.telegram_link_token = ''
            user.save(update_fields=['telegram_chat_id', 'telegram_link_token'])
            import html as _html
            send_telegram(chat_id, (
                f"🎉 <b>Salom, {_html.escape(first_name)}!</b>\n\n"
                f"StandardBridge bildirishnomalari endi Telegram orqali yuboriladi.\n\n"
                f"Yangi loyiha, to'lov, tahlil tayyorligi kabi barcha muhim xabarlarni shu yerda olasiz.\n\n"
                f"🔗 <a href='{settings.SITE_URL}'>Platformaga o'tish</a>"
            ))
            logger.info('Telegram ulandi: user_id=%s, chat_id=%s', user.pk, chat_id)
        except CustomUser.DoesNotExist:
            send_telegram(chat_id, "❌ Havola topilmadi yoki muddati o'tgan.\n\nProfil sahifasidan yangi havola oling.")
        except Exception as e:
            logger.exception('Telegram webhook xatosi: %s', e)
    else:
        import html as _html
        send_telegram(chat_id, (
            f"Salom, {_html.escape(first_name)}! 👋\n\n"
            "Bu StandardBridge rasmiy boti.\n"
            "Ulanish uchun platforma profil sahifasidagi havoladan foydalaning:\n"
            f"🔗 {settings.SITE_URL}"
        ))

    return JsonResponse({'ok': True})


def verify_email(request, token):
    if not token:
        messages.error(request, 'Noto\'g\'ri havola!')
        return redirect('landing')
    try:
        user = CustomUser.objects.get(email_verify_token=token)
        user.is_email_verified = True
        user.email_verify_token = ''
        user.save(update_fields=['is_email_verified', 'email_verify_token'])
        messages.success(request, 'Email manzil muvaffaqiyatli tasdiqlandi!')
    except CustomUser.DoesNotExist:
        messages.error(request, 'Havola yaroqsiz yoki muddati o\'tgan!')
    except CustomUser.MultipleObjectsReturned:
        # Token collision (juda kam ehtimol) — har ikkalasini ham tasdiqlash
        CustomUser.objects.filter(email_verify_token=token).update(
            is_email_verified=True, email_verify_token=''
        )
        messages.success(request, 'Email manzil muvaffaqiyatli tasdiqlandi!')
    return redirect('landing')


@login_required
@require_POST
def api_chatbot(request):
    from core.chatbot_context import (
        is_injection_attempt, build_system_prompt, get_live_stats, get_active_features,
    )
    from django_ratelimit.decorators import is_ratelimited
    if is_ratelimited(request, group='chatbot', key='user', rate='20/m', method='POST', increment=True):
        return JsonResponse({'reply': "Juda ko'p so'rov. Biroz kuting."}, status=429)

    message = request.POST.get('message', '').strip()[:500]
    if not message:
        return JsonResponse({'error': 'empty'}, status=400)

    if is_injection_attempt(message):
        return JsonResponse({'reply': "Uzr, bu savolga javob bera olmayman. Sertifikatlashtirish va platforma haqida yordam so'rang."})

    groq_key = getattr(settings, 'GROQ_API_KEY', '')
    if not groq_key:
        logger.warning('api_chatbot: GROQ_API_KEY sozlanmagan')
        return JsonResponse({'reply': "AI yordamchi hozir mavjud emas. Admin bilan bog'laning."})

    system_prompt = build_system_prompt(
        user=request.user,
        live_stats=get_live_stats(),
        active_features=get_active_features(),
    )

    try:
        from groq import Groq
        client = Groq(api_key=groq_key, timeout=25, max_retries=1)
        resp = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': message},
            ],
            max_tokens=500,
            temperature=0.4,
        )
        reply = resp.choices[0].message.content.strip()
        return JsonResponse({'reply': reply})
    except Exception as e:
        logger.exception('api_chatbot xatolik: %s', e)
        return JsonResponse({'reply': "Uzr, hozir javob bera olmayapman. Keyinroq urinib ko'ring."})
