from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django_ratelimit.decorators import ratelimit
from .models import CustomUser, ExpertProfile, EntrepreneurProfile
from experts.emails import send_welcome_email, send_expert_verified


@require_POST
def set_language_view(request):
    lang = request.POST.get('lang', 'uz')
    if lang not in ('uz', 'ru', 'en'):
        lang = 'uz'
    request.session['lang'] = lang
    next_url = request.POST.get('next', '')
    # Faqat relative URL qabul qilinadi — open redirect oldini olish
    if not next_url or not next_url.startswith('/'):
        referer = request.META.get('HTTP_REFERER', '/')
        from urllib.parse import urlparse
        parsed = urlparse(referer)
        next_url = parsed.path or '/'
    return redirect(next_url)


def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

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
    })


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        role = request.POST.get('role', '')
        company_name = request.POST.get('company_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        region = request.POST.get('region', '').strip()
        industry = request.POST.get('industry', '').strip()

        referral_code = request.POST.get('referral_code', '').strip().upper()

        # Preserve entered values so the form is not wiped on error
        form_data = {
            'first_name': first_name, 'last_name': last_name, 'email': email,
            'username': username, 'role': role, 'company_name': company_name,
            'phone': phone, 'region': region, 'industry': industry,
            'referral_code': referral_code,
        }

        def fail(msg):
            messages.error(request, msg)
            return render(request, 'accounts/register.html', {'form_data': form_data})

        # --- Validation ---
        import re as _re
        if not first_name or not last_name:
            return fail('Ism va familiyani kiriting!')
        if not username:
            return fail('Foydalanuvchi nomini kiriting!')
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

        if CustomUser.objects.filter(username=username).exists():
            return fail('Bu username allaqachon mavjud!')

        if CustomUser.objects.filter(email__iexact=email).exists():
            return fail('Bu email allaqachon ro\'yxatdan o\'tgan!')

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
            company_name=company_name,
            phone=phone,
            region=region,
            industry=industry,
            referred_by=referred_by,
        )

        if role == 'expert':
            ExpertProfile.objects.create(user=user)
        else:
            EntrepreneurProfile.objects.create(user=user)

        login(request, user)
        send_welcome_email(user)
        messages.success(request, 'Xush kelibsiz!')
        return redirect('dashboard')

    return render(request, 'accounts/register.html')


@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            # Rol login'da tanlanmaydi — 'dashboard' view foydalanuvchi rolini
            # aniqlab, to'g'ri sahifaga (entrepreneur/expert/admin) yo'naltiradi
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Username yoki parol noto\'g\'ri!')

    return render(request, 'accounts/login.html')


def logout_view(request):
    if request.method == 'POST':
        logout(request)
    return redirect('landing')


def role_select(request):
    return render(request, 'accounts/role_select.html')


@login_required
def admin_panel(request):
    if not request.user.is_staff and not request.user.is_admin():
        return redirect('dashboard')

    from django.utils import timezone
    from datetime import timedelta
    from experts.models import Project, Payment
    from analysis.models import GapAnalysis
    from accounts.models import ExpertProfile

    week_ago = timezone.now() - timedelta(days=7)

    entrepreneurs = CustomUser.objects.filter(role='entrepreneur')
    experts = CustomUser.objects.filter(role='expert')
    expert_profiles = ExpertProfile.objects.all()

    from django.db.models import Sum
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
    project_stats = []
    for status, label, color, bar_color in project_statuses:
        count = projects.filter(status=status).count()
        percent = int(count / total_projects * 100) if total_projects else 0
        project_stats.append({
            'label': label, 'count': count,
            'color': color, 'bar_color': bar_color, 'percent': percent,
        })

    stats = {
        'entrepreneurs': entrepreneurs.count(),
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

    # Oxirgi 6 oy uchun oylik statistika — aggregate ile (N+1 yo'q)
    from datetime import timedelta
    import json as _json
    from django.db.models import Sum, Count
    from django.db.models.functions import TruncMonth
    months_data = []
    for i in range(5, -1, -1):
        month_start = (timezone.now() - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_label = month_start.strftime('%b %Y')
        new_users = CustomUser.objects.filter(created_at__gte=month_start, created_at__lt=month_end).count()
        month_revenue = payments.filter(
            status='released', released_at__gte=month_start, released_at__lt=month_end
        ).aggregate(s=Sum('platform_fee'))['s'] or 0
        months_data.append({'label': month_label, 'users': new_users, 'revenue': float(month_revenue)})

    from experts.models import WithdrawalRequest, Dispute
    pending_withdrawals = WithdrawalRequest.objects.filter(status='pending').select_related('wallet__user')[:10]
    open_disputes = Dispute.objects.filter(status__in=('open', 'in_review')).select_related('project', 'opened_by')[:10]

    return render(request, 'accounts/admin_panel.html', {
        'stats': stats,
        'project_stats': project_stats,
        'pending_experts': expert_profiles.filter(is_verified=False).select_related('user')[:8],
        'recent_payments': payments.order_by('-created_at').select_related('entrepreneur', 'project')[:8],
        'recent_users': CustomUser.objects.exclude(role='admin').order_by('-created_at')[:10],
        'chart_labels': _json.dumps([m['label'] for m in months_data]),
        'chart_users': _json.dumps([m['users'] for m in months_data]),
        'chart_revenue': _json.dumps([m['revenue'] for m in months_data]),
        'pending_withdrawals': pending_withdrawals,
        'open_disputes': open_disputes,
    })


@login_required
def referral_view(request):
    user = request.user
    referrals = CustomUser.objects.filter(referred_by=user).order_by('-created_at')
    referral_link = request.build_absolute_uri(f'/register/?ref={user.referral_code}')
    return render(request, 'accounts/referral.html', {
        'referral_code': user.referral_code,
        'referral_link': referral_link,
        'referrals': referrals,
        'total_referrals': referrals.count(),
    })


@login_required
def entrepreneur_profile_view(request):
    if request.user.is_expert():
        return redirect('expert_profile')

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
def verify_expert_action(request, pk):
    if not (request.user.is_staff or request.user.is_admin()):
        return redirect('dashboard')
    if request.method == 'POST':
        from django.utils import timezone
        profile = get_object_or_404(ExpertProfile, pk=pk)
        action = request.POST.get('action', 'verify')
        if action == 'verify':
            profile.is_verified = True
            profile.verified_at = timezone.now()
            profile.save()
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
        wr.status = 'approved'
        wr.admin_note = admin_note
        wr.processed_at = timezone.now()
        wr.save()
        Notification.objects.create(
            user=wr.wallet.user,
            title='Pul yechish tasdiqlandi!',
            message=f'${wr.amount} kartangizga o\'tkazildi. *{wr.card_number_plain[-4:]}',
        )
        send_withdrawal_approved(wr)
        messages.success(request, f'${wr.amount} yechish so\'rovi tasdiqlandi!')
    elif action == 'reject':
        from django.db import transaction as _tx
        from experts.models import Wallet as _Wallet
        with _tx.atomic():
            wr_locked = WithdrawalRequest.objects.select_for_update().get(pk=wr.pk)
            if wr_locked.status != 'pending':
                messages.warning(request, 'Bu so\'rov allaqachon ko\'rib chiqilgan!')
                return redirect('admin_panel')
            wallet = _Wallet.objects.select_for_update().get(pk=wr_locked.wallet_id)
            wallet.balance += wr_locked.amount
            wallet.save(update_fields=['balance'])
            wr_locked.status = 'rejected'
            wr_locked.admin_note = admin_note
            wr_locked.processed_at = timezone.now()
            wr_locked.save()
        Notification.objects.create(
            user=wr.wallet.user,
            title='Pul yechish rad etildi',
            message=f'${wr.amount} hamyoningizga qaytarildi. Sabab: {admin_note or "Ko\'rsatilmadi"}',
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

    dispute = get_object_or_404(Dispute, pk=pk)

    if dispute.status in ('resolved', 'closed'):
        messages.warning(request, 'Bu nizo allaqachon hal qilingan!')
        return redirect('admin_panel')

    decision = request.POST.get('decision', '').strip()
    new_status = request.POST.get('status', 'resolved')

    dispute.admin_decision = decision
    dispute.status = new_status
    dispute.resolved_at = timezone.now()
    dispute.save()

    Notification.objects.create(
        user=dispute.opened_by,
        title='Nizo ko\'rib chiqildi!',
        message=f'Loyiha #{dispute.project_id} bo\'yicha nizo hal qilindi. Admin qarori: {decision[:100]}',
    )
    if dispute.project.expert:
        Notification.objects.create(
            user=dispute.project.expert,
            title='Nizo ko\'rib chiqildi!',
            message=f'Loyiha #{dispute.project_id} bo\'yicha nizo hal qilindi.',
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