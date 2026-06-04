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
from .models import (
    Project, ProjectUpdate, Document, Notification, Payment,
    Wallet, WalletTransaction, Review, WithdrawalRequest, Dispute,
)
from accounts.models import ExpertProfile
from .emails import (
    send_project_to_expert, send_price_set_to_entrepreneur,
    send_payment_confirmed_to_expert, send_project_completed_to_entrepreneur,
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

    from django.db.models import Sum
    completed_qs = projects.filter(status='completed')
    earnings = Payment.objects.filter(
        project__in=completed_qs, status='released'
    ).aggregate(s=Sum('expert_amount'))['s'] or 0

    context = {
        'projects': projects,
        'new_projects': new_projects,
        'notifications': notifications,
        'wallet': wallet,
        'total': projects.count(),
        'in_progress': projects.filter(status='in_progress').count(),
        'completed': completed_qs.count(),
        'earnings': earnings,
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
        projects = Project.objects.filter(expert=request.user).order_by('-created_at')
        return render(request, 'experts/project_list.html', {
            'projects': projects,
            'experts': [],
            'region_choices': ExpertProfile.REGION_CHOICES,
            'selected_region': '',
            'is_expert': True,
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

    expert_user = get_object_or_404(CustomUser, pk=expert_pk, role='expert')
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
            title='Yangi tahlil keldi!',
            message=f'{request.user.get_full_name()} sizga tahlil yubordi. Narx belgilang.',
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
    if request.user.is_expert():
        project = get_object_or_404(Project, pk=pk, expert=request.user)
    else:
        project = get_object_or_404(Project, pk=pk, entrepreneur=request.user)

    updates = project.updates.all()
    documents = project.documents.all()
    gaps = project.analysis.gaps.all()

    try:
        payment = project.payment
    except Payment.DoesNotExist:
        payment = None

    # Roadmap checklist
    from analysis.models import Roadmap
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
    except Roadmap.DoesNotExist:
        pass

    # Disputes
    project_disputes = project.disputes.all()

    # Entrepreneur profile info (for expert to see company scope)
    entrepreneur_profile = None
    try:
        entrepreneur_profile = project.entrepreneur.entrepreneur_profile
    except AttributeError:
        pass

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
    }
    return render(request, 'experts/project_detail.html', context)


@login_required
def project_step_toggle(request, pk, step_pk):
    """AJAX: Expert toggles a roadmap step as done/undone. Entrepreneur can view only."""
    if request.user.is_expert():
        project = get_object_or_404(Project, pk=pk, expert=request.user)
    else:
        return JsonResponse({'error': 'forbidden'}, status=403)

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
            Notification.objects.create(
                user=project.entrepreneur,
                title="Barcha bosqichlar bajarildi!",
                message=f"Mutaxassis '{project.analysis.local_standard.code} → {project.analysis.target_standard.code}' loyihasidagi barcha bosqichlarni bajarib bo'ldi."
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
            title='Mutaxassis narx belgiladi!',
            message=f'{request.user.get_full_name()} narx belgiladi: ${price}, {days} kun.',
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

        Notification.objects.create(
            user=project.expert,
            title='Mijoz narxni qabul qildi!',
            message=f'{request.user.get_full_name()} narxni qabul qildi. To\'lov kutilmoqda.',
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
        project.save()

        Notification.objects.create(
            user=project.expert,
            title='Tadbirkor qarshi taklif yubordi!',
            message=f'{request.user.get_full_name()} loyiha #{project.pk} uchun ${counter_price} taklif qildi.'
        )
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
                title='Mutaxassis qarshi taklifni qabul qildi!',
                message=f'${project.counter_price} narxda kelishildi. To\'lov sahifasiga o\'ting: {payment_url}',
            )
            messages.success(request, f'Qarshi taklif qabul qilindi — yangi narx: ${project.counter_price}. Tadbirkor to\'lov qilishini kuting.')
        elif action == 'reject':
            project.counter_status = 'rejected'
            project.save()
            Notification.objects.create(
                user=project.entrepreneur,
                title='Mutaxassis qarshi taklifni rad etdi',
                message=f'Loyiha #{project.pk} bo\'yicha asl narx (${project.expert_price}) saqlanadi.',
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

        if action == 'message' and message_text:
            upd = ProjectUpdate.objects.create(
                project=project,
                author=request.user,
                message=message_text,
                update_type='message'
            )
            notify_user = project.entrepreneur if request.user.is_expert() else project.expert
            if notify_user:
                Notification.objects.create(
                    user=notify_user,
                    title='Yangi xabar',
                    message=f'{request.user.get_full_name()}: {message_text[:100]}'
                )
            # AJAX so'rov bo'lsa — JSON qaytaramiz (sahifa qayta yuklanmaydi)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'id': upd.id})

        elif action == 'progress' and message_text:
            ProjectUpdate.objects.create(
                project=project,
                author=request.user,
                message=message_text,
                update_type='progress'
            )
            Notification.objects.create(
                user=project.entrepreneur,
                title='Yangi progress!',
                message=f'{request.user.get_full_name()}: {message_text[:100]}'
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
        # Guard: agar roadmap bo'lsa, hech bo'lmasa bitta qadam bajarilgan bo'lsin
        # (expert hech narsa qilmasdan "yakunladim" deya olmasligi uchun)
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
            title='Ish yakunlandi!',
            message=f'{request.user.get_full_name()} ishni tugatdi. Tekshirib qabul qiling.',
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
            title='Mutaxassis loyihani rad etdi',
            message=f'{request.user.get_full_name()} loyihangizni qabul qilmadi. Boshqa mutaxassis tanlang.',
            link=reverse('entrepreneur_dashboard'),
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
                title='Tadbirkor loyihani bekor qildi',
                message=f'{project.entrepreneur.get_full_name()} loyihani bekor qildi.',
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

        # Roadmap qadamlarini reset — guard o'z maqsadini bajarmaydi aks holda
        from analysis.models import RoadmapStep
        try:
            RoadmapStep.objects.filter(
                roadmap=project.analysis.roadmap
            ).update(is_completed=False, completed_at=None)
        except Exception:
            pass

        ProjectUpdate.objects.create(
            project=project,
            author=request.user,
            message=f'Mijoz qayta ishlashni so\'radi: {reason}',
            update_type='message',
        )
        if project.expert:
            Notification.objects.create(
                user=project.expert,
                title='🔄 Qayta ishlash so\'raldi',
                message=f'{request.user.get_full_name()} ishni qabul qilmadi: {reason[:100]}',
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

    # Click uchun Payment oldindan yaratilishi kerak (merchant_trans_id = payment.pk)
    if project.status == 'accepted' and settings.CLICK_SERVICE_ID:
        if not payment:
            payment = Payment.objects.create(
                project=project,
                entrepreneur=request.user,
                amount=project.expert_price,
                status='pending',
            )
        elif payment.status == 'pending' and payment.amount != project.expert_price:
            # Narx o'zgargan bo'lsa (counter-offer) yangilash
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

    # MOCK to'lov faqat DEBUG rejimida yoki Click credentials yo'q bo'lganda ishlaydi
    if not settings.DEBUG and settings.CLICK_SERVICE_ID:
        messages.error(request, 'To\'lov Click.uz orqali amalga oshiriladi.')
        return redirect('payment_page', project_pk=project_pk)

    project = get_object_or_404(Project, pk=project_pk, entrepreneur=request.user)

    # Guard: only allow payment when status is 'accepted'
    if project.status != 'accepted':
        messages.warning(request, 'Loyiha to\'lov qilishga tayyor emas!')
        return redirect('project_detail', pk=project_pk)

    with transaction.atomic():
        project = Project.objects.select_for_update().get(pk=project_pk)
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
            title='💰 To\'lov amalga oshirildi!',
            message=f'{request.user.get_full_name()} loyiha #{project.pk} uchun ${payment.amount} to\'lov qildi. Ish boshlashingiz mumkin!',
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

                try:
                    wallet = Wallet.objects.select_for_update().get(user=project.expert)
                except Wallet.DoesNotExist:
                    wallet = Wallet.objects.create(user=project.expert)

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
                        title='Pul hamyoningizga tushdi!',
                        message=f'${payment.expert_amount} hamyoningizga o\'tkazildi.',
                        link=reverse('wallet'),
                    )
                    send_project_completed_to_entrepreneur(project, payment)

                # F-12: Referral bonus — faqat birinchi loyihada
                referrer = project.entrepreneur.referred_by
                is_first = not Project.objects.filter(
                    entrepreneur=project.entrepreneur, status='completed'
                ).exclude(pk=project.pk).exists()
                if referrer and is_first:
                    from decimal import Decimal as _D
                    bonus = (payment.platform_fee * _D('0.10')).quantize(_D('0.01'))
                    if bonus > 0:
                        from django.db.models import F as _F
                        ref_wallet, _ = Wallet.objects.get_or_create(user=referrer)
                        Wallet.objects.filter(pk=ref_wallet.pk).update(
                            balance=_F('balance') + bonus
                        )
                        ref_wallet.refresh_from_db(fields=['balance'])
                        WalletTransaction.objects.create(
                            wallet=ref_wallet,
                            amount=bonus,
                            transaction_type='income',
                            description=f'Referral bonus — {project.entrepreneur.get_full_name()} birinchi loyiha',
                        )
                        Notification.objects.create(
                            user=referrer,
                            title='Referral bonus!',
                            message=f'Taklif qilganingiz {project.entrepreneur.get_full_name()} birinchi loyihasini yakunladi. ${bonus} bonus hamyoningizga tushdi!',
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
                if len(raw_card) < 16:
                    errors.append('Karta raqami 16 ta raqamdan iborat bo\'lishi kerak!')
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
                        elif _date(exp_year, exp_month, 1) < _date.today().replace(day=1):
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
            card_num = request.POST.get('withdraw_card', '').strip()
            card_holder = request.POST.get('withdraw_holder', '').strip()
            note = request.POST.get('withdraw_note', '').strip()
            if amount <= 0:
                messages.error(request, 'Summa 0 dan katta bo\'lishi kerak!')
            elif amount > user_wallet.balance:
                messages.error(request, f'Balans yetarli emas! Mavjud: ${user_wallet.balance}')
            elif not card_num:
                messages.error(request, 'Karta raqamini kiriting!')
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

    transactions = user_wallet.transactions.all()[:20]
    withdrawal_requests = user_wallet.withdrawal_requests.all()[:10]

    return render(request, 'experts/wallet.html', {
        'wallet': user_wallet,
        'transactions': transactions,
        'withdrawal_requests': withdrawal_requests,
    })


@login_required
def notifications(request):
    notifs = Notification.objects.filter(user=request.user)
    notifs.filter(is_read=False).update(is_read=True)
    
    try:
        wallet = request.user.wallet
    except Wallet.DoesNotExist:
        wallet = None
    
    return render(request, 'experts/notifications.html', {
        'notifications': notifs,
        'wallet': wallet,
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
        profile.cert_expiry = cert_expiry_raw if cert_expiry_raw else None
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

    expert_user = get_object_or_404(CustomUser, pk=expert_pk, role='expert')
    try:
        expert_profile = expert_user.expert_profile
    except ExpertProfile.DoesNotExist:
        expert_profile = None

    analyses = GapAnalysis.objects.filter(
        entrepreneur=request.user,
        status='completed'
    ).order_by('-created_at')

    if request.method == 'POST':
        analysis_id = request.POST.get('analysis_id', '').strip()
        message = request.POST.get('message', '')

        if not analysis_id:
            messages.error(request, 'Tahlilni tanlang!')
            return redirect('expert_detail', expert_pk=expert_pk)

        from analysis.models import GapAnalysis
        analysis = get_object_or_404(GapAnalysis, pk=analysis_id, entrepreneur=request.user)

        # Prevent sending the same analysis to the same expert twice
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
            title='🔔 Yangi tahlil keldi!',
            message=f'{request.user.get_full_name()} ({request.user.company_name}) sizga tahlil yubordi. Narx belgilang.'
        )
        send_project_to_expert(project)

        messages.success(request, 'Tahlil mutaxassisga yuborildi! Narx belgilanishini kuting.')
        return redirect('project_detail', pk=project.pk)

    reviews = Review.objects.filter(expert=expert_user).order_by('-created_at')

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
            title='Yangi baho!',
            message=f'{request.user.get_full_name()} sizga {rating}/5 baho berdi.'
        )

        messages.success(request, 'Rahmat! Bahoyingiz qabul qilindi.')
        return redirect('project_detail', pk=pk)

    return render(request, 'experts/leave_review.html', {'project': project})


# ─── Click To'lov ──────────────────────────────────────────────

def _click_sign(click_trans_id, service_id, secret_key, merchant_trans_id, amount, action, sign_time):
    sign_string = f"{click_trans_id}{service_id}{secret_key}{merchant_trans_id}{amount}{action}{sign_time}"
    return hashlib.md5(sign_string.encode()).hexdigest()


@csrf_exempt
def click_prepare(request):
    if request.method != 'POST':
        return JsonResponse({'error': -8, 'error_note': 'Bad request'})

    data = request.POST
    click_trans_id = data.get('click_trans_id')
    service_id = data.get('service_id')
    merchant_trans_id = data.get('merchant_trans_id')
    amount = data.get('amount')
    action = data.get('action')
    sign_time = data.get('sign_time')
    sign_string = data.get('sign_string')

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

    data = request.POST
    click_trans_id = data.get('click_trans_id')
    service_id = data.get('service_id')
    merchant_trans_id = data.get('merchant_trans_id')
    merchant_prepare_id = data.get('merchant_prepare_id')
    amount = data.get('amount')
    action = data.get('action')
    sign_time = data.get('sign_time')
    sign_string = data.get('sign_string')
    error = int(data.get('error', 0))

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
        if payment.status == 'held':
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
            title='To\'lov amalga oshirildi!',
            message=f'${payment.amount} to\'lov qilindi. Ish boshlashingiz mumkin!'
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
                title='⚠️ Nizo ochildi!',
                message=f'{request.user.get_full_name()} loyiha #{project.pk} bo\'yicha nizo ochdi. Admin ko\'rib chiqadi.',
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