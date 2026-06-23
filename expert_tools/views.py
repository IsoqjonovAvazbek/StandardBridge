from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from django_ratelimit.decorators import ratelimit
from functools import wraps
from datetime import timedelta
from .models import (
    DocumentTemplate, GeneratedDocument,
    AuditChecklist, AuditChecklistItem,
    ProjectTemplate, ClientCRM, CRMNote,
    Proposal, TimeLog,
)
from experts.models import Project, Payment, ProjectUpdate
from core.translations import get_translation
import os
import json
import logging
from decimal import Decimal
from datetime import datetime as _dt


def _parse_date(raw):
    if not raw:
        return None
    try:
        return _dt.strptime(raw.strip(), '%Y-%m-%d').date()
    except (ValueError, AttributeError):
        return None


def _safe(text, max_len=300):
    return str(text or '')[:max_len].replace('\n', ' ').replace('\r', ' ')

logger = logging.getLogger('standardbridge')


# ── access guard ─────────────────────────────────────────────────────────────

def expert_required(view_func):
    """Decorator: allows authenticated experts (and admins for support)."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_expert() and not request.user.is_admin():
            return redirect('entrepreneur_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


# ── dashboard ─────────────────────────────────────────────────────────────────

@expert_required
def expert_tools_dashboard(request):
    from django.db.models import Count, Q, Sum as _Sum
    today = timezone.now().date()

    client_stats = ClientCRM.objects.filter(expert=request.user).aggregate(
        total=Count('id'),
        active=Count('id', filter=Q(status='active')),
    )
    clients_count = client_stats['total']
    active_clients = client_stats['active']
    docs_count = GeneratedDocument.objects.filter(expert=request.user).count()
    audits_count = AuditChecklist.objects.filter(expert=request.user).count()
    proposals_count = Proposal.objects.filter(expert=request.user).count()

    # Today's CRM follow-ups
    today_followups = ClientCRM.objects.filter(
        expert=request.user,
        next_followup=today,
    ).order_by('company_name')

    upcoming_followups = ClientCRM.objects.filter(
        expert=request.user,
        next_followup__gt=today,
        next_followup__lte=today + timedelta(days=7),
    ).order_by('next_followup')[:5]

    recent_docs = GeneratedDocument.objects.filter(
        expert=request.user
    ).order_by('-created_at')[:5]

    # This month time logs
    month_start = today.replace(day=1)
    month_hours = TimeLog.objects.filter(
        expert=request.user, date__gte=month_start
    ).aggregate(total=_Sum('hours'))['total'] or Decimal('0')

    # This month released earnings
    month_earnings = Payment.objects.filter(
        project__expert=request.user,
        status='released',
        paid_at__date__gte=month_start,
    ).aggregate(total=_Sum('expert_amount'))['total'] or Decimal('0')

    return render(request, 'expert_tools/dashboard.html', {
        'docs_count': docs_count,
        'audits_count': audits_count,
        'clients_count': clients_count,
        'active_clients': active_clients,
        'proposals_count': proposals_count,
        'today_followups': today_followups,
        'upcoming_followups': upcoming_followups,
        'recent_docs': recent_docs,
        'month_hours': month_hours,
        'month_earnings': month_earnings,
    })


# ── document generator ────────────────────────────────────────────────────────

@expert_required
def document_list(request):
    docs = GeneratedDocument.objects.filter(expert=request.user)
    templates = DocumentTemplate.objects.filter(is_active=True)
    projects = Project.objects.filter(expert=request.user, status='in_progress')
    return render(request, 'expert_tools/documents.html', {
        'documents': docs,
        'templates': templates,
        'projects': projects,
    })


@expert_required
@ratelimit(key='user', rate='5/m', method='POST', block=False)
def generate_document(request):
    if request.method != 'POST':
        return redirect('expert_doc_list')
    if getattr(request, 'limited', False):
        messages.error(request, 'Juda ko\'p so\'rov. Biroz kuting.')
        return redirect('expert_doc_list')

    template_id = request.POST.get('template_id')
    project_id = request.POST.get('project_id', '').strip()
    company_name = request.POST.get('company_name', '').strip()
    industry = request.POST.get('industry', '').strip()
    language = request.POST.get('language', 'uz')

    template = get_object_or_404(DocumentTemplate, pk=template_id)
    project = None
    if project_id:
        project = get_object_or_404(Project, pk=project_id, expert=request.user)
        company_name = project.entrepreneur.company_name or company_name
        industry = project.entrepreneur.industry or industry

    # Fallback defaults so document title/prompt is never empty
    if not company_name:
        company_name = request.user.company_name or 'Korxona nomi ko\'rsatilmagan'
    if not industry:
        industry = request.user.industry or 'Umumiy'

    # Language instruction map
    lang_instruction = {
        'uz': "O'zbek tilida yoz.",
        'ru': "Напиши на русском языке.",
        'en': "Write in English.",
    }.get(language, "O'zbek tilida yoz.")

    # AI generation
    try:
        from groq import Groq
        client = Groq(api_key=settings.GROQ_API_KEY, timeout=settings.AI_TIMEOUT, max_retries=1)
        prompt = (
            f"Sen ISO standartlari bo'yicha mutaxassisson.\n"
            f"Quyidagi korxona uchun '{_safe(template.title, 100)}' hujjatini yoz. {lang_instruction}\n\n"
            f"Korxona nomi: {_safe(company_name)}\n"
            f"Soha: {_safe(industry)}\n"
            f"Standart: {_safe(template.standard, 50)}\n\n"
            f"{template.ai_prompt or template.template_content}\n\n"
            f"Professional, to'liq va tayyor hujjat yoz. Faqat hujjat matnini ber."
        )
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000,
        )
        content = response.choices[0].message.content.strip()
    except Exception as e:
        logger.exception('AI hujjat generatsiya xatosi (template=%s): %s', template_id, e)
        content = template.template_content
        messages.warning(request, 'AI vaqtincha ishlamadi — shablon matni ishlatildi. Keyinroq qayta urinib ko\'ring.')

    doc = GeneratedDocument.objects.create(
        expert=request.user,
        project=project,
        template=template,
        title=f"{template.title} — {company_name}",
        content=content,
    )
    return redirect('expert_doc_detail', pk=doc.pk)


@expert_required
def document_detail(request, pk):
    doc = get_object_or_404(GeneratedDocument, pk=pk, expert=request.user)
    return render(request, 'expert_tools/document_detail.html', {'doc': doc})


@expert_required
def edit_document(request, pk):
    doc = get_object_or_404(GeneratedDocument, pk=pk, expert=request.user)
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if not content:
            messages.error(request, 'Hujjat matni bo\'sh bo\'lishi mumkin emas!')
            return render(request, 'expert_tools/edit_document.html', {'doc': doc})
        doc.content = content
        new_doc_status = request.POST.get('status', doc.status)
        if new_doc_status in {c[0] for c in GeneratedDocument.STATUS_CHOICES}:
            doc.status = new_doc_status
        doc.save()
        messages.success(request, 'Hujjat saqlandi.')
        return redirect('expert_doc_detail', pk=pk)
    return render(request, 'expert_tools/edit_document.html', {'doc': doc})


@expert_required
def delete_document(request, pk):
    doc = get_object_or_404(GeneratedDocument, pk=pk, expert=request.user)
    if request.method == 'POST':
        doc.delete()
    return redirect('expert_doc_list')


# ── audit checklist ───────────────────────────────────────────────────────────

ISO9001_QUESTIONS = [
    ("4.1", "Tashkilot konteksti va manfaatdor tomonlar aniqlangan"),
    ("4.3", "QMS doirasi hujjatlashtirilgan"),
    ("5.1", "Rahbariyat sifatga sodiqligini ko'rsatmoqda"),
    ("5.2", "Sifat siyosati mavjud va xodimlarga ma'lum"),
    ("5.3", "Mas'uliyat va vakolatlar belgilangan"),
    ("6.1", "Risklarni boshqarish jarayoni mavjud"),
    ("6.2", "Sifat maqsadlari o'lchanadigan"),
    ("7.1", "Resurslar (odam, infratuzilma) ta'minlangan"),
    ("7.2", "Xodimlar malakasi tasdiqlangan"),
    ("7.3", "Xodimlar sifat siyosatidan xabardor"),
    ("7.4", "Kommunikatsiya jarayoni belgilangan"),
    ("7.5", "Hujjatlar boshqaruvi mavjud"),
    ("8.2", "Mijoz talablari aniqlangan"),
    ("8.4", "Ta'minotchilar nazorat qilinadi"),
    ("8.5", "Ishlab chiqarish jarayoni nazorat ostida"),
    ("8.6", "Tayyor mahsulot nazorati mavjud"),
    ("8.7", "Nomuvofiq mahsulotlar boshqaruvi bor"),
    ("9.1", "Mijoz qoniqishi o'lchanadi"),
    ("9.2", "Ichki auditlar o'tkaziladi"),
    ("9.3", "Menejment sharhi o'tkaziladi"),
    ("10.2", "Nomuvofiqliklar va tuzatuvchi choralar kuzatiladi"),
    ("10.3", "Doimiy yaxshilash dalillari mavjud"),
]

ISO22000_QUESTIONS = [
    ("4.1", "Tashkilot va uning konteksti aniqlangan"),
    ("5.1", "Oziq-ovqat xavfsizligi siyosati belgilangan"),
    ("6.1", "FSMS xavflari baholangan"),
    ("7.1.2", "Insoniy resurslar va malaka ta'minlangan"),
    ("7.4", "Kommunikatsiya (ichki/tashqi) jarayoni bor"),
    ("8.1", "Ishlab chiqarish rejalashtirilgan va nazorat ostida"),
    ("8.2", "PRPs (dastlabki shartli dasturlar) joriy qilingan"),
    ("8.3", "Kuzatuv tizimi va validatsiya bor"),
    ("8.4", "Xavf tahlili o'tkazilgan"),
    ("8.5", "HACCP rejasi mavjud va joriy qilingan"),
    ("8.8", "Tekshirish rejasi bajarilmoqda"),
    ("9.1", "Monitoring va o'lchash natijalari tahlil qilinadi"),
    ("9.3", "Menejment sharhi o'tkaziladi"),
    ("10.2", "Nomuvofiqliklar va tuzatuvchi choralar kuzatiladi"),
]

ISO14001_QUESTIONS = [
    ("4.1", "Tashkilot konteksti va atrof-muhit jihatlari aniqlangan"),
    ("5.1", "Rahbariyat EMS ga majburiyat olgan"),
    ("5.2", "Atrof-muhit siyosati belgilangan va tarqatilgan"),
    ("6.1.1", "Atrof-muhit jihatlari va ta'sirlari baholangan"),
    ("6.1.3", "Qonuniy talablar aniqlangan va kuzatiladi"),
    ("6.2", "Atrof-muhit maqsadlari o'lchanadigan"),
    ("7.2", "Xodimlar atrof-muhit bo'yicha o'qitilgan"),
    ("8.1", "Muhim jihatlar operatsion nazorat ostida"),
    ("8.2", "Favqulodda vaziyatlar rejasi bor"),
    ("9.1", "Monitoring va o'lchash amalga oshiriladi"),
    ("9.2", "Ichki auditlar o'tkaziladi"),
    ("10.2", "Nomuvofiqliklar va tuzatuvchi choralar kuzatiladi"),
]

ISO45001_QUESTIONS = [
    ("4.1", "Tashkilot konteksti va OH&S risklari aniqlangan"),
    ("5.1", "Rahbariyat xavfsizlik va sog'liqni saqlashga majburiyat olgan"),
    ("5.2", "OH&S siyosati belgilangan"),
    ("5.4", "Ishchilar ishtiroki ta'minlangan"),
    ("6.1.1", "Xavflar va OH&S risklari baholangan"),
    ("6.2", "OH&S maqsadlari belgilangan"),
    ("7.2", "Xodimlar malakasi tasdiqlangan"),
    ("8.1.1", "Xavfli jarayonlar operatsion nazorat ostida"),
    ("8.2", "Favqulodda tayyorgarlik va javob berish rejasi bor"),
    ("9.1.1", "Ishchi unumdorligi va sog'liq ko'rsatkichlari kuzatiladi"),
    ("9.2", "Ichki auditlar o'tkaziladi"),
    ("10.2", "Hodisalar, nomuvofiqliklar va tuzatuvchi choralar kuzatiladi"),
]

STANDARD_QUESTIONS_MAP = {
    'iso9001': ISO9001_QUESTIONS,
    'iso22000': ISO22000_QUESTIONS,
    'iso14001': ISO14001_QUESTIONS,
    'iso45001': ISO45001_QUESTIONS,
}


@expert_required
def audit_list(request):
    audits = AuditChecklist.objects.filter(expert=request.user)
    projects = Project.objects.filter(expert=request.user, status='in_progress')
    return render(request, 'expert_tools/audit_list.html', {
        'audits': audits,
        'projects': projects,
    })


@expert_required
def new_audit(request):
    if request.method != 'POST':
        return redirect('audit_list')

    project_id = request.POST.get('project_id', '').strip()
    company_name = request.POST.get('company_name', '').strip()
    project = None

    if project_id:
        project = get_object_or_404(Project, pk=project_id, expert=request.user)
        company_name = project.entrepreneur.company_name or company_name

    standard = request.POST.get('standard', 'iso9001')
    audit_date_raw = request.POST.get('audit_date', '').strip()
    parsed_audit_date = _parse_date(audit_date_raw)
    if not parsed_audit_date:
        messages.error(request, 'To\'g\'ri audit sanasini kiriting!')
        return redirect('audit_list')
    audit = AuditChecklist.objects.create(
        expert=request.user,
        project=project,
        company_name=company_name,
        standard=standard,
        audit_date=parsed_audit_date,
        notes=request.POST.get('notes', ''),
    )

    # Seed questions based on chosen standard
    questions = STANDARD_QUESTIONS_MAP.get(standard, ISO9001_QUESTIONS)
    for i, (clause, question) in enumerate(questions, start=1):
        AuditChecklistItem.objects.create(
            checklist=audit, clause=clause, question=question, order=i,
        )

    return redirect('audit_detail', pk=audit.pk)


@expert_required
def audit_detail(request, pk):
    audit = get_object_or_404(AuditChecklist, pk=pk, expert=request.user)
    items = audit.items.all()
    total = items.count()
    compliant = items.filter(status='compliant').count()
    score = int(compliant / total * 100) if total > 0 else 0
    return render(request, 'expert_tools/audit_detail.html', {
        'audit': audit,
        'items': items,
        'score': score,
        'compliant': compliant,
        'total': total,
    })


@expert_required
def update_audit_item(request, pk):
    audit = get_object_or_404(AuditChecklist, pk=pk, expert=request.user)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'success': False}, status=400)

        item_id = data.get('item_id')
        if not item_id:
            return JsonResponse({'success': False, 'error': 'item_id missing'}, status=400)
        item = get_object_or_404(AuditChecklistItem, pk=item_id, checklist=audit)
        item.status = data.get('status', item.status)
        item.evidence = data.get('evidence', '').strip()
        item.finding = data.get('finding', '').strip()
        item.save()

        # Recalculate score
        total = audit.items.count()
        compliant = audit.items.filter(status='compliant').count()
        score = int(compliant / total * 100) if total else 0
        audit.overall_score = score
        audit.save(update_fields=['overall_score'])

        return JsonResponse({
            'success': True, 'score': score,
            'compliant': compliant, 'total': total,
        })
    return JsonResponse({'success': False}, status=405)


@expert_required
def audit_mobile(request, pk):
    audit = get_object_or_404(AuditChecklist, pk=pk, expert=request.user)
    items = list(audit.items.order_by('order', 'pk'))
    total = len(items)
    compliant = sum(1 for i in items if i.status == 'compliant')
    score = int(compliant / total * 100) if total > 0 else 0
    # index of first unchecked item for auto-scroll
    first_unchecked = next((i for i, item in enumerate(items) if item.status == 'not_checked'), 0)
    return render(request, 'expert_tools/audit_mobile.html', {
        'audit': audit,
        'items': items,
        'score': score,
        'compliant': compliant,
        'total': total,
        'first_unchecked': first_unchecked,
    })


@expert_required
def complete_audit(request, pk):
    audit = get_object_or_404(AuditChecklist, pk=pk, expert=request.user)
    if request.method == 'POST':
        audit.is_completed = True
        audit.save(update_fields=['is_completed'])
    return redirect('audit_detail', pk=pk)


@expert_required
def audit_from_analysis(request, project_id):
    """Build a professional AuditChecklist from the client's self-assessment (gap analysis).

    Links the entrepreneur analysis module to the expert audit tool: each AI-found
    gap becomes a checklist item the expert then verifies on-site with evidence.
    """
    if request.method != 'POST':
        return redirect('audit_list')

    project = get_object_or_404(Project, pk=project_id, expert=request.user)
    analysis = project.analysis
    if analysis is None or not analysis.gaps.exists():
        messages.error(request, "Bu loyihada tahlil natijasi yoki kamchiliklar topilmadi.")
        return redirect('audit_list')

    # Map analysis target standard code (e.g. "ISO 9001") to checklist standard key
    std_map = {'9001': 'iso9001', '22000': 'iso22000', '14001': 'iso14001', '45001': 'iso45001'}
    std_code = (analysis.target_standard.code if analysis.target_standard else '') or ''
    standard = next((v for k, v in std_map.items() if k in std_code), 'iso9001')

    audit = AuditChecklist.objects.create(
        expert=request.user,
        project=project,
        company_name=project.entrepreneur.company_name or analysis.entrepreneur.company_name,
        standard=standard,
        audit_date=timezone.now().date(),
        notes=f"Mijoz tahlili (#{analysis.pk}) asosida avtomatik yaratildi.",
    )

    # Each gap → a checklist item pre-flagged as non_compliant with the gap as finding.
    # The expert then confirms/updates status with real on-site evidence.
    priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    gaps = sorted(analysis.gaps.all(), key=lambda g: priority_order.get(g.priority, 4))
    for i, gap in enumerate(gaps, start=1):
        AuditChecklistItem.objects.create(
            checklist=audit,
            clause='',
            question=gap.title,
            status='non_compliant',
            finding=gap.description,
            order=i,
        )

    messages.success(request, f"{len(gaps)} ta band mijoz tahlilidan ko'chirildi. Endi joyida tekshirib, dalil qo'shing.")
    return redirect('audit_detail', pk=audit.pk)


# ── project templates ─────────────────────────────────────────────────────────

@expert_required
def project_templates(request):
    templates = ProjectTemplate.objects.filter(is_active=True)
    projects = Project.objects.filter(expert=request.user, status='in_progress')
    return render(request, 'expert_tools/project_templates.html', {
        'templates': templates,
        'projects': projects,
    })


@expert_required
def apply_template(request, pk, project_pk):
    template = get_object_or_404(ProjectTemplate, pk=pk, is_active=True)
    project = get_object_or_404(Project, pk=project_pk, expert=request.user)

    if request.method == 'POST':
        steps_text = "\n".join(
            f"{s.order}. {s.title} ({s.duration_days} kun)"
            + (f" — {s.deliverable}" if s.deliverable else "")
            for s in template.steps.all()
        )
        ProjectUpdate.objects.create(
            project=project,
            author=request.user,
            message=f"Loyiha rejasi ({template.title}):\n\n{steps_text}",
            update_type='progress',
        )
        messages.success(request, f"'{template.title}' shabloni muvaffaqiyatli qo'llandi.")
        return redirect('project_detail', pk=project_pk)

    return render(request, 'expert_tools/apply_template.html', {
        'template': template,
        'project': project,
    })


# ── CRM ───────────────────────────────────────────────────────────────────────

@expert_required
def crm_list(request):
    clients = ClientCRM.objects.filter(expert=request.user)
    status_filter = request.GET.get('status', '')
    if status_filter:
        clients = clients.filter(status=status_filter)

    total = ClientCRM.objects.filter(expert=request.user).count()
    stats = {
        'total': total,
        'lead': ClientCRM.objects.filter(expert=request.user, status='lead').count(),
        'active': ClientCRM.objects.filter(expert=request.user, status='active').count(),
        'completed': ClientCRM.objects.filter(expert=request.user, status='completed').count(),
    }
    return render(request, 'expert_tools/crm_list.html', {
        'clients': clients,
        'status_filter': status_filter,
        'stats': stats,
    })


@expert_required
def crm_add(request):
    if request.method == 'POST':
        company_name = request.POST.get('company_name', '').strip()
        contact_person = request.POST.get('contact_person', '').strip()
        if company_name and contact_person:
            ClientCRM.objects.create(
                expert=request.user,
                company_name=company_name,
                contact_person=contact_person,
                phone=request.POST.get('phone', '').strip(),
                email=request.POST.get('email', '').strip(),
                industry=request.POST.get('industry', '').strip(),
                target_standard=request.POST.get('target_standard', '').strip(),
                status=request.POST.get('status', 'lead'),
                next_followup=request.POST.get('next_followup') or None,
                notes=request.POST.get('notes', '').strip(),
            )
            messages.success(request, 'Mijoz muvaffaqiyatli qo\'shildi!')
        else:
            messages.error(request, 'Korxona nomi va kontakt shaxsni kiriting!')
    return redirect('crm_list')


@expert_required
def crm_detail(request, pk):
    client = get_object_or_404(ClientCRM, pk=pk, expert=request.user)
    notes = client.crm_notes.all()
    return render(request, 'expert_tools/crm_detail.html', {
        'client': client,
        'notes': notes,
    })


@expert_required
def crm_update(request, pk):
    client = get_object_or_404(ClientCRM, pk=pk, expert=request.user)
    if request.method == 'POST':
        new_status = request.POST.get('status', client.status)
        if new_status in {c[0] for c in ClientCRM.STATUS_CHOICES}:
            client.status = new_status
        client.next_followup = request.POST.get('next_followup') or None
        client.notes = request.POST.get('notes', client.notes or '').strip()
        client.save()
        messages.success(request, 'Mijoz ma\'lumotlari yangilandi.')
    return redirect('crm_detail', pk=pk)


@expert_required
def crm_delete(request, pk):
    client = get_object_or_404(ClientCRM, pk=pk, expert=request.user)
    if request.method == 'POST':
        client.delete()
        messages.success(request, 'Mijoz CRM\'dan o\'chirildi.')
        return redirect('crm_list')
    return redirect('crm_detail', pk=pk)


@expert_required
def crm_add_note(request, pk):
    client = get_object_or_404(ClientCRM, pk=pk, expert=request.user)
    if request.method == 'POST':
        note_text = request.POST.get('note', '').strip()
        if note_text:
            CRMNote.objects.create(client=client, author=request.user, note=note_text)
    return redirect('crm_detail', pk=pk)


# ── Proposal Generator ────────────────────────────────────────────────────────

@expert_required
def proposal_list(request):
    proposals = Proposal.objects.filter(expert=request.user)
    status_filter = request.GET.get('status', '')
    if status_filter:
        proposals = proposals.filter(status=status_filter)
    projects = Project.objects.filter(expert=request.user).exclude(status='completed')
    return render(request, 'expert_tools/proposal_list.html', {
        'proposals': proposals,
        'status_filter': status_filter,
        'projects': projects,
    })


@expert_required
@ratelimit(key='user', rate='5/m', method='POST', block=False)
def create_proposal(request):
    if request.method != 'POST':
        return redirect('proposal_list')
    if getattr(request, 'limited', False):
        messages.error(request, 'Juda ko\'p so\'rov. Biroz kuting.')
        return redirect('proposal_list')

    company_name = request.POST.get('company_name', '').strip()
    contact_person = request.POST.get('contact_person', '').strip()
    standard = request.POST.get('standard', '').strip()
    industry = request.POST.get('industry', '').strip()
    scope = request.POST.get('scope', '').strip()
    project_id = request.POST.get('project_id', '').strip()
    lang = request.session.get('lang', 'uz')

    if not company_name or not standard:
        messages.error(request, 'Korxona nomi va standartni kiriting!')
        return redirect('proposal_list')

    project = None
    if project_id:
        try:
            project = Project.objects.get(pk=project_id, expert=request.user)
            company_name = project.entrepreneur.company_name or company_name
            industry = project.entrepreneur.industry or industry
        except Project.DoesNotExist:
            pass

    try:
        price_min = Decimal(str(request.POST.get('price_min', '0') or '0'))
        price_max = Decimal(str(request.POST.get('price_max', '0') or '0'))
        duration_days = int(request.POST.get('duration_days', 90) or 90)
    except (ValueError, Exception):
        price_min, price_max, duration_days = Decimal('0'), Decimal('0'), 90

    lang_map = {
        'uz': "O'zbek tilida yoz.",
        'ru': "Напиши на русском языке.",
        'en': "Write in English.",
    }
    expert_name = _safe(request.user.get_full_name() or request.user.username, 100)
    expert_company = _safe(request.user.company_name or 'StandardBridge orqali', 100)

    prompt = (
        f"Sen ISO sertifikatsiya bo'yicha tajribali konsultantsan. {lang_map.get(lang, lang_map['uz'])}\n\n"
        f"Quyidagi mijoz uchun professional taklifnoma (commercial proposal) tayyorla:\n\n"
        f"Mijoz korxona: {_safe(company_name, 150)}\n"
        f"Soha: {_safe(industry, 100) or 'Ko\'rsatilmagan'}\n"
        f"Maqsad standart: {_safe(standard, 50)}\n"
        f"Loyiha qamrovi: {_safe(scope, 300) or 'Standart bo\'yicha to\'liq sertifikatsiyaga tayyorlash'}\n"
        f"Narx oralig'i: ${price_min} – ${price_max}\n"
        f"Taxminiy muddat: {duration_days} kun\n"
        f"Konsultant: {expert_name} ({expert_company})\n\n"
        "Taklifnomada bo'lsin:\n"
        "1. Kirish (mijoz muammosi va bizning yechim)\n"
        "2. Xizmat qamrovi (nima qilamiz, nima qilmaymiz)\n"
        "3. Ish bosqichlari (3-5 ta aniq bosqich)\n"
        "4. Narx va to'lov shartlari\n"
        "5. Nima uchun biz? (ustunliklarimiz)\n"
        "6. Keyingi qadam\n\n"
        "Professional, qisqa va mijozni ishontiruvchi tarzda yoz. Markdown formatida."
    )

    content = ''
    try:
        from groq import Groq
        client_ai = Groq(api_key=settings.GROQ_API_KEY, timeout=settings.AI_TIMEOUT, max_retries=1)
        resp = client_ai.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=2000,
        )
        content = resp.choices[0].message.content.strip()
    except Exception as e:
        logger.exception('Proposal AI xatosi: %s', e)
        content = f"# {company_name} uchun {standard} Taklifnoma\n\n*AI hozir ishlamadi. Qo'lda to'ldiring.*"
        messages.warning(request, 'AI vaqtincha ishlamadi. Taklifnomani qo\'lda to\'ldiring.')

    from datetime import date as _date, timedelta as _td
    try:
        validity_days = max(7, min(365, int(request.POST.get('validity_days', 30) or 30)))
    except (ValueError, TypeError):
        validity_days = 30
    valid_until = _date.today() + _td(days=validity_days)

    proposal = Proposal.objects.create(
        expert=request.user,
        project=project,
        company_name=company_name[:300],
        contact_person=contact_person[:200],
        standard=standard[:50],
        industry=industry[:100],
        scope=scope,
        price_min=price_min,
        price_max=price_max,
        duration_days=duration_days,
        content=content,
        valid_until=valid_until,
    )
    messages.success(request, 'Taklifnoma yaratildi.')
    return redirect('proposal_detail', pk=proposal.pk)


@expert_required
def proposal_detail(request, pk):
    proposal = get_object_or_404(Proposal, pk=pk, expert=request.user)
    return render(request, 'expert_tools/proposal_detail.html', {'proposal': proposal})


@expert_required
def proposal_print(request, pk):
    proposal = get_object_or_404(Proposal, pk=pk, expert=request.user)
    T = get_translation(request.session.get('lang', 'uz'))
    return render(request, 'expert_tools/proposal_print.html', {
        'proposal': proposal,
        'today': timezone.now().date(),
        'expert': request.user,
        'T': T,
    })


@expert_required
def edit_proposal(request, pk):
    proposal = get_object_or_404(Proposal, pk=pk, expert=request.user)
    if request.method == 'POST':
        proposal.content = request.POST.get('content', proposal.content)
        proposal.status = request.POST.get('status', proposal.status)
        try:
            proposal.price_min = Decimal(str(request.POST.get('price_min', proposal.price_min) or proposal.price_min))
            proposal.price_max = Decimal(str(request.POST.get('price_max', proposal.price_max) or proposal.price_max))
            proposal.duration_days = int(request.POST.get('duration_days', proposal.duration_days) or proposal.duration_days)
        except (ValueError, Exception):
            pass
        proposal.save()
        messages.success(request, 'Taklifnoma saqlandi.')
        return redirect('proposal_detail', pk=pk)
    return render(request, 'expert_tools/edit_proposal.html', {'proposal': proposal})


@expert_required
def delete_proposal(request, pk):
    proposal = get_object_or_404(Proposal, pk=pk, expert=request.user)
    if request.method == 'POST':
        proposal.delete()
        messages.success(request, 'Taklifnoma o\'chirildi.')
    return redirect('proposal_list')


# ── Time Tracker ──────────────────────────────────────────────────────────────

@expert_required
def time_logs(request):
    today = timezone.now().date()
    logs = TimeLog.objects.filter(expert=request.user).select_related('project')
    projects = Project.objects.filter(expert=request.user).exclude(status='completed')

    # Per-project totals
    project_totals = {}
    for log in logs:
        pid = log.project_id
        project_totals[pid] = project_totals.get(pid, Decimal('0')) + log.hours

    # This month totals
    month_start = today.replace(day=1)
    month_logs = logs.filter(date__gte=month_start)
    month_total = sum((l.hours for l in month_logs), Decimal('0'))

    # Recent 20 entries
    recent_logs = logs[:20]

    return render(request, 'expert_tools/time_logs.html', {
        'recent_logs': recent_logs,
        'projects': projects,
        'project_totals': project_totals,
        'month_total': month_total,
        'today': today,
    })


@expert_required
def add_time_log(request):
    if request.method != 'POST':
        return redirect('time_logs')
    project_id = request.POST.get('project_id', '').strip()
    date_raw = request.POST.get('date', '').strip()
    description = request.POST.get('description', '').strip()

    try:
        hours = Decimal(str(request.POST.get('hours', '1') or '1'))
        hours = max(Decimal('0.5'), min(Decimal('24'), hours))
    except Exception:
        hours = Decimal('1')

    parsed_date = _parse_date(date_raw)
    if not project_id or not parsed_date:
        messages.error(request, 'Loyiha va to\'g\'ri sanani tanlang!')
        return redirect('time_logs')

    project = get_object_or_404(Project, pk=project_id, expert=request.user)
    TimeLog.objects.create(
        expert=request.user,
        project=project,
        date=parsed_date,
        hours=hours,
        description=description[:300],
    )
    messages.success(request, f'{hours} soat yozildi.')
    return redirect('time_logs')


@expert_required
def delete_time_log(request, pk):
    log = get_object_or_404(TimeLog, pk=pk, expert=request.user)
    if request.method == 'POST':
        log.delete()
        messages.success(request, 'Yozuv o\'chirildi.')
    return redirect('time_logs')


# ── Earnings Dashboard ────────────────────────────────────────────────────────

@expert_required
def earnings_dashboard(request):
    from django.db.models import Sum
    today = timezone.now().date()

    payments = Payment.objects.filter(
        project__expert=request.user,
        status='released',
    ).select_related('project__entrepreneur')

    # Total earnings
    total_earned = sum(p.expert_amount for p in payments if p.expert_amount) or Decimal('0')

    # This month
    month_start = today.replace(day=1)
    month_payments = [p for p in payments if p.paid_at and p.paid_at.date() >= month_start]
    month_earned = sum(p.expert_amount for p in month_payments if p.expert_amount) or Decimal('0')

    # Last 6 months chart data — use local time to avoid UTC month-boundary shift
    _ET_MONTHS = ['Yan', 'Fev', 'Mar', 'Apr', 'May', 'Iyn', 'Iyl', 'Avg', 'Sen', 'Okt', 'Noy', 'Dek']
    chart_labels = []
    chart_data = []
    for i in range(5, -1, -1):
        if today.month - i <= 0:
            m = today.month - i + 12
            y = today.year - 1
        else:
            m = today.month - i
            y = today.year
        month_ps = []
        for p in payments:
            if p.paid_at:
                local_dt = timezone.localtime(p.paid_at) if timezone.is_aware(p.paid_at) else p.paid_at
                if local_dt.year == y and local_dt.month == m:
                    month_ps.append(p)
        amount = float(sum(p.expert_amount for p in month_ps if p.expert_amount) or 0)
        chart_labels.append(_ET_MONTHS[m - 1] + ' ' + str(y))
        chart_data.append(amount)

    # Per-project breakdown
    project_breakdown = {}
    for p in payments:
        pid = p.project_id
        name = p.project.entrepreneur.company_name or f'Loyiha #{pid}'
        if pid not in project_breakdown:
            project_breakdown[pid] = {'name': name, 'amount': Decimal('0'), 'count': 0}
        project_breakdown[pid]['amount'] += p.expert_amount or Decimal('0')
        project_breakdown[pid]['count'] += 1
    project_breakdown = sorted(project_breakdown.values(), key=lambda x: x['amount'], reverse=True)[:10]

    # Time stats this month
    month_hours = sum(
        t.hours for t in TimeLog.objects.filter(expert=request.user, date__gte=month_start)
    ) or Decimal('0')

    return render(request, 'expert_tools/earnings.html', {
        'total_earned': total_earned,
        'month_earned': month_earned,
        'month_hours': month_hours,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'project_breakdown': project_breakdown,
        'payments': payments[:20],
        'today': today,
    })


# ── Audit Print ───────────────────────────────────────────────────────────────

@expert_required
def audit_print(request, pk):
    audit = get_object_or_404(AuditChecklist, pk=pk, expert=request.user)
    items = audit.items.all()
    total = items.count()
    compliant = items.filter(status='compliant').count()
    partial = items.filter(status='partial').count()
    non_compliant = items.filter(status='non_compliant').count()
    score = int(compliant / total * 100) if total else 0
    findings = items.exclude(finding='').order_by('order')
    T = get_translation(request.session.get('lang', 'uz'))
    return render(request, 'expert_tools/audit_print.html', {
        'audit': audit,
        'items': items,
        'total': total,
        'compliant': compliant,
        'partial': partial,
        'non_compliant': non_compliant,
        'score': score,
        'findings': findings,
        'today': timezone.now().date(),
        'expert': request.user,
        'T': T,
    })
