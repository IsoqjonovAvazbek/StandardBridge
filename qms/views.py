from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.conf import settings
from django.core.files.base import ContentFile
from datetime import timedelta
from django_ratelimit.decorators import ratelimit
from .models import ChecklistItem, ChecklistResponse, QMSDocument, QMSDocumentVersion, NonConformity, AuditSchedule
import json
import csv
import os
import logging

logger = logging.getLogger('standardbridge')


@login_required
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
    })


STANDARD_LABELS = {
    'iso9001': 'ISO 9001',
    'iso22000': 'ISO 22000',
    'iso14001': 'ISO 14001',
    'iso45001': 'ISO 45001',
}


@login_required
def qms_checklist(request):
    standard = request.GET.get('standard', 'iso9001')
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
    std_codes = (
        ChecklistItem.objects
        .filter(is_active=True)
        .values_list('standard', flat=True)
        .distinct()
        .order_by('standard')
    )

    standards = []
    for code in std_codes:
        total = ChecklistItem.objects.filter(standard=code, is_active=True).count()
        compliant = ChecklistResponse.objects.filter(
            company=request.user, item__standard=code, status='compliant'
        ).count()
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


@login_required
def update_checklist(request):
    """AJAX endpoint — saves a single checklist item response."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'success': False, 'error': 'invalid json'}, status=400)

        item_id = data.get('item_id')
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


@login_required
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


@login_required
def upload_document(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        doc_type = request.POST.get('doc_type', '')
        file = request.FILES.get('file')
        version = request.POST.get('version', '1.0').strip() or '1.0'
        expiry_raw = request.POST.get('expiry_date', '').strip()

        allowed_types = {'application/pdf', 'application/msword',
                         'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                         'application/vnd.ms-excel',
                         'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         'image/jpeg', 'image/png'}
        max_size = 10 * 1024 * 1024  # 10 MB
        if not (title and doc_type and file):
            messages.error(request, 'Sarlavha, hujjat turi va faylni kiriting!')
        elif file.size > max_size:
            messages.error(request, 'Fayl hajmi 10 MB dan oshmasligi kerak!')
        elif file.content_type not in allowed_types:
            messages.error(request, 'Faqat PDF, Word, Excel, JPG yoki PNG formatlar ruxsat etiladi!')
        else:
            QMSDocument.objects.create(
                company=request.user,
                title=title[:300],
                doc_type=doc_type,
                file=file,
                version=version,
                expiry_date=expiry_raw if expiry_raw else None,
            )
            messages.success(request, 'Hujjat muvaffaqiyatli yuklandi.')
    return redirect('qms_documents')


@login_required
def delete_document(request, pk):
    if request.method != 'POST':
        return redirect('qms_documents')
    doc = get_object_or_404(QMSDocument, pk=pk, company=request.user)
    doc.is_active = False
    doc.save(update_fields=['is_active'])
    messages.success(request, 'Hujjat o\'chirildi.')
    return redirect('qms_documents')


@login_required
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


@login_required
def nonconformities(request):
    ncs = NonConformity.objects.filter(company=request.user)
    status_filter = request.GET.get('status', '')
    if status_filter:
        ncs = ncs.filter(status=status_filter)
    return render(request, 'qms/nonconformities.html', {
        'nonconformities': ncs,
        'status_filter': status_filter,
    })


@login_required
def add_nonconformity(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        severity = request.POST.get('severity', 'minor')
        assigned_to = request.POST.get('assigned_to', '').strip()
        due_raw = request.POST.get('due_date', '').strip()

        if title and description:
            NonConformity.objects.create(
                company=request.user,
                code=_next_nc_code(request.user),
                title=title[:300],
                description=description,
                severity=severity,
                assigned_to=assigned_to,
                due_date=due_raw if due_raw else None,
            )
            messages.success(request, 'Nomuvofiqlik qo\'shildi.')
        else:
            messages.error(request, 'Sarlavha va tavsifni kiriting!')
    return redirect('nonconformities')


def _next_nc_code(company):
    """Generate a per-company, per-year traceable NC code: NC-2026-001."""
    year = timezone.now().year
    prefix = f'NC-{year}-'
    count = NonConformity.objects.filter(
        company=company, code__startswith=prefix
    ).count()
    return f'{prefix}{count + 1:03d}'


@login_required
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


@login_required
def audit_schedule(request):
    audits = AuditSchedule.objects.filter(company=request.user)
    today = timezone.now().date()
    return render(request, 'qms/audit_schedule.html', {
        'audits': audits,
        'today': today,
    })


@login_required
def checklist_print(request):
    """Print-friendly checklist report page."""
    standard = request.GET.get('standard', 'iso9001')
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


@login_required
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


@login_required
def add_audit(request):
    if request.method == 'POST':
        audit_type = request.POST.get('audit_type', '')
        standard = request.POST.get('standard', '').strip()
        planned_date = request.POST.get('planned_date', '')
        auditor_name = request.POST.get('auditor_name', '').strip()
        notes = request.POST.get('notes', '').strip()

        if audit_type and standard and planned_date:
            from datetime import date as _date, datetime as _dt
            try:
                pd = _dt.strptime(planned_date, '%Y-%m-%d').date()
                if pd < _date.today():
                    messages.warning(request, 'Audit sanasi o\'tib ketgan. Kelajak sanasini kiriting.')
            except ValueError:
                pass
            AuditSchedule.objects.create(
                company=request.user,
                audit_type=audit_type,
                standard=standard,
                planned_date=planned_date,
                auditor_name=auditor_name,
                notes=notes,
            )
            messages.success(request, 'Audit rejaga qo\'shildi.')
        else:
            messages.error(request, 'Audit turi, standart va sanani kiriting!')
    return redirect('audit_schedule')


# ---------------------------------------------------------------------------
# AI yordamchi
# ---------------------------------------------------------------------------

def _qms_ai(prompt, max_tokens=900):
    """Call Groq once and return text, or (None, error_message)."""
    try:
        from groq import Groq
        client = Groq(api_key=os.environ.get('GROQ_API_KEY'), timeout=settings.AI_TIMEOUT, max_retries=1)
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


@login_required
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
        f"Nomuvofiqlik: {nc.title}\n"
        f"Tavsif: {nc.description}\n"
        f"Jiddiylik: {nc.get_severity_display()}\n\n"
        "Javobni ikki qism qilib ber: '## Tub sabab' va '## Tuzatuvchi chora'. Qisqa va amaliy."
    )
    text, err = _qms_ai(prompt)
    if err:
        return JsonResponse({'success': False, 'error': err}, status=502)
    nc.ai_suggestion = text
    nc.save(update_fields=['ai_suggestion'])
    return JsonResponse({'success': True, 'suggestion': text})


@login_required
@ratelimit(key='user', rate='5/m', method='POST', block=False)
def qms_generate_policy(request):
    """AI generates an ISO policy/procedure and stores it as a QMS document."""
    if request.method != 'POST':
        return redirect('qms_documents')
    if getattr(request, 'limited', False):
        messages.error(request, 'Juda ko\'p so\'rov. Biroz kuting.')
        return redirect('qms_documents')
    standard = request.POST.get('standard', '').strip() or 'ISO 9001'
    doc_type = request.POST.get('doc_type', 'policy')
    topic = request.POST.get('topic', '').strip()
    lang = request.POST.get('language', request.session.get('lang', 'uz'))
    company = request.user.company_name or 'Korxona'
    industry = request.user.industry or 'Umumiy'

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
    )
    safe_name = f"ai_{doc_type}_{timezone.now():%Y%m%d_%H%M%S}.md"
    doc.file.save(safe_name, ContentFile(text.encode('utf-8')), save=False)
    doc.save()
    messages.success(request, 'AI hujjat yaratildi va hujjatlar ro\'yxatiga qo\'shildi.')
    return redirect('qms_documents')


# ---------------------------------------------------------------------------
# Eksport (Excel-mos CSV)
# ---------------------------------------------------------------------------

def _csv_response(filename):
    resp = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
    resp.write('﻿')  # BOM so Excel reads UTF-8 correctly
    return resp


@login_required
def export_checklist_csv(request):
    standard = request.GET.get('standard', 'iso9001')
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


@login_required
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
