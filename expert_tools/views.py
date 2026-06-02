from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from .models import (
    DocumentTemplate, GeneratedDocument,
    AuditChecklist, AuditChecklistItem,
    ProjectTemplate, ClientCRM, CRMNote,
)
from experts.models import Project
import os
import json
import logging

logger = logging.getLogger('standardbridge')


# ── access guard ─────────────────────────────────────────────────────────────

def expert_required(view_func):
    """Decorator: allows authenticated experts (and admins for support)."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_expert() and not request.user.is_admin():
            return redirect('entrepreneur_dashboard')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


# ── dashboard ─────────────────────────────────────────────────────────────────

@expert_required
def expert_tools_dashboard(request):
    today = timezone.now().date()
    docs_count = GeneratedDocument.objects.filter(expert=request.user).count()
    audits_count = AuditChecklist.objects.filter(expert=request.user).count()
    clients_count = ClientCRM.objects.filter(expert=request.user).count()
    active_clients = ClientCRM.objects.filter(expert=request.user, status='active').count()

    upcoming_followups = ClientCRM.objects.filter(
        expert=request.user,
        next_followup__gte=today,
        next_followup__lte=today + timedelta(days=7),
    ).order_by('next_followup')[:5]

    recent_docs = GeneratedDocument.objects.filter(
        expert=request.user
    ).order_by('-created_at')[:5]

    return render(request, 'expert_tools/dashboard.html', {
        'docs_count': docs_count,
        'audits_count': audits_count,
        'clients_count': clients_count,
        'active_clients': active_clients,
        'upcoming_followups': upcoming_followups,
        'recent_docs': recent_docs,
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
def generate_document(request):
    if request.method != 'POST':
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
        client = Groq(api_key=os.environ.get('GROQ_API_KEY'), timeout=settings.AI_TIMEOUT, max_retries=1)
        prompt = (
            f"Sen ISO standartlari bo'yicha mutaxassisson.\n"
            f"Quyidagi korxona uchun '{template.title}' hujjatini yoz. {lang_instruction}\n\n"
            f"Korxona nomi: {company_name}\n"
            f"Soha: {industry}\n"
            f"Standart: {template.standard}\n\n"
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
        doc.status = request.POST.get('status', doc.status)
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
    if not audit_date_raw:
        messages.error(request, 'Audit sanasini kiriting!')
        return redirect('audit_list')
    audit = AuditChecklist.objects.create(
        expert=request.user,
        project=project,
        company_name=company_name,
        standard=standard,
        audit_date=audit_date_raw,
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
        from experts.models import ProjectUpdate
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
        client.status = request.POST.get('status', client.status)
        client.next_followup = request.POST.get('next_followup') or None
        client.notes = request.POST.get('notes', client.notes or '').strip()
        client.save()
        messages.success(request, 'Mijoz ma\'lumotlari yangilandi.')
    return redirect('crm_detail', pk=pk)


@expert_required
def crm_add_note(request, pk):
    client = get_object_or_404(ClientCRM, pk=pk, expert=request.user)
    if request.method == 'POST':
        note_text = request.POST.get('note', '').strip()
        if note_text:
            CRMNote.objects.create(client=client, author=request.user, note=note_text)
    return redirect('crm_detail', pk=pk)
