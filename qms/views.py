from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.conf import settings
from django.db.models import Count, F, ExpressionWrapper, IntegerField
from datetime import timedelta
from django_ratelimit.decorators import ratelimit
from .models import ChecklistItem, ChecklistResponse, QMSDocument, QMSDocumentVersion, NonConformity, AuditSchedule, RiskItem, TrainingRecord
from core.translations import notif_text as _nl
import json
import csv
import os
import logging

logger = logging.getLogger('standardbridge')


def _parse_date(raw):
    """Return a date object if raw is a valid YYYY-MM-DD string, else None."""
    if not raw:
        return None
    try:
        from datetime import datetime
        return datetime.strptime(raw.strip(), '%Y-%m-%d').date()
    except (ValueError, AttributeError):
        return None


def _entrepreneur_required(view_func):
    from functools import wraps
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.conf import settings
            return redirect(settings.LOGIN_URL)
        if not request.user.is_entrepreneur():
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped


@_entrepreneur_required
def qms_dashboard(request):
    user = request.user

    # Checklist statistics
    total_items = ChecklistItem.objects.filter(is_active=True).count()
    responses = ChecklistResponse.objects.filter(company=user)
    compliant = responses.filter(status='compliant').count()
    partial = responses.filter(status='partial').count()
    non_compliant = responses.filter(status='non_compliant').count()
    checked = compliant + partial + non_compliant
    completion_pct = int(checked / total_items * 100) if total_items > 0 else 0
    compliance_pct = int(compliant / total_items * 100) if total_items > 0 else 0

    # Non-conformities
    open_nc = NonConformity.objects.filter(company=user, status='open').count()
    critical_nc = NonConformity.objects.filter(company=user, status='open', severity='critical').count()

    # Documents
    today = timezone.now().date()
    total_docs = QMSDocument.objects.filter(company=user, is_active=True).count()
    expiring_docs = QMSDocument.objects.filter(
        company=user,
        is_active=True,
        expiry_date__lte=today + timedelta(days=30),
        expiry_date__gte=today,
    ).count()

    # Next audit
    next_audit = AuditSchedule.objects.filter(
        company=user,
        status='planned',
        planned_date__gte=today,
    ).order_by('planned_date').first()

    # Recent non-conformities (last 5)
    recent_ncs = NonConformity.objects.filter(company=user).order_by('-created_at')[:5]

    # Recent documents (last 5)
    recent_docs = QMSDocument.objects.filter(company=user, is_active=True).order_by('-uploaded_at')[:5]

    # Risk register stats
    total_risks = RiskItem.objects.filter(company=user).count()
    open_risks = RiskItem.objects.filter(company=user, status='open').count()
    critical_risks = RiskItem.objects.annotate(
        rs=ExpressionWrapper(F('likelihood') * F('impact'), output_field=IntegerField())
    ).filter(company=user, status='open', rs__gte=15).count()

    # Training records stats
    total_trainings = TrainingRecord.objects.filter(company=user).count()
    expiring_trainings = TrainingRecord.objects.filter(
        company=user,
        expiry_date__lte=today + timedelta(days=30),
        expiry_date__gte=today,
    ).count()

    # QMS Health Score (weighted)
    # 1. Checklist compliance 40%
    checklist_score = compliance_pct * 0.4

    # 2. NC resolution rate 30% — data yo'q bo'lsa 0 (hali kuzatish boshlanmagan)
    total_nc = NonConformity.objects.filter(company=user).count()
    closed_nc = NonConformity.objects.filter(company=user, status='closed').count()
    nc_score = (int(closed_nc / total_nc * 100) if total_nc > 0 else 0) * 0.3

    # 3. Document validity 20% — hujjat yuklanmagan bo'lsa 0
    expired_docs = QMSDocument.objects.filter(
        company=user, is_active=True, expiry_date__lt=today
    ).count()
    doc_valid_pct = int((total_docs - expired_docs) / total_docs * 100) if total_docs > 0 else 0
    doc_score = doc_valid_pct * 0.2

    # 4. Audit on schedule 10% — audit rejalashtirilmagan bo'lsa 0
    total_audits = AuditSchedule.objects.filter(company=user).count()
    overdue_audits = AuditSchedule.objects.filter(
        company=user,
        status__in=('planned', 'in_progress'),
        planned_date__lt=today,
    ).count()
    audit_pct = int((total_audits - overdue_audits) / total_audits * 100) if total_audits > 0 else 0
    audit_score = audit_pct * 0.1

    health_score = int(checklist_score + nc_score + doc_score + audit_score)
    # Yangi foydalanuvchi: hech qanday ma'lumot kiritilmagan
    no_qms_data = (checked == 0 and total_nc == 0 and total_docs == 0 and total_audits == 0)

    return render(request, 'qms/dashboard.html', {
        'completion_pct': completion_pct,
        'compliance_pct': compliance_pct,
        'total_items': total_items,
        'checked': checked,
        'compliant': compliant,
        'partial': partial,
        'non_compliant': non_compliant,
        'open_nc': open_nc,
        'critical_nc': critical_nc,
        'total_docs': total_docs,
        'expiring_docs': expiring_docs,
        'next_audit': next_audit,
        'recent_ncs': recent_ncs,
        'recent_docs': recent_docs,
        'total_risks': total_risks,
        'open_risks': open_risks,
        'critical_risks': critical_risks,
        'total_trainings': total_trainings,
        'expiring_trainings': expiring_trainings,
        'health_score': health_score,
        'no_qms_data': no_qms_data,
        'expired_docs': expired_docs,
    })


STANDARD_LABELS = {
    'iso9001': 'ISO 9001',
    'iso22000': 'ISO 22000',
    'iso14001': 'ISO 14001',
    'iso45001': 'ISO 45001',
}


_VALID_STANDARDS = {'iso9001', 'iso14001', 'iso45001', 'iso22000'}


@_entrepreneur_required
def qms_checklist(request):
    standard = request.GET.get('standard', 'iso9001')
    if standard not in _VALID_STANDARDS:
        standard = 'iso9001'
    items = ChecklistItem.objects.filter(standard=standard, is_active=True)

    # Build a dict of existing responses keyed by item pk
    responses = {r.item_id: r for r in ChecklistResponse.objects.filter(company=request.user)}

    items_with_response = [
        {'item': item, 'response': responses.get(item.pk)}
        for item in items
    ]

    # Build a structured list of standards with per-standard stats.
    # Django templates cannot do dict[variable] access, so we embed
    # all data into a list of plain dicts that the template iterates over.
    # Aggregate in 2 queries instead of 2×N
    item_totals = {
        row['standard']: row['cnt']
        for row in ChecklistItem.objects.filter(is_active=True)
        .values('standard').annotate(cnt=Count('id'))
    }
    compliant_totals = {
        row['item__standard']: row['cnt']
        for row in ChecklistResponse.objects.filter(
            company=request.user, status='compliant'
        ).values('item__standard').annotate(cnt=Count('id'))
    }

    standards = []
    for code in sorted(item_totals.keys()):
        total = item_totals[code]
        compliant = compliant_totals.get(code, 0)
        standards.append({
            'code': code,
            'label': STANDARD_LABELS.get(code, code.upper()),
            'total': total,
            'compliant': compliant,
            'pct': int(compliant / total * 100) if total else 0,
        })

    return render(request, 'qms/checklist.html', {
        'items_with_response': items_with_response,
        'current_standard': standard,
        'standards': standards,
    })


@_entrepreneur_required
def update_checklist(request):
    """AJAX endpoint — saves a single checklist item response."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'success': False, 'error': 'invalid json'}, status=400)

        try:
            item_id = int(data.get('item_id'))
        except (TypeError, ValueError):
            return JsonResponse({'success': False, 'error': 'bad params'}, status=400)
        status = data.get('status')
        note = data.get('note', '')

        if not item_id or status not in ('compliant', 'partial', 'non_compliant', 'not_checked'):
            return JsonResponse({'success': False, 'error': 'bad params'}, status=400)

        evidence = data.get('evidence', '')
        item = get_object_or_404(ChecklistItem, pk=item_id)
        response, created = ChecklistResponse.objects.get_or_create(
            company=request.user,
            item=item,
            defaults={'status': status, 'note': note, 'evidence_text': evidence},
        )
        if not created:
            response.status = status
            response.note = note
            response.evidence_text = evidence
            response.save()

        # Shu standart bo'yicha foizni qayta hisoblaymiz (real-time progress uchun)
        std_code = item.standard
        total = ChecklistItem.objects.filter(standard=std_code, is_active=True).count()
        compliant = ChecklistResponse.objects.filter(
            company=request.user, item__standard=std_code, status='compliant'
        ).count()
        checked = ChecklistResponse.objects.filter(
            company=request.user, item__standard=std_code,
        ).exclude(status='not_checked').count()
        pct = int(compliant / total * 100) if total else 0

        return JsonResponse({
            'success': True,
            'standard': std_code,
            'pct': pct,
            'compliant': compliant,
            'checked': checked,
            'total': total,
        })
    return JsonResponse({'success': False}, status=405)


@_entrepreneur_required
def qms_documents(request):
    docs = QMSDocument.objects.filter(company=request.user, is_active=True).prefetch_related('version_history')
    doc_type = request.GET.get('type', '')
    if doc_type:
        docs = docs.filter(doc_type=doc_type)
    doc_types = QMSDocument.DOC_TYPE_CHOICES
    return render(request, 'qms/documents.html', {
        'documents': docs,
        'current_type': doc_type,
        'doc_types': doc_types,
        'today': timezone.now().date(),
    })


@_entrepreneur_required
def upload_document(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        doc_type = request.POST.get('doc_type', '')
        file = request.FILES.get('file')
        version = request.POST.get('version', '1.0').strip() or '1.0'
        expiry_raw = request.POST.get('expiry_date', '').strip()

        import os as _os
        allowed_types = {'application/pdf', 'application/msword',
                         'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                         'application/vnd.ms-excel',
                         'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         'image/jpeg', 'image/png'}
        allowed_exts = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.jpeg', '.png'}
        max_size = 10 * 1024 * 1024  # 10 MB
        file_ext = _os.path.splitext(file.name)[1].lower() if file else ''
        if not (title and doc_type and file):
            messages.error(request, 'Sarlavha, hujjat turi va faylni kiriting!')
        elif file.size > max_size:
            messages.error(request, 'Fayl hajmi 10 MB dan oshmasligi kerak!')
        elif file.content_type not in allowed_types or file_ext not in allowed_exts:
            messages.error(request, 'Faqat PDF, Word, Excel, JPG yoki PNG formatlar ruxsat etiladi!')
        else:
            QMSDocument.objects.create(
                company=request.user,
                title=title[:300],
                doc_type=doc_type,
                file=file,
                version=version,
                expiry_date=_parse_date(expiry_raw),
            )
            messages.success(request, 'Hujjat muvaffaqiyatli yuklandi.')
    return redirect('qms_documents')


@_entrepreneur_required
def delete_document(request, pk):
    if request.method != 'POST':
        return redirect('qms_documents')
    doc = get_object_or_404(QMSDocument, pk=pk, company=request.user)
    doc.is_active = False
    doc.save(update_fields=['is_active'])
    messages.success(request, 'Hujjat o\'chirildi.')
    return redirect('qms_documents')


@_entrepreneur_required
def update_document_version(request, pk):
    """Upload a new version of an existing document, keeping history."""
    doc = get_object_or_404(QMSDocument, pk=pk, company=request.user)
    if request.method == 'POST':
        new_file = request.FILES.get('file')
        new_version = request.POST.get('version', '').strip()
        change_note = request.POST.get('note', '').strip()

        if new_file and new_version:
            # Save current version to history before overwriting
            QMSDocumentVersion.objects.create(
                document=doc,
                version=doc.version,
                file=doc.file,
                note=change_note or f'Eski versiya: {doc.version}',
                created_by=request.user,
            )
            # Update the document to new version
            doc.file = new_file
            doc.version = new_version
            doc.save(update_fields=['file', 'version'])
            messages.success(request, f'Hujjat v{new_version} ga yangilandi.')
        else:
            messages.error(request, 'Yangi fayl va versiya raqamini kiriting!')
    return redirect('qms_documents')


@_entrepreneur_required
def nonconformities(request):
    ncs = NonConformity.objects.filter(company=request.user)
    status_filter = request.GET.get('status', '')
    if status_filter:
        ncs = ncs.filter(status=status_filter)
    return render(request, 'qms/nonconformities.html', {
        'nonconformities': ncs,
        'status_filter': status_filter,
    })


@_entrepreneur_required
def add_nonconformity(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        severity = request.POST.get('severity', 'minor')
        assigned_to = request.POST.get('assigned_to', '').strip()
        due_raw = request.POST.get('due_date', '').strip()

        if title and description:
            nc = NonConformity.objects.create(
                company=request.user,
                code=_next_nc_code(request.user),
                title=title[:300],
                description=description,
                severity=severity,
                assigned_to=assigned_to,
                due_date=_parse_date(due_raw),
            )
            from experts.models import Notification
            Notification.objects.create(
                user=request.user,
                title=_nl(request.user, f'Yangi nomuvofiqlik: {nc.code}', f'Новое несоответствие: {nc.code}', f'New nonconformity: {nc.code}'),
                message=_nl(request.user,
                    f'"{title[:80]}" nomuvofiqlik QMS tizimiga qo\'shildi. Holat: Ochiq.',
                    f'Несоответствие "{title[:80]}" добавлено в QMS. Статус: Открытое.',
                    f'Nonconformity "{title[:80]}" added to QMS. Status: Open.'),
                link='/qms/nc/',
            )
            messages.success(request, 'Nomuvofiqlik qo\'shildi.')
        else:
            messages.error(request, 'Sarlavha va tavsifni kiriting!')
    return redirect('nonconformities')


def _next_nc_code(company):
    """Generate unique NC code atomically. Locks the company row to serialize
    concurrent requests — COUNT alone doesn't lock on PostgreSQL."""
    from django.db import transaction
    from accounts.models import CustomUser as _CU
    year = timezone.now().year
    prefix = f'NC-{year}-'
    with transaction.atomic():
        _CU.objects.select_for_update().filter(pk=company.pk).get()
        count = NonConformity.objects.filter(
            company=company, code__startswith=prefix
        ).count()
        return f'{prefix}{count + 1:03d}'


@_entrepreneur_required
def update_nonconformity(request, pk):
    nc = get_object_or_404(NonConformity, pk=pk, company=request.user)
    if request.method == 'POST':
        new_status = request.POST.get('status', nc.status)
        valid_statuses = {c[0] for c in NonConformity.STATUS_CHOICES}
        nc.status = new_status if new_status in valid_statuses else nc.status
        nc.root_cause = request.POST.get('root_cause', '').strip()
        nc.corrective_action = request.POST.get('corrective_action', '').strip()
        if nc.status == 'closed' and not nc.closed_at:
            nc.closed_at = timezone.now()
        nc.save()
        messages.success(request, 'Nomuvofiqlik yangilandi.')
    return redirect('nonconformities')


@_entrepreneur_required
def audit_schedule(request):
    audits = AuditSchedule.objects.filter(company=request.user)
    today = timezone.now().date()
    return render(request, 'qms/audit_schedule.html', {
        'audits': audits,
        'today': today,
    })


@_entrepreneur_required
def checklist_print(request):
    """Print-friendly checklist report page."""
    standard = request.GET.get('standard', 'iso9001')
    if standard not in _VALID_STANDARDS:
        standard = 'iso9001'
    items = ChecklistItem.objects.filter(standard=standard, is_active=True)
    responses = {r.item_id: r for r in ChecklistResponse.objects.filter(company=request.user)}
    items_with_response = [
        {'item': item, 'response': responses.get(item.pk)}
        for item in items
    ]
    total = items.count()
    compliant = sum(1 for r in items_with_response if r['response'] and r['response'].status == 'compliant')
    partial = sum(1 for r in items_with_response if r['response'] and r['response'].status == 'partial')
    non_compliant = sum(1 for r in items_with_response if r['response'] and r['response'].status == 'non_compliant')
    pct = int(compliant / total * 100) if total else 0

    return render(request, 'qms/checklist_print.html', {
        'items_with_response': items_with_response,
        'current_standard': standard,
        'standard_label': STANDARD_LABELS.get(standard, standard.upper()),
        'total': total,
        'compliant': compliant,
        'partial': partial,
        'non_compliant': non_compliant,
        'pct': pct,
        'company': request.user,
        'today': timezone.now().date(),
    })


@_entrepreneur_required
def update_audit(request, pk):
    """AJAX or POST: change audit status inline."""
    audit = get_object_or_404(AuditSchedule, pk=pk, company=request.user)
    if request.method == 'POST':
        new_status = request.POST.get('status', '').strip()
        valid_statuses = [s[0] for s in AuditSchedule.STATUS_CHOICES]
        if new_status in valid_statuses:
            audit.status = new_status
            audit.save(update_fields=['status'])
            messages.success(request, 'Audit holati yangilandi.')
        else:
            messages.error(request, 'Noto\'g\'ri holat tanlandi.')
    return redirect('audit_schedule')


@_entrepreneur_required
def add_audit(request):
    if request.method == 'POST':
        audit_type = request.POST.get('audit_type', '')
        standard = request.POST.get('standard', '').strip()
        planned_date = request.POST.get('planned_date', '')
        auditor_name = request.POST.get('auditor_name', '').strip()
        notes = request.POST.get('notes', '').strip()

        pd = _parse_date(planned_date)
        if audit_type and standard and pd:
            from datetime import date as _date
            if pd < _date.today():
                messages.warning(request, 'Audit sanasi o\'tib ketgan. Kelajak sanasini kiriting.')
                return redirect('audit_schedule')
            AuditSchedule.objects.create(
                company=request.user,
                audit_type=audit_type,
                standard=standard,
                planned_date=pd,
                auditor_name=auditor_name,
                notes=notes,
            )
            messages.success(request, 'Audit rejaga qo\'shildi.')
        else:
            messages.error(request, 'Audit turi, standart va to\'g\'ri sana kiriting!')
    return redirect('audit_schedule')


# ---------------------------------------------------------------------------
# AI yordamchi
# ---------------------------------------------------------------------------

def _safe(text, max_len=300):
    return str(text or '')[:max_len].replace('\n', ' ').replace('\r', ' ')


def _qms_ai(prompt, max_tokens=900):
    """Call Groq once and return text, or (None, error_message)."""
    try:
        from groq import Groq
        client = Groq(api_key=settings.GROQ_API_KEY, timeout=settings.AI_TIMEOUT, max_retries=1)
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip(), None
    except Exception as e:
        logger.exception('QMS AI xatosi: %s', e)
        return None, str(e)


LANG_INSTRUCTION = {
    'uz': "O'zbek tilida yoz.",
    'ru': "Напиши на русском языке.",
    'en': "Write in English.",
}


@_entrepreneur_required
@ratelimit(key='user', rate='10/m', method='POST', block=False)
def ai_nc_suggestion(request, pk):
    """AJAX POST: AI suggests root cause + corrective action for a non-conformity."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    if getattr(request, 'limited', False):
        return JsonResponse({'success': False, 'error': 'Juda ko\'p so\'rov. Biroz kuting.'}, status=429)
    nc = get_object_or_404(NonConformity, pk=pk, company=request.user)
    lang = request.session.get('lang', 'uz')
    prompt = (
        "Sen ISO sifat menejmenti bo'yicha auditorsan. "
        f"{LANG_INSTRUCTION.get(lang, LANG_INSTRUCTION['uz'])}\n"
        f"Quyidagi nomuvofiqlik uchun tub sababni (root cause, 5-Whys yondashuvi) va "
        f"aniq tuzatuvchi chora-tadbirlarni (corrective action) taklif qil.\n\n"
        f"Nomuvofiqlik: {_safe(nc.title, 200)}\n"
        f"Tavsif: {_safe(nc.description, 500)}\n"
        f"Jiddiylik: {nc.get_severity_display()}\n\n"
        "Javobni ikki qism qilib ber: '## Tub sabab' va '## Tuzatuvchi chora'. Qisqa va amaliy."
    )
    text, err = _qms_ai(prompt)
    if err:
        return JsonResponse({'success': False, 'error': err}, status=502)
    nc.ai_suggestion = text
    nc.save(update_fields=['ai_suggestion'])
    return JsonResponse({'success': True, 'suggestion': text})


@_entrepreneur_required
@ratelimit(key='user', rate='5/m', method='POST', block=False)
def qms_generate_policy(request):
    """AI generates an ISO policy/procedure and stores it as a QMS document."""
    if request.method != 'POST':
        return redirect('qms_documents')
    if getattr(request, 'limited', False):
        messages.error(request, 'Juda ko\'p so\'rov. Biroz kuting.')
        return redirect('qms_documents')
    standard = _safe(request.POST.get('standard', '').strip() or 'ISO 9001', 50)
    doc_type = request.POST.get('doc_type', 'policy')
    topic = _safe(request.POST.get('topic', '').strip(), 200)
    lang = request.POST.get('language', request.session.get('lang', 'uz'))
    company = _safe(request.user.company_name or 'Korxona', 100)
    industry = _safe(request.user.industry or 'Umumiy', 100)

    type_label = dict(QMSDocument.DOC_TYPE_CHOICES).get(doc_type, doc_type)
    title_topic = topic or type_label
    prompt = (
        "Sen ISO standartlari bo'yicha mutaxassisson. "
        f"{LANG_INSTRUCTION.get(lang, LANG_INSTRUCTION['uz'])}\n"
        f"'{company}' korxonasi ({industry} sohasi) uchun {standard} talablariga mos "
        f"'{title_topic}' nomli {type_label.lower()} hujjatini to'liq yoz.\n"
        "Sarlavhalar, maqsad, qamrov, javobgarlik va amaliy bandlar bilan. "
        "Markdown formatida, professional va tayyor hujjat ber."
    )
    text, err = _qms_ai(prompt, max_tokens=2000)
    if err or not text or not text.strip():
        messages.error(request, f'AI hujjat yarata olmadi. Qayta urinib ko\'ring.')
        return redirect('qms_documents')

    title = f'{title_topic} — {standard}'
    doc = QMSDocument(
        company=request.user,
        title=title[:300],
        doc_type=doc_type,
        version='1.0',
        ai_content=text,
    )
    try:
        doc.save()
    except Exception:
        messages.error(request, 'Hujjat saqlashda xato yuz berdi. Qayta urinib ko\'ring.')
        return redirect('qms_documents')
    messages.success(request, 'AI hujjat yaratildi.')
    return redirect('qms_document_view', pk=doc.pk)


@_entrepreneur_required
def qms_document_view(request, pk):
    """Inline rendered view for AI-generated documents."""
    doc = get_object_or_404(QMSDocument, pk=pk, company=request.user, is_active=True)
    # ai_content DB field dan o'qiymiz (fayl kerak emas)
    content = doc.ai_content
    # Eski hujjatlar uchun fallback: fayldan o'qib ai_content ga saqlaymiz
    if not content and doc.file and doc.file.name.endswith('.md'):
        try:
            doc.file.open('r')
            raw = doc.file.read()
            doc.file.close()
            content = raw.decode('utf-8') if isinstance(raw, bytes) else raw
            # Bir marta saqlab qo'yamiz
            doc.ai_content = content
            doc.save(update_fields=['ai_content'])
        except Exception:
            content = ''
    return render(request, 'qms/document_view.html', {'doc': doc, 'content': content})


# ---------------------------------------------------------------------------
# Risk Register
# ---------------------------------------------------------------------------

@_entrepreneur_required
def risk_register(request):
    risks = RiskItem.objects.filter(company=request.user)
    standard_filter = request.GET.get('standard', '')
    status_filter = request.GET.get('status', '')
    if standard_filter and standard_filter in _VALID_STANDARDS:
        risks = risks.filter(standard=standard_filter)
    if status_filter:
        risks = risks.filter(status=status_filter)

    # Stats for matrix
    total = risks.count()
    critical_count = sum(1 for r in risks if r.risk_level == 'critical')
    high_count = sum(1 for r in risks if r.risk_level == 'high')

    return render(request, 'qms/risk_register.html', {
        'risks': risks,
        'standard_filter': standard_filter,
        'status_filter': status_filter,
        'total': total,
        'critical_count': critical_count,
        'high_count': high_count,
        'standards': RiskItem.STANDARD_CHOICES,
        'statuses': RiskItem.STATUS_CHOICES,
    })


@_entrepreneur_required
def add_risk(request):
    if request.method == 'POST':
        process_area = request.POST.get('process_area', '').strip()
        description = request.POST.get('description', '').strip()
        standard = request.POST.get('standard', 'iso9001')
        owner = request.POST.get('owner', '').strip()
        due_raw = request.POST.get('due_date', '').strip()

        try:
            likelihood = int(request.POST.get('likelihood', 3))
            impact = int(request.POST.get('impact', 3))
            likelihood = max(1, min(5, likelihood))
            impact = max(1, min(5, impact))
        except (ValueError, TypeError):
            likelihood, impact = 3, 3

        if process_area and description:
            RiskItem.objects.create(
                company=request.user,
                standard=standard,
                process_area=process_area[:200],
                description=description,
                likelihood=likelihood,
                impact=impact,
                owner=owner,
                due_date=_parse_date(due_raw),
            )
            messages.success(request, 'Risk qo\'shildi.')
        else:
            messages.error(request, 'Jarayon nomi va risk tavsifini kiriting!')
    return redirect('risk_register')


@_entrepreneur_required
def update_risk(request, pk):
    risk = get_object_or_404(RiskItem, pk=pk, company=request.user)
    if request.method == 'POST':
        new_status = request.POST.get('status', risk.status)
        if new_status in {c[0] for c in RiskItem.STATUS_CHOICES}:
            risk.status = new_status
        risk.mitigation = request.POST.get('mitigation', '').strip()
        risk.owner = request.POST.get('owner', '').strip()
        try:
            likelihood = int(request.POST.get('likelihood', risk.likelihood))
            impact = int(request.POST.get('impact', risk.impact))
            risk.likelihood = max(1, min(5, likelihood))
            risk.impact = max(1, min(5, impact))
        except (ValueError, TypeError):
            pass
        due_raw = request.POST.get('due_date', '').strip()
        risk.due_date = _parse_date(due_raw) if due_raw else None
        risk.save()
        messages.success(request, 'Risk yangilandi.')
    return redirect('risk_register')


@_entrepreneur_required
def delete_risk(request, pk):
    if request.method != 'POST':
        return redirect('risk_register')
    risk = get_object_or_404(RiskItem, pk=pk, company=request.user)
    risk.delete()
    messages.success(request, 'Risk o\'chirildi.')
    return redirect('risk_register')


@_entrepreneur_required
def export_risk_csv(request):
    risks = RiskItem.objects.filter(company=request.user)
    resp = _csv_response('risk_register.csv')
    w = csv.writer(resp)
    w.writerow(['Standart', 'Jarayon', 'Tavsif', 'Ehtimol', 'Ta\'sir', 'Risk ball',
                'Risk darajasi', 'Kamaytirish', 'Masul', 'Holat', 'Muddat'])
    for r in risks:
        w.writerow([
            r.get_standard_display(), r.process_area, r.description,
            r.likelihood, r.impact, r.risk_score, r.risk_level,
            r.mitigation, r.owner, r.get_status_display(),
            r.due_date or '',
        ])
    return resp


# ---------------------------------------------------------------------------
# Training Records
# ---------------------------------------------------------------------------

@_entrepreneur_required
def training_records(request):
    records = TrainingRecord.objects.filter(company=request.user)
    today = timezone.now().date()
    expiring_soon = [r for r in records if r.days_to_expiry is not None and 0 <= r.days_to_expiry <= 30]
    expired = [r for r in records if r.is_expired]
    return render(request, 'qms/training_records.html', {
        'records': records,
        'expiring_soon': expiring_soon,
        'expired': expired,
        'today': today,
    })


@_entrepreneur_required
def add_training(request):
    if request.method == 'POST':
        employee_name = request.POST.get('employee_name', '').strip()
        training_name = request.POST.get('training_name', '').strip()
        date_completed = request.POST.get('date_completed', '').strip()

        parsed_date = _parse_date(date_completed)
        if employee_name and training_name and parsed_date:
            expiry_raw = request.POST.get('expiry_date', '').strip()
            TrainingRecord.objects.create(
                company=request.user,
                employee_name=employee_name[:200],
                position=request.POST.get('position', '').strip()[:200],
                training_name=training_name[:300],
                standard_clause=request.POST.get('standard_clause', '').strip()[:100],
                date_completed=parsed_date,
                trainer=request.POST.get('trainer', '').strip()[:200],
                certificate_number=request.POST.get('certificate_number', '').strip()[:100],
                expiry_date=_parse_date(expiry_raw),
            )
            messages.success(request, 'O\'quv yozuvi qo\'shildi.')
        else:
            messages.error(request, 'Xodim ismi, o\'quv nomi va to\'g\'ri sana kiritilishi shart!')
    return redirect('training_records')


@_entrepreneur_required
def delete_training(request, pk):
    if request.method != 'POST':
        return redirect('training_records')
    record = get_object_or_404(TrainingRecord, pk=pk, company=request.user)
    record.delete()
    messages.success(request, 'Yozuv o\'chirildi.')
    return redirect('training_records')


@_entrepreneur_required
def export_training_csv(request):
    records = TrainingRecord.objects.filter(company=request.user)
    resp = _csv_response('training_records.csv')
    w = csv.writer(resp)
    w.writerow(['Xodim', 'Lavozim', 'O\'quv nomi', 'ISO band', 'Sana',
                'O\'qituvchi', 'Sertifikat raqami', 'Amal qilish muddati'])
    for r in records:
        w.writerow([
            r.employee_name, r.position, r.training_name, r.standard_clause,
            r.date_completed, r.trainer, r.certificate_number, r.expiry_date or '',
        ])
    return resp


# ---------------------------------------------------------------------------
# NC Effectiveness verify
# ---------------------------------------------------------------------------

@_entrepreneur_required
def verify_nc_effectiveness(request, pk):
    nc = get_object_or_404(NonConformity, pk=pk, company=request.user)
    if request.method == 'POST' and nc.status == 'closed':
        nc.is_effective_verified = True
        nc.verification_note = request.POST.get('verification_note', '').strip()
        nc.verified_at = timezone.now()
        nc.save(update_fields=['is_effective_verified', 'verification_note', 'verified_at'])
        messages.success(request, 'Samaradorlik tasdiqlandi.')
    return redirect('nonconformities')


# ---------------------------------------------------------------------------
# Eksport (Excel-mos CSV)
# ---------------------------------------------------------------------------

def _csv_response(filename):
    resp = HttpResponse(content_type='text/csv; charset=utf-8')
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
    resp.write('﻿')  # BOM so Excel reads UTF-8 correctly
    return resp


@_entrepreneur_required
def export_checklist_csv(request):
    standard = request.GET.get('standard', 'iso9001')
    if standard not in _VALID_STANDARDS:
        standard = 'iso9001'
    items = ChecklistItem.objects.filter(standard=standard, is_active=True)
    responses = {r.item_id: r for r in ChecklistResponse.objects.filter(company=request.user)}
    resp = _csv_response(f'checklist_{standard}.csv')
    w = csv.writer(resp)
    w.writerow(['Band', 'Savol', 'Talab', 'Holat', 'Izoh', 'Dalil'])
    for item in items:
        r = responses.get(item.pk)
        w.writerow([
            item.clause, item.question, item.requirement,
            r.get_status_display() if r else 'Tekshirilmagan',
            r.note if r else '', r.evidence_text if r else '',
        ])
    return resp


@_entrepreneur_required
def export_nc_csv(request):
    ncs = NonConformity.objects.filter(company=request.user)
    resp = _csv_response('nonconformities.csv')
    w = csv.writer(resp)
    w.writerow(['Raqam', 'Sarlavha', 'Jiddiylik', 'Holat', 'Masul', 'Muddat',
                'Tub sabab', 'Tuzatuvchi chora', 'Yaratilgan'])
    for nc in ncs:
        w.writerow([
            nc.code, nc.title, nc.get_severity_display(), nc.get_status_display(),
            nc.assigned_to, nc.due_date or '', nc.root_cause, nc.corrective_action,
            nc.created_at.strftime('%d.%m.%Y'),
        ])
    return resp
