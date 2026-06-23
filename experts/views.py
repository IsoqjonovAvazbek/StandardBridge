from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.urls import reverse
import hashlib
import json
import logging
from decimal import Decimal, InvalidOperation

logger = logging.getLogger('standardbridge')
from core.translations import notif_text as _nl
from .models import (
    Project, ProjectUpdate, Document, Notification, Payment,
    Wallet, WalletTransaction, Review, WithdrawalRequest, Dispute, ScopeRequest,
)
from accounts.models import ExpertProfile
from .emails import (
    send_project_to_expert, send_price_set_to_entrepreneur,
    send_payment_confirmed_to_expert, send_project_completed_to_entrepreneur,
    send_counter_offer_to_expert,
    send_scope_request_to_entrepreneur, send_scope_request_response_to_expert,
    _tg, _e,
)


@login_required
def expert_dashboard(request):
    if not request.user.is_expert():
        return redirect('entrepreneur_dashboard')

    projects = Project.objects.filter(expert=request.user).select_related(
        'analysis__local_standard', 'analysis__target_standard', 'entrepreneur'
    ).prefetch_related('analysis__gaps').order_by('-created_at')
    new_projects = Project.objects.filter(status='pending', expert=request.user).select_related(
        'analysis__local_standard', 'analysis__target_standard', 'entrepreneur'
    ).prefetch_related('analysis__gaps').order_by('sla_deadline')
    notifications = Notification.objects.filter(user=request.user, is_read=False)[:5]

    try:
        wallet = request.user.wallet
    except Wallet.DoesNotExist:
        wallet = Wallet.objects.create(user=request.user)

    from django.db.models import Sum, Count, Q
    from datetime import timedelta

    # Bir aggregate bilan 3 ta count (avval 3 ta alohida query edi)
    counts = projects.aggregate(
        total=Count('pk'),
        in_progress=Count('pk', filter=Q(status='in_progress')),
        completed=Count('pk', filter=Q(status='completed')),
    )

    earnings = Payment.objects.filter(
        project__expert=request.user, status='released'
    ).aggregate(s=Sum('expert_amount'))['s'] or 0

    now = timezone.now()
    week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    last_week_start = week_start - timedelta(days=7)
    payments_qs = Payment.objects.filter(project__expert=request.user, status='released')
    week_earnings = payments_qs.filter(paid_at__gte=week_start).aggregate(s=Sum('expert_amount'))['s'] or 0
    last_week_earnings = payments_qs.filter(
        paid_at__gte=last_week_start, paid_at__lt=week_start
    ).aggregate(s=Sum('expert_amount'))['s'] or 0
    month_earnings = payments_qs.filter(
        paid_at__year=now.year, paid_at__month=now.month
    ).aggregate(s=Sum('expert_amount'))['s'] or 0

    context = {
        'projects': projects,
        'new_projects': new_projects,
        'notifications': notifications,
        'wallet': wallet,
        'total': counts['total'],
        'in_progress': counts['in_progress'],
        'completed': counts['completed'],
        'earnings': earnings,
        'week_earnings': week_earnings,
        'last_week_earnings': last_week_earnings,
        'month_earnings': month_earnings,
    }
    return render(request, 'experts/expert_dashboard.html', context)


@login_required
def project_list(request):
    from analysis.models import GapAnalysis
    latest_analysis = GapAnalysis.objects.filter(
        entrepreneur=request.user
    ).order_by('-created_at').first()
    from accounts.models import ExpertProfile

    if request.user.is_expert():
        from django.core.paginator import Paginator
        from django.db.models import Q as _EQ
        ex_status = request.GET.get('status', '')
        ex_search = request.GET.get('search', '')
        projects_qs = Project.objects.filter(expert=request.user).select_related(
            'entrepreneur', 'analysis__local_standard', 'analysis__target_standard'
        ).order_by('-created_at')
        if ex_status:
            projects_qs = projects_qs.filter(status=ex_status)
        if ex_search:
            projects_qs = projects_qs.filter(
                _EQ(entrepreneur__first_name__icontains=ex_search) |
                _EQ(entrepreneur__last_name__icontains=ex_search) |
                _EQ(entrepreneur__company_name__icontains=ex_search) |
                _EQ(analysis__target_standard__code__icontains=ex_search)
            )
        ex_paginator = Paginator(projects_qs, 15)
        ex_page_obj = ex_paginator.get_page(request.GET.get('page', 1))
        return render(request, 'experts/project_list.html', {
            'projects': ex_page_obj,
            'page_obj': ex_page_obj,
            'experts': [],
            'region_choices': ExpertProfile.REGION_CHOICES,
            'selected_region': '',
            'is_expert': True,
            'ex_status': ex_status,
            'ex_search': ex_search,
            'latest_analysis': latest_analysis,
        })

    region = request.GET.get('region', '')
    search = request.GET.get('search', '')
    standard = request.GET.get('standard', '')
    min_rating = request.GET.get('min_rating', '')
    max_price = request.GET.get('max_price', '')
    sort_by = request.GET.get('sort', 'rating')

    experts = ExpertProfile.objects.filter(
        is_available=True, is_verified=True
    ).select_related('user').exclude(user=request.user)

    if region:
        experts = experts.filter(region=region)
    if standard:
        experts = experts.filter(specializations__icontains=standard)
    if search:
        experts = experts.filter(specializations__icontains=search)
    if min_rating:
        try:
            experts = experts.filter(rating__gte=float(min_rating))
        except ValueError:
            pass
    if max_price:
        try:
            experts = experts.filter(project_price__lte=float(max_price))
        except ValueError:
            pass

    sort_map = {
        'rating': '-rating',
        'price': 'project_price',
        'experience': '-experience_years',
        'projects': '-total_projects',
    }
    experts = experts.order_by(sort_map.get(sort_by, '-rating'))

    region_choices = ExpertProfile.REGION_CHOICES

    sort_options = [
        ('rating', 'Reyting'),
        ('price', 'Narx'),
        ('experience', 'Tajriba'),
        ('projects', 'Loyihalar'),
    ]

    from accounts.models import ExpertProfile as EP
    return render(request, 'experts/project_list.html', {
        'experts': experts,
        'region_choices': region_choices,
        'selected_region': region,
        'search': search,
        'standard': standard,
        'standard_choices': EP.STANDARD_CHOICES,
        'min_rating': min_rating,
        'max_price': max_price,
        'sort_by': sort_by,
        'sort_options': sort_options,
        'is_expert': False,
    })


@login_required
def send_to_expert(request, expert_pk, analysis_pk):
    if not request.user.is_entrepreneur():
        return redirect('expert_dashboard')
    from analysis.models import GapAnalysis
    from accounts.models import CustomUser

    expert_user = get_object_or_404(CustomUser, pk=expert_pk, role='expert',
                                    expert_profile__is_verified=True)
    analysis = get_object_or_404(GapAnalysis, pk=analysis_pk, entrepreneur=request.user)

    if request.method == 'POST':
        message = request.POST.get('message', '')

        # Prevent duplicate project for same analysis + expert
        existing = Project.objects.filter(
            analysis=analysis,
            entrepreneur=request.user,
            expert=expert_user,
        ).exclude(status='cancelled').first()
        if existing:
            messages.warning(request, 'Bu tahlil allaqachon bu mutaxassisga yuborilgan!')
            return redirect('project_detail', pk=existing.pk)

        project = Project.objects.create(
            analysis=analysis,
            entrepreneur=request.user,
            expert=expert_user,
            status='pending',
            entrepreneur_message=message,
        )

        Notification.objects.create(
            user=expert_user,
            title=_nl(expert_user, 'Yangi tahlil keldi!', 'Новый анализ!', 'New analysis!'),
            message=_nl(expert_user,
                f'{request.user.get_full_name()} sizga tahlil yubordi. Narx belgilang.',
                f'{request.user.get_full_name()} отправил вам анализ. Установите цену.',
                f'{request.user.get_full_name()} sent you an analysis. Set a price.'),
            link=reverse('project_detail', args=[project.pk]),
        )
        send_project_to_expert(project)

        messages.success(request, 'Tahlil mutaxassisga yuborildi! Narx belgilanishini kuting.')
        return redirect('project_detail', pk=project.pk)

    try:
        expert_profile = expert_user.expert_profile
    except ExpertProfile.DoesNotExist:
        expert_profile = None

    return render(request, 'experts/send_to_expert.html', {
        'expert_user': expert_user,
        'expert_profile': expert_profile,
        'analysis': analysis,
    })


@login_required
def project_detail(request, pk):
    from analysis.models import Roadmap
    qs = Project.objects.select_related(
        'entrepreneur__entrepreneur_profile',
        'expert',
        'analysis__roadmap',
    ).prefetch_related(
        'updates__author',
        'documents',
        'analysis__gaps',
        'analysis__roadmap__steps',
        'disputes',
    )
    if request.user.is_expert():
        project = get_object_or_404(qs, pk=pk, expert=request.user)
    else:
        project = get_object_or_404(qs, pk=pk, entrepreneur=request.user)

    updates = project.updates.all()
    documents = project.documents.all()
    gaps = project.analysis.gaps.all()

    try:
        payment = project.payment
    except Payment.DoesNotExist:
        payment = None

    roadmap = None
    roadmap_steps = []
    roadmap_progress = 0
    roadmap_done_count = 0
    try:
        roadmap = project.analysis.roadmap
        roadmap_steps = list(roadmap.steps.all().order_by('order'))
        total = len(roadmap_steps)
        roadmap_done_count = sum(1 for s in roadmap_steps if s.is_completed)
        roadmap_progress = int(roadmap_done_count / total * 100) if total > 0 else 0
    except (Roadmap.DoesNotExist, AttributeError):
        pass

    project_disputes = project.disputes.all()

    entrepreneur_profile = None
    try:
        entrepreneur_profile = project.entrepreneur.entrepreneur_profile
    except AttributeError:
        pass

    # Status timeline
    from core.translations import get_translation
    T = get_translation(request.session.get('lang', 'uz'))
    STATUS_ORDER = ['pending', 'negotiating', 'accepted', 'in_progress', 'review', 'completed']
    step_labels = {
        'pending': T.get('proj_step_pending', ''),
        'negotiating': T.get('proj_step_negotiating', ''),
        'accepted': T.get('proj_step_accepted', ''),
        'in_progress': T.get('proj_step_in_progress', ''),
        'review': T.get('proj_step_review', ''),
        'completed': T.get('proj_step_completed', ''),
    }
    current_idx = STATUS_ORDER.index(project.status) if project.status in STATUS_ORDER else 0
    project_steps = [(s, step_labels[s]) for s in STATUS_ORDER]
    project_done_steps = set(STATUS_ORDER[:current_idx])

    scope_requests = project.scope_requests.all()
    pending_scope_request = scope_requests.filter(status='pending').first()

    context = {
        'project': project,
        'updates': updates,
        'documents': documents,
        'gaps': gaps,
        'payment': payment,
        'roadmap': roadmap,
        'roadmap_steps': roadmap_steps,
        'roadmap_progress': roadmap_progress,
        'roadmap_done_count': roadmap_done_count,
        'project_disputes': project_disputes,
        'entrepreneur_profile': entrepreneur_profile,
        'project_steps': project_steps,
        'project_done_steps': project_done_steps,
        'scope_requests': scope_requests,
        'pending_scope_request': pending_scope_request,
    }
    return render(request, 'experts/project_detail.html', context)


@login_required
def project_step_toggle(request, pk, step_pk):
    """AJAX: Expert toggles a roadmap step as done/undone. Entrepreneur can view only."""
    if request.user.is_expert():
        project = get_object_or_404(Project, pk=pk, expert=request.user)
    else:
        return JsonResponse({'error': 'forbidden'}, status=403)

    if project.status == 'completed':
        return JsonResponse({'error': 'Yakunlangan loyihada o\'zgartirish mumkin emas'}, status=403)
    if project.status not in ('in_progress', 'review'):
        return JsonResponse({'error': 'invalid status'}, status=400)

    from analysis.models import RoadmapStep
    step = get_object_or_404(RoadmapStep, pk=step_pk, roadmap__analysis=project.analysis)

    if request.method == 'POST':
        was_completed = step.is_completed
        step.is_completed = not step.is_completed
        step.completed_at = timezone.now() if step.is_completed else None
        step.save()

        roadmap = step.roadmap
        total = roadmap.steps.count()
        completed = roadmap.steps.filter(is_completed=True).count()
        progress = int(completed / total * 100) if total > 0 else 0

        # Notify entrepreneur only when transitioning to all-complete (not on un-check)
        if not was_completed and step.is_completed and completed == total and total > 0:
            _std = f"{getattr(project.analysis.local_standard, 'code', '?')} → {getattr(project.analysis.target_standard, 'code', '?')}"
            Notification.objects.create(
                user=project.entrepreneur,
                title=_nl(project.entrepreneur, "Barcha bosqichlar bajarildi!", 'Все этапы выполнены!', 'All steps completed!'),
                message=_nl(project.entrepreneur,
                    f"Mutaxassis '{_std}' loyihasidagi barcha bosqichlarni bajarib bo'ldi.",
                    f"Эксперт выполнил все этапы проекта '{_std}'.",
                    f"Expert completed all steps of project '{_std}'.")
            )

        return JsonResponse({
            'is_completed': step.is_completed,
            'completed_at': step.completed_at.strftime('%d.%m.%Y %H:%M') if step.completed_at else None,
            'progress': progress,
            'completed': completed,
            'total': total,
        })

    return JsonResponse({'error': 'method not allowed'}, status=405)


@login_required
def project_set_price(request, pk):
    if not request.user.is_expert():
        return redirect('dashboard')
    project = get_object_or_404(Project, pk=pk, expert=request.user)

    # Guard: narx faqat dastlabki bosqichlarda belgilanadi (to'lovdan keyin emas)
    if project.status not in ('pending', 'negotiating'):
        messages.error(request, 'Bu loyiha narxini endi o\'zgartirib bo\'lmaydi!')
        return redirect('project_detail', pk=pk)

    if request.method == 'POST':
        try:
            price = Decimal(str(request.POST.get('price', '0')))
            days = int(request.POST.get('days', 0))
        except (InvalidOperation, ValueError, TypeError):
            messages.error(request, 'Narx va kunlar to\'g\'ri raqam bo\'lishi kerak!')
            return redirect('project_set_price', pk=pk)

        if price <= 0 or days <= 0:
            messages.error(request, 'Narx va muddat 0 dan katta bo\'lishi kerak!')
            return redirect('project_set_price', pk=pk)

        message = request.POST.get('message', '')

        project.expert_price = price
        project.expert_days = days
        project.expert_message = message
        project.status = 'negotiating'
        project.save()

        Notification.objects.create(
            user=project.entrepreneur,
            title=_nl(project.entrepreneur, 'Mutaxassis narx belgiladi!', 'Эксперт установил цену!', 'Expert set a price!'),
            message=_nl(project.entrepreneur,
                f'{request.user.get_full_name()} narx belgiladi: ${price}, {days} kun.',
                f'{request.user.get_full_name()} установил цену: ${price}, {days} дней.',
                f'{request.user.get_full_name()} set price: ${price}, {days} days.'),
            link=reverse('project_detail', args=[project.pk]),
        )
        send_price_set_to_entrepreneur(project)

        messages.success(request, 'Narx yuborildi! Mijoz javobini kuting.')
        return redirect('project_detail', pk=pk)

    return render(request, 'experts/set_price.html', {'project': project})


@login_required
def project_accept(request, pk):
    project = get_object_or_404(Project, pk=pk, entrepreneur=request.user)

    # Guard: faqat narx belgilangan (negotiating) loyihani qabul qilish mumkin
    if project.status != 'negotiating':
        messages.error(request, 'Bu loyihani hozir qabul qilib bo\'lmaydi!')
        return redirect('project_detail', pk=pk)

    if request.method == 'POST':
        project.status = 'accepted'
        project.save()

        if project.expert:
            Notification.objects.create(
                user=project.expert,
                title=_nl(project.expert, 'Mijoz narxni qabul qildi!', 'Клиент принял цену!', 'Client accepted the price!'),
                message=_nl(project.expert,
                    f'{request.user.get_full_name()} narxni qabul qildi. To\'lov kutilmoqda.',
                    f'{request.user.get_full_name()} принял цену. Ожидается оплата.',
                    f'{request.user.get_full_name()} accepted the price. Awaiting payment.'),
                link=reverse('project_detail', args=[project.pk]),
            )

        messages.success(request, 'Narx qabul qilindi! To\'lov sahifasiga o\'ting.')
        return redirect('payment_page', project_pk=pk)

    return redirect('project_detail', pk=pk)


@login_required
def project_counter_offer(request, pk):
    """Tadbirkor narxga qarshi taklif yuboradi."""
    project = get_object_or_404(Project, pk=pk, entrepreneur=request.user)

    if project.status != 'negotiating':
        messages.error(request, 'Qarshi taklif faqat kelishuv bosqichida yuboriladi!')
        return redirect('project_detail', pk=pk)

    if project.counter_status == 'pending':
        messages.warning(request, 'Oldingi qarshi taklifingiz hali ko\'rib chiqilmagan. Mutaxassis javobini kuting.')
        return redirect('project_detail', pk=pk)

    if project.counter_rounds >= 3:
        messages.error(request, 'Maksimal kelishuv (3 ta) turi tugadi. Narxni qabul qiling yoki loyihani bekor qiling.')
        return redirect('project_detail', pk=pk)

    if request.method == 'POST':
        try:
            counter_price = Decimal(str(request.POST.get('counter_price', '0')))
        except (InvalidOperation, ValueError):
            messages.error(request, 'Narxni to\'g\'ri kiriting!')
            return redirect('project_detail', pk=pk)

        if counter_price <= 0:
            messages.error(request, 'Narx 0 dan katta bo\'lishi kerak!')
            return redirect('project_detail', pk=pk)

        if counter_price >= project.expert_price:
            messages.warning(request, 'Qarshi taklif mutaxassis narxidan past bo\'lishi kerak!')
            return redirect('project_detail', pk=pk)

        project.counter_price = counter_price
        project.counter_message = request.POST.get('counter_message', '').strip()
        project.counter_status = 'pending'
        project.counter_rounds = project.counter_rounds + 1
        project.save()

        if project.expert:
            Notification.objects.create(
                user=project.expert,
                title=_nl(project.expert, 'Tadbirkor qarshi taklif yubordi!', 'Предприниматель предложил встречную цену!', 'Entrepreneur sent a counter-offer!'),
                message=_nl(project.expert,
                    f'{request.user.get_full_name()} loyiha #{project.pk} uchun ${counter_price} taklif qildi.',
                    f'{request.user.get_full_name()} предложил ${counter_price} за проект #{project.pk}.',
                    f'{request.user.get_full_name()} offered ${counter_price} for project #{project.pk}.'),
                link=reverse('project_detail', args=[project.pk]),
            )
        send_counter_offer_to_expert(project)
        _tg(project.expert, (
            f"🔄 <b>Yangi qarshi taklif!</b>\n\n"
            f"Tadbirkor <b>{_e(request.user.get_full_name())}</b> loyiha #{project.pk} uchun "
            f"<b>${counter_price}</b> taklif qildi.\n\n"
            f"Platforma: {settings.SITE_URL}/experts/projects/{project.pk}/"
        ))
        messages.success(request, f'Qarshi taklif yuborildi: ${counter_price}. Mutaxassis javobini kuting.')
    return redirect('project_detail', pk=pk)


@login_required
def project_respond_counter(request, pk):
    """Expert qarshi taklifni qabul qiladi yoki rad etadi."""
    project = get_object_or_404(Project, pk=pk, expert=request.user)

    if project.counter_status != 'pending':
        messages.error(request, 'Aktiv qarshi taklif yo\'q!')
        return redirect('project_detail', pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'accept':
            # Tadbirkor o'zi taklif qilgan narx — ikki tomon kelishdi, to'lovga o'tamiz
            project.expert_price = project.counter_price
            project.counter_status = 'accepted'
            project.status = 'accepted'
            project.save()
            from django.urls import reverse
            payment_url = reverse('payment_page', kwargs={'project_pk': project.pk})
            Notification.objects.create(
                user=project.entrepreneur,
                title=_nl(project.entrepreneur, 'Mutaxassis qarshi taklifni qabul qildi!', 'Эксперт принял встречное предложение!', 'Expert accepted the counter-offer!'),
                message=_nl(project.entrepreneur,
                    f'${project.counter_price} narxda kelishildi. To\'lov sahifasiga o\'ting: {payment_url}',
                    f'Договорились на ${project.counter_price}. Перейдите к оплате: {payment_url}',
                    f'Agreed on ${project.counter_price}. Go to payment: {payment_url}'),
            )
            messages.success(request, f'Qarshi taklif qabul qilindi — yangi narx: ${project.counter_price}. Tadbirkor to\'lov qilishini kuting.')
        elif action == 'reject':
            project.counter_status = 'rejected'
            project.save()
            Notification.objects.create(
                user=project.entrepreneur,
                title=_nl(project.entrepreneur, 'Mutaxassis qarshi taklifni rad etdi', 'Эксперт отклонил встречное предложение', 'Expert rejected the counter-offer'),
                message=_nl(project.entrepreneur,
                    f'Loyiha #{project.pk} bo\'yicha asl narx (${project.expert_price}) saqlanadi.',
                    f'По проекту #{project.pk} сохраняется первоначальная цена (${project.expert_price}).',
                    f'For project #{project.pk}, the original price (${project.expert_price}) remains.'),
            )
            messages.info(request, 'Qarshi taklif rad etildi. Asl narx saqlanadi.')
    return redirect('project_detail', pk=pk)


@login_required
def project_messages(request, pk):
    """AJAX: loyiha xabarlarini JSON qaytaradi (real-time chat polling uchun).

    ?after=<id> berilsa, faqat o'sha id dan keyingi yangi xabarlar qaytadi.
    """
    if request.user.is_expert():
        project = get_object_or_404(Project, pk=pk, expert=request.user)
    else:
        project = get_object_or_404(Project, pk=pk, entrepreneur=request.user)

    updates = project.updates.select_related('author').order_by('id')
    after = request.GET.get('after')
    if after:
        try:
            updates = updates.filter(id__gt=int(after))
        except (ValueError, TypeError):
            pass

    data = [{
        'id': u.id,
        'message': u.message,
        'type': u.update_type,
        'is_mine': u.author_id == request.user.id,
        'author': u.author.get_full_name() or u.author.username,
        'author_initial': (u.author.first_name or u.author.username or '?')[0],
        'created_at': u.created_at.strftime('%d.%m %H:%M'),
        'file_url': u.file.url if u.file else '',
        'file_name': u.file_name or '',
    } for u in updates]
    return JsonResponse({'messages': data})


@login_required
def project_update(request, pk):
    if request.user.is_expert():
        project = get_object_or_404(Project, pk=pk, expert=request.user)
    else:
        project = get_object_or_404(Project, pk=pk, entrepreneur=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')
        message_text = request.POST.get('message', '')

        if action == 'message' and (message_text or request.FILES.get('chat_file')):
            import os as _os
            chat_file = request.FILES.get('chat_file')
            upd = ProjectUpdate(
                project=project,
                author=request.user,
                message=message_text,
                update_type='message'
            )
            if chat_file:
                allowed_exts = {'.pdf','.doc','.docx','.xls','.xlsx','.jpg','.jpeg','.png','.gif','.zip','.txt'}
                file_ext = _os.path.splitext(chat_file.name)[1].lower()
                if chat_file.size <= 10 * 1024 * 1024 and file_ext in allowed_exts:
                    upd.file = chat_file
                    upd.file_name = _os.path.basename(chat_file.name)
            upd.save()
            notify_user = project.entrepreneur if request.user.is_expert() else project.expert
            if notify_user:
                _notif_body = message_text[:80] if message_text else f'📎 {upd.file_name}'
                Notification.objects.create(
                    user=notify_user,
                    title=_nl(notify_user, 'Yangi xabar', 'Новое сообщение', 'New message'),
                    message=f'{request.user.get_full_name()}: {_notif_body}'
                )
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                file_url = upd.file.url if upd.file else ''
                return JsonResponse({
                    'success': True, 'id': upd.id,
                    'file_url': file_url, 'file_name': upd.file_name
                })

        elif action == 'progress' and message_text:
            ProjectUpdate.objects.create(
                project=project,
                author=request.user,
                message=message_text,
                update_type='progress'
            )
            Notification.objects.create(
                user=project.entrepreneur,
                title=_nl(project.entrepreneur, 'Yangi progress!', 'Новый прогресс!', 'New progress!'),
                message=f'{request.user.get_full_name()}: {message_text[:100]}',
                link=reverse('project_detail', args=[project.pk]),
            )

        elif action == 'upload' and request.FILES.get('file'):
            import os as _os
            uploaded_file = request.FILES['file']
            allowed_types = {'application/pdf', 'application/msword',
                             'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                             'application/vnd.ms-excel',
                             'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                             'image/jpeg', 'image/png'}
            allowed_exts = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.jpeg', '.png'}
            max_size = 10 * 1024 * 1024  # 10 MB
            file_ext = _os.path.splitext(uploaded_file.name)[1].lower()
            if uploaded_file.size > max_size:
                messages.error(request, 'Fayl hajmi 10 MB dan oshmasligi kerak!')
            elif uploaded_file.content_type not in allowed_types or file_ext not in allowed_exts:
                messages.error(request, 'Ruxsat etilgan formatlar: PDF, Word, Excel, JPG, PNG')
            else:
                Document.objects.create(
                    project=project,
                    uploaded_by=request.user,
                    title=request.POST.get('title', 'Hujjat'),
                    doc_type=request.POST.get('doc_type', 'filled'),
                    file=uploaded_file
                )
                messages.success(request, 'Hujjat yuklandi!')

    return redirect('project_detail', pk=pk)


@login_required
def project_complete(request, pk):
    project = get_object_or_404(Project, pk=pk, expert=request.user)

    if request.method == 'POST' and project.status == 'in_progress':
        # Guard: to'lov held bo'lmasa yakunlash mumkin emas
        try:
            _pay = project.payment
            if _pay.status not in ('held', 'released'):
                messages.error(request, 'To\'lov escrowga kirmagan. Tadbirkor to\'lov qilishi kerak!')
                return redirect('project_detail', pk=pk)
        except Payment.DoesNotExist:
            messages.error(request, 'To\'lov topilmadi. Tadbirkor avval to\'lov qilishi kerak!')
            return redirect('project_detail', pk=pk)

        # Guard: agar roadmap bo'lsa, hech bo'lmasa bitta qadam bajarilgan bo'lsin
        from analysis.models import Roadmap
        try:
            roadmap = project.analysis.roadmap
            if roadmap.steps.exists() and not roadmap.steps.filter(is_completed=True).exists():
                messages.error(request, 'Ishni yakunlashdan oldin kamida bitta bosqichni bajarilgan deb belgilang!')
                return redirect('project_detail', pk=pk)
        except Roadmap.DoesNotExist:
            pass

        project.status = 'review'
        project.review_at = timezone.now()
        project.save()

        ProjectUpdate.objects.create(
            project=project,
            author=request.user,
            message='Ish yakunlandi! Mijoz tekshirib qabul qilishi kutilmoqda.',
            update_type='completed'
        )

        Notification.objects.create(
            user=project.entrepreneur,
            title=_nl(project.entrepreneur, 'Ish yakunlandi!', 'Работа завершена!', 'Work completed!'),
            message=_nl(project.entrepreneur,
                f'{request.user.get_full_name()} ishni tugatdi. Tekshirib qabul qiling.',
                f'{request.user.get_full_name()} завершил работу. Проверьте и примите.',
                f'{request.user.get_full_name()} completed the work. Check and accept.'),
            link=reverse('project_detail', args=[project.pk]),
        )

        messages.success(request, 'Ish yakunlandi! Mijoz qabul qilishi kutilmoqda.')

    return redirect('project_detail', pk=pk)


@login_required
def project_decline(request, pk):
    """Expert loyihani rad etadi — faqat pending statusda."""
    project = get_object_or_404(Project, pk=pk, expert=request.user)
    if project.status != 'pending':
        messages.error(request, 'Bu loyihani rad etib bo\'lmaydi!')
        return redirect('project_detail', pk=pk)
    if request.method == 'POST':
        project.status = 'cancelled'
        project.save()
        Notification.objects.create(
            user=project.entrepreneur,
            title=_nl(project.entrepreneur, 'Mutaxassis loyihani rad etdi', 'Эксперт отклонил проект', 'Expert declined the project'),
            message=_nl(project.entrepreneur,
                f'{request.user.get_full_name()} loyihangizni qabul qilmadi. Boshqa mutaxassis tanlang.',
                f'{request.user.get_full_name()} не принял ваш проект. Выберите другого эксперта.',
                f'{request.user.get_full_name()} declined your project. Choose another expert.'),
            link=reverse('entrepreneur_dashboard'),
        )
        from .emails import _send
        from .emails import SITE_URL
        if project.entrepreneur.email:
            _send(
                f"Loyiha #{project.pk} rad etildi — StandardBridge",
                (f"Salom {project.entrepreneur.get_full_name()},\n\n"
                 f"Mutaxassis {request.user.get_full_name()} loyiha #{project.pk}ni rad etdi.\n\n"
                 f"Boshqa mutaxassis tanlash uchun:\n{SITE_URL}/dashboard/\n\n"
                 "StandardBridge jamoasi"),
                project.entrepreneur.email
            )
        messages.info(request, 'Loyiha rad etildi.')
        return redirect('expert_dashboard')
    return redirect('project_detail', pk=pk)


@login_required
def project_cancel(request, pk):
    """Tadbirkor loyihani bekor qiladi — faqat pending/negotiating statusda."""
    project = get_object_or_404(Project, pk=pk, entrepreneur=request.user)
    if project.status not in ('pending', 'negotiating'):
        messages.error(request, 'Bu loyihani bekor qilib bo\'lmaydi — to\'lov amalga oshgan yoki ish boshlangan!')
        return redirect('project_detail', pk=pk)
    if request.method == 'POST':
        project.status = 'cancelled'
        project.save()
        if project.expert:
            Notification.objects.create(
                user=project.expert,
                title=_nl(project.expert, 'Tadbirkor loyihani bekor qildi', 'Предприниматель отменил проект', 'Entrepreneur cancelled the project'),
                message=_nl(project.expert,
                    f'{project.entrepreneur.get_full_name()} loyihani bekor qildi.',
                    f'{project.entrepreneur.get_full_name()} отменил проект.',
                    f'{project.entrepreneur.get_full_name()} cancelled the project.'),
                link=reverse('expert_dashboard'),
            )
        messages.info(request, 'Loyiha bekor qilindi.')
        return redirect('entrepreneur_dashboard')
    return redirect('project_detail', pk=pk)


@login_required
def project_request_revision(request, pk):
    """Entrepreneur ishni qabul qilmay, qayta ishlashga qaytaradi (review -> in_progress)."""
    project = get_object_or_404(Project, pk=pk, entrepreneur=request.user)

    if request.method == 'POST' and project.status == 'review':
        reason = request.POST.get('reason', '').strip()
        if not reason:
            messages.error(request, 'Qayta ishlash sababini kiriting!')
            return redirect('project_detail', pk=pk)

        project.status = 'in_progress'
        project.save()

        # Roadmap qadamlarini reset — faqat bu loyiha uchun (boshqa loyihalar shu
        # analysis dan foydalanayotgan bo'lsa, ularning qadamlarini o'zgartirmaymiz)
        from analysis.models import RoadmapStep
        try:
            other_active = Project.objects.filter(
                analysis=project.analysis
            ).exclude(pk=project.pk).exclude(status__in=['cancelled', 'completed']).exists()
            if not other_active:
                RoadmapStep.objects.filter(
                    roadmap=project.analysis.roadmap
                ).update(is_completed=False, completed_at=None)
        except Exception as _e:
            logger.warning('Roadmap reset qilinmadi (project_pk=%s): %s', pk, _e)

        ProjectUpdate.objects.create(
            project=project,
            author=request.user,
            message=f'Mijoz qayta ishlashni so\'radi: {reason}',
            update_type='message',
        )
        if project.expert:
            Notification.objects.create(
                user=project.expert,
                title=_nl(project.expert, '🔄 Qayta ishlash so\'raldi', '🔄 Запрошена доработка', '🔄 Revision requested'),
                message=_nl(project.expert,
                    f'{request.user.get_full_name()} ishni qabul qilmadi: {reason[:100]}',
                    f'{request.user.get_full_name()} не принял работу: {reason[:100]}',
                    f'{request.user.get_full_name()} did not accept the work: {reason[:100]}'),
            )
        messages.info(request, 'Ish mutaxassisga qayta ishlash uchun qaytarildi.')

    return redirect('project_detail', pk=pk)


@login_required
def payment_page(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk, entrepreneur=request.user)
    try:
        payment = project.payment
    except Payment.DoesNotExist:
        payment = None

    # Payment ob'ekti har doim yaratilishi kerak (Click yoki mock uchun)
    if project.status == 'accepted':
        with transaction.atomic():
            payment, _ = Payment.objects.get_or_create(
                project=project,
                defaults={
                    'entrepreneur': request.user,
                    'amount': project.expert_price,
                    'status': 'pending',
                }
            )
            if payment.status == 'pending' and payment.amount != project.expert_price:
                payment.amount = project.expert_price
                payment.save(update_fields=['amount', 'platform_fee', 'expert_amount'])

    click_return_url = request.build_absolute_uri(
        reverse('project_detail', args=[project.pk])
    )
    return render(request, 'experts/payment.html', {
        'project': project,
        'payment': payment,
        'click_service_id': settings.CLICK_SERVICE_ID,
        'click_merchant_id': settings.CLICK_MERCHANT_ID,
        'click_return_url': click_return_url,
    })


@login_required
def payment_confirm(request, project_pk):
    if request.method != 'POST':
        return redirect('payment_page', project_pk=project_pk)

    # MOCK to'lov DEBUG yoki TEST rejimida ishlaydi. Production'da Click.uz majburiy.
    if not (settings.DEBUG or getattr(settings, 'TESTING', False)):
        messages.error(request, 'To\'lov Click.uz orqali amalga oshiriladi.')
        return redirect('payment_page', project_pk=project_pk)

    project = get_object_or_404(Project, pk=project_pk, entrepreneur=request.user)

    # Guard: only allow payment when status is 'accepted'
    if project.status != 'accepted':
        messages.warning(request, 'Loyiha to\'lov qilishga tayyor emas!')
        return redirect('project_detail', pk=project_pk)

    # Guard: expert tayinlanmagan bo'lsa to'lov qilinmaydi
    if not project.expert:
        messages.error(request, 'Mutaxassis tayinlanmagan. Admin bilan bog\'laning.')
        return redirect('project_detail', pk=project_pk)

    with transaction.atomic():
        project = Project.objects.select_for_update().get(pk=project_pk)
        # Expert hali ham tayinlanganligini atomic ichida qayta tekshirish
        if not project.expert:
            messages.error(request, 'Mutaxassis hisobi topilmadi. Admin bilan bog\'laning.')
            return redirect('project_detail', pk=project_pk)
        # Guard: prevent double payment
        existing_payment = Payment.objects.filter(project=project).first()
        if existing_payment:
            if existing_payment.status in ('held', 'released'):
                messages.warning(request, 'Bu loyiha uchun to\'lov allaqachon amalga oshirilgan!')
                return redirect('project_detail', pk=project_pk)
            payment = existing_payment
            payment.amount = project.expert_price
        else:
            payment = Payment(
                project=project,
                entrepreneur=request.user,
                amount=project.expert_price,
            )

        payment.status = 'held'
        payment.paid_at = timezone.now()
        payment.payme_transaction_id = f'MOCK-{project.pk}-{timezone.now().timestamp():.0f}'
        if payment.pk:
            payment.save(update_fields=['status', 'paid_at', 'payme_transaction_id', 'amount', 'platform_fee', 'expert_amount'])
        else:
            payment.save()

        project.status = 'in_progress'
        project.started_at = timezone.now()
        if project.expert_days and project.expert_days > 0:
            from datetime import timedelta
            project.work_deadline = timezone.now() + timedelta(days=project.expert_days)
        project.save()

    if project.expert:
        Notification.objects.create(
            user=project.expert,
            title=_nl(project.expert, '💰 To\'lov amalga oshirildi!', '💰 Оплата произведена!', '💰 Payment made!'),
            message=_nl(project.expert,
                f'{request.user.get_full_name()} loyiha #{project.pk} uchun ${payment.amount} to\'lov qildi. Ish boshlashingiz mumkin!',
                f'{request.user.get_full_name()} оплатил ${payment.amount} за проект #{project.pk}. Можете начинать работу!',
                f'{request.user.get_full_name()} paid ${payment.amount} for project #{project.pk}. You may start working!'),
            link=reverse('project_detail', args=[project.pk]),
        )
        send_payment_confirmed_to_expert(project, payment)

    messages.success(request, f'To\'lov muvaffaqiyatli! ${payment.amount} escrowda saqlanmoqda.')
    return redirect('project_detail', pk=project_pk)

@login_required
def payment_release(request, project_pk):
    if request.method != 'POST':
        return redirect('project_detail', pk=project_pk)

    project = get_object_or_404(Project, pk=project_pk, entrepreneur=request.user)

    # Guard: payment can only be released after expert submits work for review
    if project.status != 'review':
        messages.warning(request, 'Loyiha hali tekshiruvga topshirilmagan! Expert ishni yakunlab "Tekshiruvga topshirish" bosishi kerak.')
        return redirect('project_detail', pk=project_pk)

    if not project.expert:
        messages.error(request, 'Mutaxassis hisobi topilmadi. Admin bilan bog\'laning.')
        return redirect('project_detail', pk=project_pk)

    # Guard: ochiq nizo bo'lsa pul muzlatiladi (admin hal qilmaguncha)
    if project.disputes.filter(status__in=('open', 'in_review')).exists():
        messages.warning(request, 'Bu loyiha bo\'yicha ochiq nizo bor — admin hal qilmaguncha to\'lov bloklangan.')
        return redirect('project_detail', pk=project_pk)

    try:
        with transaction.atomic():
            payment = Payment.objects.select_for_update().get(project=project)
            if payment.status == 'held':
                payment.status = 'released'
                payment.released_at = timezone.now()
                payment.save(update_fields=['status', 'released_at'])

                project.status = 'completed'
                project.completed_at = timezone.now()
                project.save()

                Wallet.objects.get_or_create(user=project.expert)
                wallet = Wallet.objects.select_for_update().get(user=project.expert)

                wallet.balance += payment.expert_amount
                wallet.save()

                WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=payment.expert_amount,
                    transaction_type='income',
                    description=f'Loyiha #{project.pk} uchun to\'lov',
                    project=project
                )

                if project.expert:
                    Notification.objects.create(
                        user=project.expert,
                        title=_nl(project.expert, 'Pul hamyoningizga tushdi!', 'Деньги поступили на ваш кошелёк!', 'Money received in your wallet!'),
                        message=_nl(project.expert,
                            f'${payment.expert_amount} hamyoningizga o\'tkazildi.',
                            f'${payment.expert_amount} переведено на ваш кошелёк.',
                            f'${payment.expert_amount} transferred to your wallet.'),
                        link=reverse('wallet'),
                    )
                    send_project_completed_to_entrepreneur(project, payment)
                    from .emails import _send, SITE_URL
                    if project.expert.email:
                        _send(
                            f"${payment.expert_amount} hamyoningizga tushdi — StandardBridge",
                            (f"Salom {project.expert.get_full_name()},\n\n"
                             f"Loyiha #{project.pk} muvaffaqiyatli yakunlandi!\n\n"
                             f"  To'lov: ${payment.expert_amount} hamyoningizga o'tkazildi.\n\n"
                             f"Hamyon: {SITE_URL}/experts/wallet/\n\n"
                             "StandardBridge jamoasi"),
                            project.expert.email
                        )

                messages.success(request, f'Loyiha yakunlandi! ${payment.expert_amount} mutaxassisga o\'tkazildi.')
            else:
                messages.warning(request, 'To\'lov allaqachon amalga oshirilgan.')
    except Payment.DoesNotExist:
        messages.error(request, 'To\'lov topilmadi.')
    except Exception as e:
        logger.exception('payment_release xatosi (project_pk=%s): %s', project_pk, e)
        messages.error(request, 'Kutilmagan xatolik yuz berdi. Iltimos, qayta urinib ko\'ring.')

    return redirect('project_detail', pk=project_pk)


@login_required
def wallet(request):
    if not request.user.is_expert():
        return redirect('entrepreneur_dashboard')

    try:
        user_wallet = request.user.wallet
    except Wallet.DoesNotExist:
        user_wallet = Wallet.objects.create(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_card':
            import re as _re
            raw_card = request.POST.get('card_number', '').replace(' ', '').strip()
            card_holder = request.POST.get('card_holder', '').strip()
            card_expiry = request.POST.get('card_expiry', '').strip()
            # Karta raqami bo'sh bo'lsa — faqat holder/expiry yangilansin
            # Validatsiyalar — hammasi oldin, o'zgartirish keyin
            errors = []
            if raw_card:
                if len(raw_card) < 16 or len(raw_card) > 19:
                    errors.append('Karta raqami 16-19 ta raqamdan iborat bo\'lishi kerak!')
                elif not raw_card.isdigit():
                    errors.append('Karta raqami faqat raqamlardan iborat bo\'lishi kerak!')
                elif not card_holder:
                    errors.append('Karta egasining ismini kiriting!')
            elif not card_holder and not card_expiry:
                errors.append('Karta raqamini kiriting!')
            if card_expiry:
                if not _re.match(r'^\d{2}/\d{2}$', card_expiry):
                    errors.append('Amal qilish muddati MM/YY formatida bo\'lishi kerak!')
                else:
                    from datetime import date as _date
                    try:
                        exp_month, exp_year = int(card_expiry[:2]), int(card_expiry[3:]) + 2000
                        if not (1 <= exp_month <= 12):
                            errors.append('Oy 01-12 oralig\'ida bo\'lishi kerak!')
                        elif exp_year > timezone.now().year + 25:
                            errors.append('Karta muddati juda uzoq — qayta tekshiring!')
                        elif _date(exp_year, exp_month, 1) < timezone.now().date().replace(day=1):
                            errors.append('Kartaning amal qilish muddati o\'tib ketgan!')
                    except ValueError:
                        errors.append('Amal qilish muddati noto\'g\'ri!')

            if errors:
                for e in errors:
                    messages.error(request, e)
            else:
                if raw_card:
                    user_wallet.card_number = raw_card[-4:]
                if card_holder:
                    user_wallet.card_holder = card_holder
                if card_expiry:
                    user_wallet.card_expiry = card_expiry
                user_wallet.save()
                messages.success(request, 'Karta ma\'lumotlari saqlandi!')
        elif action == 'withdraw':
            amount_str = request.POST.get('amount', '0')
            try:
                amount = Decimal(str(amount_str)).quantize(Decimal('0.01'))
            except (InvalidOperation, ValueError):
                amount = Decimal('0')
            card_num = request.POST.get('withdraw_card', '').replace(' ', '').strip()
            card_holder = request.POST.get('withdraw_holder', '').strip()
            note = request.POST.get('withdraw_note', '').strip()
            if amount <= 0:
                messages.error(request, 'Summa 0 dan katta bo\'lishi kerak!')
            elif amount > user_wallet.balance:
                messages.error(request, f'Balans yetarli emas! Mavjud: ${user_wallet.balance}')
            elif not card_num:
                messages.error(request, 'Karta raqamini kiriting!')
            elif not card_num.isdigit() or not (16 <= len(card_num) <= 19):
                messages.error(request, 'Karta raqami 16-19 ta raqamdan iborat bo\'lishi kerak!')
            else:
                from .crypto import encrypt_card
                with transaction.atomic():
                    locked_wallet = Wallet.objects.select_for_update().get(pk=user_wallet.pk)
                    if amount > locked_wallet.balance:
                        messages.error(request, f'Balans yetarli emas! Mavjud: ${locked_wallet.balance}')
                    else:
                        locked_wallet.balance -= amount
                        locked_wallet.save(update_fields=['balance'])
                        WalletTransaction.objects.create(
                            wallet=locked_wallet,
                            amount=amount,
                            transaction_type='withdrawal',
                            description=f'Pul yechish so\'rovi — karta *{card_num[-4:]}',
                        )
                        WithdrawalRequest.objects.create(
                            wallet=locked_wallet,
                            amount=amount,
                            card_number=encrypt_card(card_num),
                            card_holder=card_holder,
                            note=note,
                        )
                        messages.success(request, f'${amount:.2f} yechish so\'rovi yuborildi! 1-3 ish kuni ichida kartangizga o\'tkaziladi.')

    from django.core.paginator import Paginator as _Pag
    tx_qs = user_wallet.transactions.all()
    tx_paginator = _Pag(tx_qs, 20)
    tx_page = tx_paginator.get_page(request.GET.get('page'))
    withdrawal_requests = user_wallet.withdrawal_requests.all()[:10]

    # CSV export
    if request.GET.get('export') == 'csv':
        import csv
        from django.http import HttpResponse
        resp = HttpResponse(content_type='text/csv; charset=utf-8')
        resp['Content-Disposition'] = 'attachment; filename="wallet_transactions.csv"'
        resp.write('﻿')  # BOM — Excel UTF-8 to'g'ri o'qisin
        writer = csv.writer(resp)
        writer.writerow(['Sana', 'Turi', 'Miqdor ($)', 'Izoh'])
        for tx in tx_qs:
            writer.writerow([
                tx.created_at.strftime('%d.%m.%Y %H:%M'),
                tx.get_transaction_type_display(),
                tx.amount,
                tx.description,
            ])
        return resp

    return render(request, 'experts/wallet.html', {
        'wallet': user_wallet,
        'transactions': tx_page,
        'tx_page_obj': tx_page,
        'withdrawal_requests': withdrawal_requests,
    })


@login_required
def notifications(request):
    from django.core.paginator import Paginator
    filter_unread = request.GET.get('filter') == 'unread'
    notifs_qs = Notification.objects.filter(user=request.user)
    unread_count = notifs_qs.filter(is_read=False).count()
    if filter_unread:
        display_qs = notifs_qs.filter(is_read=False)
    else:
        notifs_qs.filter(is_read=False).update(is_read=True)
        display_qs = notifs_qs
    paginator = Paginator(display_qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    try:
        wallet = request.user.wallet
    except Wallet.DoesNotExist:
        wallet = None

    return render(request, 'experts/notifications.html', {
        'notifications': page_obj,
        'page_obj': page_obj,
        'wallet': wallet,
        'filter_unread': filter_unread,
        'unread_count': unread_count,
    })
@login_required
def expert_profile(request):
    if not request.user.is_expert():
        return redirect('entrepreneur_dashboard')
    try:
        profile = request.user.expert_profile
    except ExpertProfile.DoesNotExist:
        profile = ExpertProfile.objects.create(user=request.user)
    return render(request, 'experts/expert_profile.html', {'profile': profile})


@login_required
def expert_profile_edit(request):
    if not request.user.is_expert():
        return redirect('entrepreneur_dashboard')
    try:
        profile = request.user.expert_profile
    except ExpertProfile.DoesNotExist:
        profile = ExpertProfile.objects.create(user=request.user)

    if request.method == 'POST':
        def _safe_int(val, default=0):
            try:
                return max(0, int(val))
            except (ValueError, TypeError):
                return default

        def _safe_decimal(val, default=Decimal('0')):
            try:
                d = Decimal(str(val).strip() or '0')
                return d if d >= 0 else default
            except (InvalidOperation, ValueError, TypeError):
                return default

        profile.bio = request.POST.get('bio', '')
        profile.specializations = request.POST.get('specializations', '')
        profile.experience_years = _safe_int(request.POST.get('experience_years', 0))
        profile.project_price = _safe_decimal(request.POST.get('project_price', 0))
        profile.completion_days = _safe_int(request.POST.get('completion_days', 0))
        profile.phone = request.POST.get('phone', '')
        profile.region = request.POST.get('region', '')
        profile.certificates = request.POST.get('certificates', '')
        profile.is_available = request.POST.get('is_available') == 'on'
        profile.cert_number = request.POST.get('cert_number', '').strip()
        profile.issuing_body = request.POST.get('issuing_body', '').strip()
        cert_expiry_raw = request.POST.get('cert_expiry', '').strip()
        if cert_expiry_raw:
            try:
                from datetime import datetime as _dt
                profile.cert_expiry = _dt.strptime(cert_expiry_raw, '%Y-%m-%d').date()
            except ValueError:
                profile.cert_expiry = None
        else:
            profile.cert_expiry = None
        # Standart teglari (checkbox ro'yxati)
        valid_codes = {c[0] for c in ExpertProfile.STANDARD_CHOICES}
        profile.standard_tags = [t for t in request.POST.getlist('standard_tags') if t in valid_codes]
        profile.save()
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.save()
        messages.success(request, 'Profil yangilandi!')
        return redirect('expert_profile')

    return render(request, 'experts/expert_profile_edit.html', {'profile': profile})
@login_required
def expert_detail(request, expert_pk):
    from accounts.models import CustomUser, ExpertProfile
    from analysis.models import GapAnalysis

    expert_user = get_object_or_404(CustomUser, pk=expert_pk, role='expert',
                                    expert_profile__is_verified=True)
    try:
        expert_profile = expert_user.expert_profile
    except ExpertProfile.DoesNotExist:
        expert_profile = None

    analyses = (
        GapAnalysis.objects.filter(entrepreneur=request.user, status='completed').order_by('-created_at')
        if request.user.is_authenticated else []
    )

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(f'/accounts/login/?next=/experts/expert/{expert_pk}/')
        analysis_id = request.POST.get('analysis_id', '').strip()
        message = request.POST.get('message', '')

        if not analysis_id:
            messages.error(request, 'Tahlilni tanlang!')
            return redirect('expert_detail', expert_pk=expert_pk)

        from analysis.models import GapAnalysis
        analysis = get_object_or_404(GapAnalysis, pk=analysis_id, entrepreneur=request.user)

        # Prevent sending the same analysis to the same expert twice (allow re-send only after completed)
        existing = Project.objects.filter(
            analysis=analysis,
            entrepreneur=request.user,
            expert=expert_user,
        ).exclude(status__in=['cancelled', 'completed']).first()
        if existing:
            messages.warning(request, 'Bu tahlil allaqachon bu mutaxassisga yuborilgan!')
            return redirect('project_detail', pk=existing.pk)

        project = Project.objects.create(
            analysis=analysis,
            entrepreneur=request.user,
            expert=expert_user,
            status='pending',
            entrepreneur_message=message,
        )

        Notification.objects.create(
            user=expert_user,
            title=_nl(expert_user, '🔔 Yangi tahlil keldi!', '🔔 Новый анализ!', '🔔 New analysis!'),
            message=_nl(expert_user,
                f'{request.user.get_full_name()} ({request.user.company_name}) sizga tahlil yubordi. Narx belgilang.',
                f'{request.user.get_full_name()} ({request.user.company_name}) отправил вам анализ. Установите цену.',
                f'{request.user.get_full_name()} ({request.user.company_name}) sent you an analysis. Set a price.')
        )
        send_project_to_expert(project)

        messages.success(request, 'Tahlil mutaxassisga yuborildi! Narx belgilanishini kuting.')
        return redirect('project_detail', pk=project.pk)

    reviews = Review.objects.filter(expert=expert_user).select_related('entrepreneur').order_by('-created_at')[:30]

    return render(request, 'experts/expert_detail.html', {
        'expert_user': expert_user,
        'expert_profile': expert_profile,
        'analyses': analyses,
        'reviews': reviews,
    })


@login_required
def leave_review(request, pk):
    project = get_object_or_404(Project, pk=pk, entrepreneur=request.user)

    if project.status != 'completed':
        messages.error(request, 'Faqat yakunlangan loyihaga baho beriladi!')
        return redirect('project_detail', pk=pk)

    if hasattr(project, 'review'):
        messages.warning(request, 'Siz allaqachon baho bergansiz!')
        return redirect('project_detail', pk=pk)

    if not project.expert:
        messages.error(request, 'Bu loyihaning mutaxassisi topilmadi.')
        return redirect('project_detail', pk=pk)

    if request.method == 'POST':
        try:
            rating = int(request.POST.get('rating', 5))
        except (ValueError, TypeError):
            rating = 5
        rating = max(1, min(5, rating))  # 1..5 oralig'ida
        comment = request.POST.get('comment', '')

        from django.db.models import Avg
        with transaction.atomic():
            Review.objects.create(
                project=project,
                entrepreneur=request.user,
                expert=project.expert,
                rating=rating,
                comment=comment,
            )
            expert_profile = ExpertProfile.objects.select_for_update().get(user=project.expert)
            agg = Review.objects.filter(expert=project.expert).aggregate(avg=Avg('rating'))
            expert_profile.rating = agg['avg'] or 0
            expert_profile.total_projects = Project.objects.filter(
                expert=project.expert, status='completed'
            ).count()
            expert_profile.save(update_fields=['rating', 'total_projects'])

        Notification.objects.create(
            user=project.expert,
            title=_nl(project.expert, 'Yangi baho!', 'Новый отзыв!', 'New rating!'),
            message=_nl(project.expert,
                f'{request.user.get_full_name()} sizga {rating}/5 baho berdi.',
                f'{request.user.get_full_name()} поставил вам оценку {rating}/5.',
                f'{request.user.get_full_name()} gave you a {rating}/5 rating.'),
            link=reverse('project_detail', args=[project.pk]),
        )

        messages.success(request, 'Rahmat! Bahoyingiz qabul qilindi.')
        return redirect('project_detail', pk=pk)

    return render(request, 'experts/leave_review.html', {'project': project})


# ─── Click To'lov ──────────────────────────────────────────────

def _click_sign(click_trans_id, service_id, secret_key, merchant_trans_id, amount, action, sign_time):
    sign_string = f"{click_trans_id}{service_id}{secret_key}{merchant_trans_id}{amount}{action}{sign_time}"
    return hashlib.md5(sign_string.encode()).hexdigest()


_CLICK_ALLOWED_IPS = {
    '91.204.239.44', '91.204.239.45', '91.204.239.46', '91.204.239.47',
    '195.158.29.56', '195.158.29.57',
}


def _click_ip_ok(request):
    # Proxy (Railway) ortida ishlaganda REMOTE_ADDR proxy'ning o'z IP'si bo'ladi.
    # X-Forwarded-For'ning eng oxirgi (o'ng) IP'si eng ishonchli — proxy tomonidan qo'shilgan.
    # Birinchi (chap) IP esa foydalanuvchi tomonidan soxtalashtirish mumkin.
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded:
        # Eng o'ng IP — proxy infratuzilmasi tomonidan qo'shilgan
        client_ip = forwarded.split(',')[-1].strip()
    else:
        client_ip = request.META.get('REMOTE_ADDR', '')
    if not _CLICK_ALLOWED_IPS:
        return False
    return client_ip in _CLICK_ALLOWED_IPS


@csrf_exempt
def click_prepare(request):
    if request.method != 'POST':
        return JsonResponse({'error': -8, 'error_note': 'Bad request'})

    if not _click_ip_ok(request):
        logger.warning('Click prepare blocked: bad IP %s', request.META.get('REMOTE_ADDR'))
        return JsonResponse({'error': -1, 'error_note': 'Forbidden'})

    data = request.POST
    click_trans_id = data.get('click_trans_id', '')
    service_id = data.get('service_id', '')
    merchant_trans_id = data.get('merchant_trans_id', '')
    amount = data.get('amount', '')
    action = data.get('action', '')
    sign_time = data.get('sign_time', '')
    sign_string = data.get('sign_string', '')

    # Basic type/length guards to prevent abuse
    if len(click_trans_id) > 64 or len(merchant_trans_id) > 64:
        return JsonResponse({'click_trans_id': click_trans_id, 'merchant_trans_id': merchant_trans_id,
                             'merchant_prepare_id': None, 'error': -8, 'error_note': 'Invalid request'})
    try:
        Decimal(amount)
    except (InvalidOperation, ValueError, TypeError):
        return JsonResponse({'click_trans_id': click_trans_id, 'merchant_trans_id': merchant_trans_id,
                             'merchant_prepare_id': None, 'error': -8, 'error_note': 'Invalid amount'})

    try:
        ts_diff = abs(int(timezone.now().timestamp()) - int(sign_time or 0))
        if ts_diff > 3600:
            return JsonResponse({'click_trans_id': click_trans_id, 'merchant_trans_id': merchant_trans_id,
                                 'merchant_prepare_id': None, 'error': -1, 'error_note': 'Request expired'})
    except (ValueError, TypeError):
        return JsonResponse({'click_trans_id': click_trans_id, 'merchant_trans_id': merchant_trans_id,
                             'merchant_prepare_id': None, 'error': -1, 'error_note': 'Invalid sign_time'})

    if str(service_id) != str(settings.CLICK_SERVICE_ID):
        return JsonResponse({'click_trans_id': click_trans_id, 'merchant_trans_id': merchant_trans_id,
                             'merchant_prepare_id': None, 'error': -1, 'error_note': 'Invalid service'})

    expected_sign = _click_sign(
        click_trans_id, service_id,
        settings.CLICK_SECRET_KEY,
        merchant_trans_id, amount, action, sign_time
    )

    if sign_string != expected_sign:
        return JsonResponse({'click_trans_id': click_trans_id, 'merchant_trans_id': merchant_trans_id,
                             'merchant_prepare_id': None, 'error': -1, 'error_note': 'Sign check failed'})

    try:
        payment = Payment.objects.get(pk=merchant_trans_id)
    except Payment.DoesNotExist:
        return JsonResponse({'click_trans_id': click_trans_id, 'merchant_trans_id': merchant_trans_id,
                             'merchant_prepare_id': None, 'error': -5, 'error_note': 'Payment not found'})

    if Decimal(str(amount)) != payment.amount:
        return JsonResponse({'click_trans_id': click_trans_id, 'merchant_trans_id': merchant_trans_id,
                             'merchant_prepare_id': None, 'error': -2, 'error_note': 'Incorrect amount'})

    if payment.status == 'held':
        return JsonResponse({'click_trans_id': click_trans_id, 'merchant_trans_id': merchant_trans_id,
                             'merchant_prepare_id': payment.pk, 'error': -4, 'error_note': 'Already paid'})

    return JsonResponse({
        'click_trans_id': click_trans_id,
        'merchant_trans_id': merchant_trans_id,
        'merchant_prepare_id': payment.pk,
        'error': 0,
        'error_note': 'Success',
    })


@csrf_exempt
def click_complete(request):
    if request.method != 'POST':
        return JsonResponse({'error': -8, 'error_note': 'Bad request'})

    if not _click_ip_ok(request):
        logger.warning('Click complete blocked: bad IP %s', request.META.get('REMOTE_ADDR'))
        return JsonResponse({'error': -1, 'error_note': 'Forbidden'})

    data = request.POST
    click_trans_id = data.get('click_trans_id', '')
    service_id = data.get('service_id', '')
    merchant_trans_id = data.get('merchant_trans_id', '')
    merchant_prepare_id = data.get('merchant_prepare_id', '')
    amount = data.get('amount', '')
    action = data.get('action', '')
    sign_time = data.get('sign_time', '')
    sign_string = data.get('sign_string', '')
    try:
        error = int(data.get('error', 0))
    except (ValueError, TypeError):
        error = 0

    if len(click_trans_id) > 64 or len(merchant_trans_id) > 64:
        return JsonResponse({'click_trans_id': click_trans_id, 'merchant_trans_id': merchant_trans_id,
                             'merchant_confirm_id': None, 'error': -8, 'error_note': 'Invalid request'})
    try:
        Decimal(amount)
    except (InvalidOperation, ValueError, TypeError):
        return JsonResponse({'click_trans_id': click_trans_id, 'merchant_trans_id': merchant_trans_id,
                             'merchant_confirm_id': None, 'error': -8, 'error_note': 'Invalid amount'})

    try:
        ts_diff = abs(int(timezone.now().timestamp()) - int(sign_time or 0))
        if ts_diff > 3600:
            return JsonResponse({'click_trans_id': click_trans_id, 'merchant_trans_id': merchant_trans_id,
                                 'merchant_confirm_id': None, 'error': -1, 'error_note': 'Request expired'})
    except (ValueError, TypeError):
        return JsonResponse({'click_trans_id': click_trans_id, 'merchant_trans_id': merchant_trans_id,
                             'merchant_confirm_id': None, 'error': -1, 'error_note': 'Invalid sign_time'})

    if str(service_id) != str(settings.CLICK_SERVICE_ID):
        return JsonResponse({'click_trans_id': click_trans_id, 'merchant_trans_id': merchant_trans_id,
                             'merchant_confirm_id': None, 'error': -1, 'error_note': 'Invalid service'})

    expected_sign = _click_sign(
        click_trans_id, service_id,
        settings.CLICK_SECRET_KEY,
        merchant_trans_id, amount, action, sign_time
    )

    if sign_string != expected_sign:
        return JsonResponse({'click_trans_id': click_trans_id, 'merchant_trans_id': merchant_trans_id,
                             'merchant_confirm_id': None, 'error': -1, 'error_note': 'Sign check failed'})

    try:
        payment = Payment.objects.get(pk=merchant_trans_id)
    except Payment.DoesNotExist:
        return JsonResponse({'click_trans_id': click_trans_id, 'merchant_trans_id': merchant_trans_id,
                             'merchant_confirm_id': None, 'error': -6, 'error_note': 'Transaction not found'})

    if Decimal(str(amount)) != payment.amount:
        return JsonResponse({'click_trans_id': click_trans_id, 'merchant_trans_id': merchant_trans_id,
                             'merchant_confirm_id': payment.pk, 'error': -2, 'error_note': 'Incorrect amount'})

    if error < 0:
        with transaction.atomic():
            p = Payment.objects.select_for_update().get(pk=payment.pk)
            if p.status not in ('held', 'released'):
                p.status = 'refunded'
                p.save(update_fields=['status'])
        return JsonResponse({'click_trans_id': click_trans_id, 'merchant_trans_id': merchant_trans_id,
                             'merchant_confirm_id': payment.pk, 'error': 0, 'error_note': 'Cancelled'})

    with transaction.atomic():
        payment = Payment.objects.select_for_update().get(pk=payment.pk)
        click_tx_key = f'CLICK-{click_trans_id}'
        if payment.status in ('held', 'released') or payment.payme_transaction_id == click_tx_key:
            # Already processed — idempotent response
            return JsonResponse({'click_trans_id': click_trans_id, 'merchant_trans_id': merchant_trans_id,
                                 'merchant_confirm_id': payment.pk, 'error': 0, 'error_note': 'Success'})

        project = Project.objects.select_for_update().get(pk=payment.project_id)
        if project.status not in ('accepted',):
            # Only transition from accepted; ignore duplicate webhooks for in_progress/completed
            return JsonResponse({'click_trans_id': click_trans_id, 'merchant_trans_id': merchant_trans_id,
                                 'merchant_confirm_id': payment.pk, 'error': 0, 'error_note': 'Success'})

        payment.status = 'held'
        payment.paid_at = timezone.now()
        payment.payme_transaction_id = f'CLICK-{click_trans_id}'
        payment.save(update_fields=['status', 'paid_at', 'payme_transaction_id'])

        project.status = 'in_progress'
        project.started_at = timezone.now()
        if project.expert_days and project.expert_days > 0:
            from datetime import timedelta
            project.work_deadline = timezone.now() + timedelta(days=project.expert_days)
        project.save()

    if project.expert:
        Notification.objects.create(
            user=project.expert,
            title=_nl(project.expert, 'To\'lov amalga oshirildi!', 'Оплата произведена!', 'Payment made!'),
            message=_nl(project.expert,
                f'${payment.amount} to\'lov qilindi. Ish boshlashingiz mumkin!',
                f'${payment.amount} оплачено. Можете начинать работу!',
                f'${payment.amount} paid. You may start working!')
        )
        send_payment_confirmed_to_expert(project, payment)

    return JsonResponse({
        'click_trans_id': click_trans_id,
        'merchant_trans_id': merchant_trans_id,
        'merchant_confirm_id': payment.pk,
        'error': 0,
        'error_note': 'Success',
    })


# ─── Dispute ────────────────────────────────────────────────────────

@login_required
def open_dispute(request, pk):
    """Entrepreneur opens a dispute for a project in review or completed status."""
    project = get_object_or_404(Project, pk=pk, entrepreneur=request.user)

    if project.status not in ('review', 'in_progress'):
        messages.error(request, 'Nizo faqat jarayondagi yoki tekshiruvdagi loyiha uchun ochiladi!')
        return redirect('project_detail', pk=pk)

    # Allow only one open dispute per project
    existing = project.disputes.filter(status__in=('open', 'in_review')).first()
    if existing:
        messages.warning(request, 'Bu loyiha bo\'yicha allaqachon ochiq nizo mavjud!')
        return redirect('project_detail', pk=pk)

    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        if not reason:
            messages.error(request, 'Nizo sababini kiriting!')
            return redirect('project_detail', pk=pk)

        dispute = Dispute.objects.create(
            project=project,
            opened_by=request.user,
            reason=reason,
        )
        # Notify expert
        if project.expert:
            Notification.objects.create(
                user=project.expert,
                title=_nl(project.expert, '⚠️ Nizo ochildi!', '⚠️ Открыт спор!', '⚠️ Dispute opened!'),
                message=_nl(project.expert,
                    f'{request.user.get_full_name()} loyiha #{project.pk} bo\'yicha nizo ochdi. Admin ko\'rib chiqadi.',
                    f'{request.user.get_full_name()} открыл спор по проекту #{project.pk}. Администратор рассмотрит его.',
                    f'{request.user.get_full_name()} opened a dispute on project #{project.pk}. Admin will review it.'),
                link=reverse('project_detail', args=[project.pk]),
            )
            from .emails import send_dispute_opened
            send_dispute_opened(dispute)
        # Notify all admins at once
        from accounts.models import CustomUser as CU
        admin_users = list(CU.objects.filter(role='admin'))
        Notification.objects.bulk_create([
            Notification(
                user=admin_user,
                title=f'⚠️ Yangi nizo — Loyiha #{project.pk}',
                message=f'{request.user.get_full_name()} nizo ochdi: {reason[:100]}',
                link=reverse('admin_panel'),
            )
            for admin_user in admin_users
        ])
        messages.success(request, 'Nizo muvaffaqiyatli ochildi! Admin 1-2 ish kuni ichida ko\'rib chiqadi.')
    return redirect('project_detail', pk=pk)


# ─── Roadmap Step Management (Expert) ──────────────────────────────

@login_required
def add_roadmap_step(request, pk):
    """Expert adds a custom step to the project roadmap."""
    project = get_object_or_404(Project, pk=pk, expert=request.user)
    if project.status not in ('in_progress', 'review'):
        return JsonResponse({'error': 'invalid status'}, status=400)

    from analysis.models import Roadmap, RoadmapStep
    try:
        roadmap = project.analysis.roadmap
    except Roadmap.DoesNotExist:
        return JsonResponse({'error': 'no roadmap'}, status=400)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        duration_days_str = request.POST.get('duration_days', '0')
        try:
            duration_days = int(duration_days_str)
        except ValueError:
            duration_days = 0

        if not title:
            messages.error(request, 'Qadam nomini kiriting!')
            return redirect('project_detail', pk=pk)

        # Add after existing steps
        max_order = roadmap.steps.count()
        RoadmapStep.objects.create(
            roadmap=roadmap,
            title=title[:200],
            description=description,
            duration_days=duration_days,
            order=max_order + 1,
        )
        roadmap.total_days = sum(s.duration_days for s in roadmap.steps.all())
        roadmap.save(update_fields=['total_days'])
        messages.success(request, 'Yangi qadam qo\'shildi!')
    return redirect('project_detail', pk=pk)


@login_required
def delete_roadmap_step(request, pk, step_pk):
    """Expert deletes a roadmap step."""
    project = get_object_or_404(Project, pk=pk, expert=request.user)
    if project.status not in ('in_progress', 'review'):
        return redirect('project_detail', pk=pk)

    from analysis.models import RoadmapStep, Roadmap
    step = get_object_or_404(RoadmapStep, pk=step_pk, roadmap__analysis=project.analysis)
    if request.method == 'POST':
        roadmap = step.roadmap
        step.delete()
        roadmap.total_days = sum(s.duration_days for s in roadmap.steps.all())
        roadmap.save(update_fields=['total_days'])
        messages.success(request, 'Qadam o\'chirildi!')
    return redirect('project_detail', pk=pk)


@login_required
def edit_roadmap_step(request, pk, step_pk):
    """Expert mavjud qadamning vaqti/nomi/tavsifini aniqlashtiradi (AI taxminini tuzatadi)."""
    project = get_object_or_404(Project, pk=pk, expert=request.user)
    if project.status not in ('in_progress', 'review'):
        return redirect('project_detail', pk=pk)

    from analysis.models import RoadmapStep, Roadmap
    step = get_object_or_404(RoadmapStep, pk=step_pk, roadmap__analysis=project.analysis)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        try:
            duration_days = int(request.POST.get('duration_days', step.duration_days))
        except (ValueError, TypeError):
            duration_days = step.duration_days
        if duration_days < 0:
            duration_days = 0

        if not title:
            messages.error(request, 'Qadam nomini kiriting!')
            return redirect('project_detail', pk=pk)

        step.title = title
        step.description = description
        step.duration_days = duration_days
        step.save()

        # Roadmap umumiy vaqtini qayta hisoblash
        roadmap = step.roadmap
        roadmap.total_days = sum(s.duration_days for s in roadmap.steps.all())
        roadmap.save(update_fields=['total_days'])

        messages.success(request, 'Qadam yangilandi!')
    return redirect('project_detail', pk=pk)

@login_required
def project_contract(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.user != project.entrepreneur and request.user != project.expert:
        from django.http import Http404
        raise Http404
    if project.status not in ('accepted', 'in_progress', 'review', 'completed'):
        messages.error(request, 'Shartnoma faqat qabul qilingan loyihalar uchun mavjud.')
        return redirect('project_detail', pk=pk)
    return render(request, 'experts/contract_print.html', {'project': project})


@login_required
def scope_request_send(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.user != project.expert:
        messages.error(request, 'Ruxsat yo\'q.')
        return redirect('project_detail', pk=pk)
    if project.status not in ('in_progress', 'review'):
        messages.error(request, 'Faqat jarayondagi loyiha uchun mumkin.')
        return redirect('project_detail', pk=pk)
    if request.method != 'POST':
        return redirect('project_detail', pk=pk)

    reason = request.POST.get('reason', '').strip()
    extra_price_raw = request.POST.get('extra_price', '').strip()
    try:
        extra_price = Decimal(extra_price_raw)
        if extra_price <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        messages.error(request, "Narx noto'g'ri kiritildi.")
        return redirect('project_detail', pk=pk)
    if not reason:
        messages.error(request, 'Sabab kiritish majburiy.')
        return redirect('project_detail', pk=pk)

    from django.db import transaction as _stx
    with _stx.atomic():
        locked_project = Project.objects.select_for_update().get(pk=pk)
        if locked_project.scope_requests.filter(status='pending').exists():
            messages.error(request, "Allaqachon javob kutilayotgan so'rov bor.")
            return redirect('project_detail', pk=pk)
        sr = ScopeRequest.objects.create(
            project=project,
            expert=request.user,
            reason=reason,
            extra_price=extra_price,
        )
    Notification.objects.create(
        user=project.entrepreneur,
        title=_nl(project.entrepreneur,
            f"Loyiha #{project.pk} — qo'shimcha ish so'rovi",
            f"Проект #{project.pk} — запрос дополнительной работы",
            f"Project #{project.pk} — scope request"),
        message=_nl(project.entrepreneur,
            f"Mutaxassis +${extra_price} qo'shimcha ish so'rovi yubordi: {reason[:100]}",
            f"Эксперт отправил запрос на +${extra_price} дополнительной работы: {reason[:100]}",
            f"Expert sent a +${extra_price} scope request: {reason[:100]}"),
        link=f"/experts/projects/{project.pk}/",
    )
    send_scope_request_to_entrepreneur(sr)
    messages.success(request, "So'rov tadbirkorga yuborildi.")
    return redirect('project_detail', pk=pk)


@login_required
def scope_request_respond(request, pk, sr_pk):
    project = get_object_or_404(Project, pk=pk)
    if request.user != project.entrepreneur:
        messages.error(request, "Ruxsat yo'q.")
        return redirect('project_detail', pk=pk)
    sr = get_object_or_404(ScopeRequest, pk=sr_pk, project=project, status='pending')
    if request.method != 'POST':
        return redirect('project_detail', pk=pk)

    action = request.POST.get('action')
    if action not in ('accept', 'reject'):
        messages.error(request, "Noto'g'ri amal.")
        return redirect('project_detail', pk=pk)

    from django.db import transaction as _tx
    with _tx.atomic():
        # select_for_update — ikki bir vaqtda accept xabaridan himoya
        sr = ScopeRequest.objects.select_for_update().get(pk=sr_pk, project=project)
        if sr.status != 'pending':
            messages.warning(request, "Bu so'rov allaqachon ko'rib chiqilgan.")
            return redirect('project_detail', pk=pk)
        sr.status = 'accepted' if action == 'accept' else 'rejected'
        sr.responded_at = timezone.now()
        sr.save(update_fields=['status', 'responded_at'])

        if action == 'accept':
            # Payment summasini yangilaymiz — release da expert to'liq summa oladi
            try:
                _pay = Payment.objects.select_for_update().get(project=project)
                if _pay.status == 'held':
                    _pay.amount += sr.extra_price
                    _pay.save()  # triggers Payment.save() fee recomputation
            except Payment.DoesNotExist:
                pass

    if action == 'accept':
        if project.expert:
            Notification.objects.create(
                user=project.expert,
                title=_nl(project.expert,
                    f"Loyiha #{project.pk} — so'rovingiz qabul qilindi",
                    f"Проект #{project.pk} — ваш запрос принят",
                    f"Project #{project.pk} — your request accepted"),
                message=_nl(project.expert,
                    f"Tadbirkor +${sr.extra_price} so'rovingizni qabul qildi.",
                    f"Предприниматель принял ваш запрос на +${sr.extra_price}.",
                    f"Entrepreneur accepted your +${sr.extra_price} request."),
                link=f"/experts/projects/{project.pk}/",
            )
        messages.success(request, f"So'rov qabul qilindi. Qo'shimcha ${sr.extra_price} to'lov hisobga olindi.")
    else:
        if project.expert:
            Notification.objects.create(
                user=project.expert,
                title=_nl(project.expert,
                    f"Loyiha #{project.pk} — so'rovingiz rad etildi",
                    f"Проект #{project.pk} — ваш запрос отклонён",
                    f"Project #{project.pk} — your request rejected"),
                message=_nl(project.expert,
                    "Tadbirkor qo'shimcha ish so'rovini rad etdi.",
                    "Предприниматель отклонил запрос на дополнительную работу.",
                    "Entrepreneur rejected the scope request."),
                link=f"/experts/projects/{project.pk}/",
            )
        messages.info(request, "So'rov rad etildi.")

    send_scope_request_response_to_expert(sr)
    return redirect('project_detail', pk=pk)
