from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from .models import GapAnalysis, Standard, GapItem, Roadmap, RoadmapStep, Industry, Question, QuestionAnswer, DisclaimerAcceptance
from experts.models import Project, Notification
import json
import os
import threading
import logging
from groq import Groq

logger = logging.getLogger('standardbridge')


AI_LANG_INSTRUCTION = {
    'uz': "Barcha matnlarni (title, description, summary) O'ZBEK tilida yoz.",
    'ru': "Все тексты (title, description, summary) пиши на РУССКОМ языке.",
    'en': "Write all text fields (title, description, summary) in ENGLISH.",
}


def _extract_json(text):
    """Robustly pull a JSON object out of an AI response (handles ``` fences and prose)."""
    import re
    text = text.strip()
    # Strip markdown code fences
    if text.startswith('```'):
        text = re.sub(r'^```[a-zA-Z]*\n?', '', text)
        text = re.sub(r'\n?```$', '', text).strip()
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass
    # Fallback: grab the outermost {...} block
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    raise ValueError('AI javobidan JSON ajratib bo\'lmadi')


def get_ai_analysis(local_standards, target_standards, industry_name, weak_answers,
                    company_context='', readiness=None, language='uz'):
    client = Groq(api_key=os.environ.get('GROQ_API_KEY'), timeout=settings.AI_TIMEOUT, max_retries=1)

    local_codes = ', '.join([s.code for s in local_standards])
    target_codes = ', '.join([s.code for s in target_standards])

    weak_text = '\n'.join([f"- {q}: {a}" for q, a in weak_answers]) if weak_answers else "Aniqlanmadi"
    lang_rule = AI_LANG_INSTRUCTION.get(language, AI_LANG_INSTRUCTION['uz'])
    context_block = f"\nKorxona ma'lumotlari:\n{company_context}\n" if company_context else ""
    readiness_block = f"\nKorxonaning hozirgi tayyorlik darajasi: {readiness}%\n" if readiness is not None else ""

    prompt = f"""Sen standartlar bo'yicha mutaxassisson.

Soha: {industry_name}
Hozirgi standartlar: {local_codes}
Maqsadli standartlar: {target_codes}
{context_block}{readiness_block}
Korxonada aniqlangan kamchiliklar (faqat "Yo'q" va "Qisman" javoblar):
{weak_text}

MUHIM: Faqat yuqoridagi kamchiliklar va korxona ma'lumotlariga asoslanib gap tahlil qil. Tavsiyalarni korxona hajmi va holatiga moslab ber.
{lang_rule}

Quyidagi formatda JSON javob ber (boshqa hech narsa yozma, faqat JSON):
{{
    "gaps": [
        {{
            "title": "Gap nomi",
            "description": "Batafsil tavsif",
            "priority": "critical",
            "estimated_days": 30
        }}
    ],
    "total_days": 180,
    "estimated_cost": 3000,
    "cost_breakdown": {{"consulting": 2000, "certification_body": 1000}},
    "roadmap_steps": [
        {{
            "order": 1,
            "title": "Qadam nomi (qisqa, aniq)",
            "description": "Batafsil: 1) nima qilinadi (aniq harakatlar ro'yxati), 2) qaysi hujjatlar tayyorlanadi, 3) kutilgan natija. Kamida 3-4 jumla, amaliy.",
            "deliverables": ["Tayyorlanadigan hujjat yoki natija 1", "natija 2"],
            "duration_days": 30
        }}
    ],
    "summary": "Umumiy tavsif"
}}

MUHIM QOIDALAR:
- total_days: har bir gap uchun estimated_days larni qo'sh
- estimated_cost: kichik korxona uchun $500-2000, o'rta uchun $2000-5000
- cost_breakdown: estimated_cost ni konsalting va sertifikatsiya organi to'lovlariga ajrat
- priority faqat shu qiymatlardan: critical, high, medium, low
- roadmap_steps: 5-8 ta aniq, amaliy bosqich bo'lsin. Har bir description BATAFSIL bo'lsin (nima qilinadi, qaysi hujjat, qanday natija) — quruq bir jumla emas
- deliverables: har qadamda 1-3 ta aniq tayyorlanadigan hujjat/natija
- Agar kamchilik 1 ta bo'lsa, total_days 30-60 oralig'ida bo'lsin
- Agar kamchilik yo'q bo'lsa (hamma Ha desa), gaps bo'sh bo'lsin"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=2000,
    )

    return _extract_json(response.choices[0].message.content)


@login_required
def entrepreneur_dashboard(request):
    from experts.models import Project

    all_projects = Project.objects.filter(
        entrepreneur=request.user
    ).order_by('-created_at')

    # IDs of analyses that have NON-completed, NON-cancelled projects (i.e. "active" projects)
    # Used in template to hide the delete button for analyses with ongoing projects.
    project_analysis_ids = list(
        all_projects.exclude(status__in=['cancelled', 'completed'])
        .values_list('analysis_id', flat=True)
    )

    analyses = GapAnalysis.objects.filter(
        entrepreneur=request.user,
        status='completed'
    ).order_by('-created_at')

    negotiating_projects = all_projects.filter(status='negotiating')
    active_projects = all_projects.filter(status__in=['accepted', 'in_progress', 'review'])
    completed_projects = all_projects.filter(status='completed')

    context = {
        'analyses': analyses,
        'project_analysis_ids': project_analysis_ids,
        'total': analyses.count(),
        'negotiating_projects': negotiating_projects,
        'active_projects': active_projects,
        'completed_projects': completed_projects,
    }
    return render(request, 'analysis/entrepreneur_dashboard.html', context)
@login_required
def select_industry(request):
    industries = Industry.objects.filter(is_active=True)
    return render(request, 'analysis/select_industry.html', {'industries': industries})


@login_required
def select_standards(request, industry_id):
    industry = get_object_or_404(Industry, pk=industry_id)
    local_standards = Standard.objects.filter(
        type='local', is_active=True, industry=industry
    )
    target_standards = Standard.objects.filter(
        type='international', is_active=True, industry=industry
    )

    if request.method == 'POST':
        local_ids = request.POST.getlist('local_standards')
        target_ids = request.POST.getlist('target_standards')

        if not local_ids or not target_ids:
            messages.error(request, 'Kamida bittadan standart tanlang!')
            return render(request, 'analysis/select_standards.html', {
                'industry': industry,
                'local_standards': local_standards,
                'target_standards': target_standards,
            })

        request.session['local_ids'] = local_ids
        request.session['target_ids'] = target_ids
        return redirect('answer_questions', industry_id=industry_id)

    return render(request, 'analysis/select_standards.html', {
        'industry': industry,
        'local_standards': local_standards,
        'target_standards': target_standards,
    })


@login_required
def answer_questions(request, industry_id):
    industry = get_object_or_404(Industry, pk=industry_id)
    target_ids = request.session.get('target_ids', [])

    target_standards = Standard.objects.filter(pk__in=target_ids)
    questions = Question.objects.filter(
        standard__in=target_standards,
        is_active=True
    ).select_related('standard')

    if not questions:
        return redirect('run_analysis', industry_id=industry_id)

    if request.method == 'POST':
        request.session['question_answers'] = {}
        for question in questions:
            answer = request.POST.get(f'question_{question.pk}', 'no')
            request.session['question_answers'][str(question.pk)] = answer
        # Capture company context (improves AI analysis quality)
        request.session['company_context'] = {
            'employee_count': request.POST.get('employee_count', '').strip(),
            'current_state': request.POST.get('current_state', '').strip(),
            'export_markets': request.POST.get('export_markets', '').strip(),
            'existing_certs': request.POST.get('existing_certs', '').strip(),
        }
        request.session.modified = True
        return redirect('run_analysis', industry_id=industry_id)

    context = {
        'industry': industry,
        'questions': questions,
        'target_standards': target_standards,
    }
    return render(request, 'analysis/answer_questions.html', context)


def _compute_readiness(question_answers):
    """Readiness % from answers: yes=1.0, partial=0.5, no=0.0."""
    if not question_answers:
        return None
    weights = {'yes': 1.0, 'partial': 0.5, 'no': 0.0}
    total = sum(weights.get(a, 0.0) for a in question_answers.values())
    return int(total / len(question_answers) * 100)


def _ai_background_task(analysis_id, local_ids, target_ids, industry_name, weak_answers,
                        company_context='', readiness=None, language='uz'):
    """AI tahlilni background threadda bajaradi."""
    import django
    django.db.close_old_connections()
    try:
        analysis = GapAnalysis.objects.get(pk=analysis_id)
        local_standards = Standard.objects.filter(pk__in=local_ids)
        target_standards = Standard.objects.filter(pk__in=target_ids)

        ai_result = get_ai_analysis(
            local_standards, target_standards, industry_name, weak_answers,
            company_context=company_context, readiness=readiness, language=language,
        )

        analysis.ai_result = ai_result
        analysis.status = 'completed'
        analysis.save()

        roadmap = Roadmap.objects.create(
            analysis=analysis,
            total_days=ai_result.get('total_days', 0),
            estimated_cost=ai_result.get('estimated_cost', 0),
        )
        valid_priorities = {'critical', 'high', 'medium', 'low'}
        for gap_data in ai_result.get('gaps', []):
            priority = gap_data.get('priority', 'medium')
            if priority not in valid_priorities:
                priority = 'medium'
            GapItem.objects.create(
                analysis=analysis,
                title=gap_data.get('title', 'Nomsiz gap')[:300],
                description=gap_data.get('description', ''),
                priority=priority,
                estimated_days=gap_data.get('estimated_days', 0) or 0,
            )
        for i, step_data in enumerate(ai_result.get('roadmap_steps', []), start=1):
            deliverables = step_data.get('deliverables', [])
            if not isinstance(deliverables, list):
                deliverables = []
            RoadmapStep.objects.create(
                roadmap=roadmap,
                order=step_data.get('order', i),
                title=step_data.get('title', f'Qadam {i}')[:300],
                description=step_data.get('description', ''),
                deliverables=[str(d)[:300] for d in deliverables][:5],
                duration_days=step_data.get('duration_days', 0) or 0,
            )

        # Remove any orphaned expert-less projects for this analysis
        Project.objects.filter(analysis=analysis, expert__isnull=True).delete()

    except Exception as e:
        logger.exception('AI tahlil xatosi (analysis_id=%s): %s', analysis_id, e)
        try:
            analysis = GapAnalysis.objects.get(pk=analysis_id)
            analysis.status = 'pending'
            analysis.ai_result = {'error': str(e)}
            analysis.save()
        except Exception:
            logger.exception('AI xato holatini saqlashda xatolik (analysis_id=%s)', analysis_id)
    finally:
        django.db.close_old_connections()


@login_required
def run_analysis(request, industry_id):
    industry = get_object_or_404(Industry, pk=industry_id)
    local_ids = request.session.get('local_ids', [])
    target_ids = request.session.get('target_ids', [])
    question_answers = request.session.get('question_answers', {})

    if not local_ids or not target_ids:
        return redirect('select_industry')

    local_standards = Standard.objects.filter(pk__in=local_ids)
    target_standards = Standard.objects.filter(pk__in=target_ids)

    weak_answers = []
    for q_id, answer in question_answers.items():
        if answer in ['no', 'partial']:
            try:
                question = Question.objects.get(pk=int(q_id))
                weak_answers.append((question.text, 'Yo\'q' if answer == 'no' else 'Qisman'))
            except Question.DoesNotExist:
                pass

    readiness = _compute_readiness(question_answers)
    company_context = _build_company_context(request.user, request.session.get('company_context', {}))
    language = request.session.get('lang', 'uz')

    analysis = GapAnalysis.objects.create(
        entrepreneur=request.user,
        local_standard=local_standards.first(),
        target_standard=target_standards.first(),
        industry=industry,
        company_info=company_context,
        status='in_progress',
    )

    for q_id, answer in question_answers.items():
        try:
            question = Question.objects.get(pk=int(q_id))
            QuestionAnswer.objects.create(analysis=analysis, question=question, answer=answer)
        except Question.DoesNotExist:
            pass

    request.session.pop('local_ids', None)
    request.session.pop('target_ids', None)
    request.session.pop('question_answers', None)
    request.session.pop('company_context', None)

    thread = threading.Thread(
        target=_ai_background_task,
        args=(analysis.pk, list(local_ids), list(target_ids), industry.name, weak_answers,
              company_context, readiness, language),
        daemon=True,
    )
    thread.start()

    return redirect('analysis_processing', pk=analysis.pk)


def _build_company_context(user, ctx):
    """Build a human-readable company context block from profile + form input."""
    parts = []
    if user.company_name:
        parts.append(f"Korxona: {user.company_name}")
    if ctx.get('employee_count'):
        parts.append(f"Xodimlar soni: {ctx['employee_count']}")
    if ctx.get('current_state'):
        parts.append(f"Hozirgi holat: {ctx['current_state']}")
    if ctx.get('export_markets'):
        parts.append(f"Eksport bozorlari: {ctx['export_markets']}")
    if ctx.get('existing_certs'):
        parts.append(f"Mavjud sertifikatlar: {ctx['existing_certs']}")
    return '\n'.join(parts)


def _relaunch_analysis(analysis):
    """Re-run the AI task for an existing analysis using its saved data (for retry)."""
    answers = {str(a.question_id): a.answer for a in analysis.answers.all()}
    weak_answers = []
    for a in analysis.answers.select_related('question').all():
        if a.answer in ('no', 'partial'):
            weak_answers.append((a.question.text, 'Yo\'q' if a.answer == 'no' else 'Qisman'))
    readiness = _compute_readiness(answers)
    local_ids = [analysis.local_standard_id] if analysis.local_standard_id else []
    target_ids = [analysis.target_standard_id] if analysis.target_standard_id else []
    industry_name = analysis.industry.name if analysis.industry else 'Umumiy'
    language = 'uz'

    analysis.status = 'in_progress'
    analysis.ai_result = None
    analysis.save(update_fields=['status', 'ai_result'])
    # Clear any partial previous results
    analysis.gaps.all().delete()
    Roadmap.objects.filter(analysis=analysis).delete()

    thread = threading.Thread(
        target=_ai_background_task,
        args=(analysis.pk, local_ids, target_ids, industry_name, weak_answers,
              analysis.company_info or '', readiness, language),
        daemon=True,
    )
    thread.start()


@login_required
def analysis_processing(request, pk):
    analysis = get_object_or_404(GapAnalysis, pk=pk, entrepreneur=request.user)
    if analysis.status == 'completed':
        return redirect('analysis_detail', pk=pk)
    # On AI failure, stay on the page and offer a retry (work is NOT lost — answers saved in DB)
    has_error = analysis.status == 'pending' and analysis.ai_result and 'error' in analysis.ai_result
    return render(request, 'analysis/processing.html', {
        'analysis': analysis,
        'has_error': has_error,
    })


@login_required
def analysis_retry(request, pk):
    """Re-run a failed analysis without losing the entrepreneur's answers."""
    analysis = get_object_or_404(GapAnalysis, pk=pk, entrepreneur=request.user)
    if request.method == 'POST':
        _relaunch_analysis(analysis)
        messages.info(request, 'AI tahlil qayta boshlandi.')
    return redirect('analysis_processing', pk=pk)


@login_required
def analysis_status(request, pk):
    analysis = get_object_or_404(GapAnalysis, pk=pk, entrepreneur=request.user)
    has_error = bool(analysis.status == 'pending' and analysis.ai_result and 'error' in analysis.ai_result)
    return JsonResponse({'status': analysis.status, 'pk': analysis.pk, 'has_error': has_error})


@login_required
def analysis_detail(request, pk):
    analysis = get_object_or_404(GapAnalysis, pk=pk, entrepreneur=request.user)
    gaps = analysis.gaps.all()
    priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    gaps = sorted(gaps, key=lambda x: priority_order.get(x.priority, 4))
    answers = analysis.answers.select_related('question').all()

    from accounts.models import ExpertProfile
    experts = ExpertProfile.objects.filter(
        is_available=True, is_verified=True
    ).select_related('user')

    # Check if user has accepted the current disclaimer version
    needs_disclaimer = not DisclaimerAcceptance.objects.filter(
        user=request.user,
        version=DisclaimerAcceptance.CURRENT_VERSION,
    ).exists()

    answers_map = {str(a.question_id): a.answer for a in answers}
    readiness = _compute_readiness(answers_map)
    priority_counts = {
        'critical': sum(1 for g in gaps if g.priority == 'critical'),
        'high': sum(1 for g in gaps if g.priority == 'high'),
        'medium': sum(1 for g in gaps if g.priority == 'medium'),
        'low': sum(1 for g in gaps if g.priority == 'low'),
    }
    cost_breakdown = analysis.ai_result.get('cost_breakdown', {}) if analysis.ai_result else {}

    # Progress vs the previous completed analysis for the same target standard
    prev_readiness = None
    readiness_delta = None
    if readiness is not None and analysis.target_standard_id:
        previous = (
            GapAnalysis.objects
            .filter(entrepreneur=request.user, target_standard=analysis.target_standard,
                    status='completed', created_at__lt=analysis.created_at)
            .exclude(pk=analysis.pk)
            .order_by('-created_at')
            .first()
        )
        if previous:
            prev_map = {str(a.question_id): a.answer for a in previous.answers.all()}
            prev_readiness = _compute_readiness(prev_map)
            if prev_readiness is not None:
                readiness_delta = readiness - prev_readiness

    resolved_count = sum(1 for g in gaps if g.is_resolved)
    gaps_total = len(gaps)
    resolved_pct = int(resolved_count / gaps_total * 100) if gaps_total else 0

    # Standart kodini expert filter uchun aniqlash (ISO 9001 → iso9001)
    standard_code_map = {
        'iso 9001': 'iso9001', 'iso9001': 'iso9001',
        'iso 14001': 'iso14001', 'iso14001': 'iso14001',
        'iso 45001': 'iso45001', 'iso45001': 'iso45001',
        'iso 22000': 'iso22000', 'iso22000': 'iso22000',
        'ce marking': 'ce_marking', 'ce': 'ce_marking',
        'gost r': 'gost_r', 'gost': 'gost_r',
        'uzdst': 'uzdst',
    }
    std_name = (analysis.target_standard.code if analysis.target_standard else '').lower().strip()
    expert_standard_filter = standard_code_map.get(std_name, '')

    context = {
        'analysis': analysis,
        'gaps': gaps,
        'answers': answers,
        'experts': experts,
        'summary': analysis.ai_result.get('summary', '') if analysis.ai_result else '',
        'needs_disclaimer': needs_disclaimer,
        'readiness': readiness,
        'prev_readiness': prev_readiness,
        'readiness_delta': readiness_delta,
        'priority_counts': priority_counts,
        'cost_breakdown': cost_breakdown,
        'resolved_count': resolved_count,
        'gaps_total': gaps_total,
        'resolved_pct': resolved_pct,
        'expert_standard_filter': expert_standard_filter,
    }
    return render(request, 'analysis/analysis_detail.html', context)


@login_required
def gap_toggle_resolved(request, pk, gap_pk):
    """AJAX: entrepreneur marks a gap as resolved/unresolved. Turns the static report into a worklist."""
    analysis = get_object_or_404(GapAnalysis, pk=pk, entrepreneur=request.user)
    gap = get_object_or_404(GapItem, pk=gap_pk, analysis=analysis)
    if request.method == 'POST':
        gap.is_resolved = not gap.is_resolved
        gap.save(update_fields=['is_resolved'])
        total = analysis.gaps.count()
        resolved = analysis.gaps.filter(is_resolved=True).count()
        return JsonResponse({
            'is_resolved': gap.is_resolved,
            'resolved': resolved,
            'total': total,
            'pct': int(resolved / total * 100) if total else 0,
        })
    return JsonResponse({'success': False}, status=405)


@login_required
def analysis_print(request, pk):
    """Print-friendly / PDF-export view of the gap analysis report."""
    analysis = get_object_or_404(GapAnalysis, pk=pk, entrepreneur=request.user)
    gaps = analysis.gaps.all()
    priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    gaps = sorted(gaps, key=lambda x: priority_order.get(x.priority, 4))
    answers_map = {str(a.question_id): a.answer for a in analysis.answers.all()}
    roadmap = Roadmap.objects.filter(analysis=analysis).first()
    steps = roadmap.steps.all() if roadmap else []
    return render(request, 'analysis/analysis_print.html', {
        'analysis': analysis,
        'gaps': gaps,
        'roadmap': roadmap,
        'steps': steps,
        'readiness': _compute_readiness(answers_map),
        'summary': analysis.ai_result.get('summary', '') if analysis.ai_result else '',
        'cost_breakdown': analysis.ai_result.get('cost_breakdown', {}) if analysis.ai_result else {},
        'company': request.user,
        'today': timezone.now().date(),
    })


@login_required
def gaps_to_qms(request, pk):
    """Convert this analysis's AI gaps into QMS NonConformity records (links the two modules)."""
    analysis = get_object_or_404(GapAnalysis, pk=pk, entrepreneur=request.user)
    if request.method != 'POST':
        return redirect('analysis_detail', pk=pk)

    from qms.models import NonConformity
    from qms.views import _next_nc_code

    # priority → QMS severity
    severity_map = {'critical': 'critical', 'high': 'major', 'medium': 'minor', 'low': 'minor'}
    gaps = analysis.gaps.all()
    if not gaps:
        messages.error(request, 'Bu tahlilda nomuvofiqlik topilmadi.')
        return redirect('analysis_detail', pk=pk)

    std_code = analysis.target_standard.code if analysis.target_standard else ''
    created = 0
    skipped = 0
    for gap in gaps:
        # Avoid duplicates: same company + same title not already present
        if NonConformity.objects.filter(company=request.user, title=gap.title).exists():
            skipped += 1
            continue
        NonConformity.objects.create(
            company=request.user,
            code=_next_nc_code(request.user),
            title=gap.title,
            description=f"[{std_code} gap-analiz] {gap.description}",
            severity=severity_map.get(gap.priority, 'minor'),
        )
        created += 1

    if created:
        messages.success(request, f'{created} ta nomuvofiqlik QMS ga ko\'chirildi.'
                         + (f' {skipped} ta avval mavjud edi.' if skipped else ''))
    else:
        messages.info(request, 'Barcha nomuvofiqliklar avval QMS ga ko\'chirilgan.')
    return redirect('nonconformities')


@login_required
def accept_disclaimer(request):
    """AJAX-friendly endpoint: record disclaimer acceptance, then redirect back."""
    if request.method == 'POST':
        # Extract real IP (handles reverse proxies)
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
        ip = x_forwarded.split(',')[0].strip() if x_forwarded else request.META.get('REMOTE_ADDR', '')

        DisclaimerAcceptance.objects.get_or_create(
            user=request.user,
            version=DisclaimerAcceptance.CURRENT_VERSION,
            defaults={'ip_address': ip},
        )

        next_url = request.POST.get('next', '')
        # Safety: only allow relative URLs
        if next_url and next_url.startswith('/'):
            return redirect(next_url)
        return redirect('entrepreneur_dashboard')
    return redirect('entrepreneur_dashboard')


@login_required
def roadmap_view(request, pk):
    analysis = get_object_or_404(GapAnalysis, pk=pk, entrepreneur=request.user)
    try:
        roadmap = Roadmap.objects.get(analysis=analysis)
    except Roadmap.DoesNotExist:
        messages.error(request, 'Yo\'l xarita hali tayyor emas. AI tahlil tugashini kuting.')
        return redirect('analysis_detail', pk=pk)
    steps = roadmap.steps.all()

    context = {
        'analysis': analysis,
        'roadmap': roadmap,
        'steps': steps,
        'progress': int((steps.filter(is_completed=True).count() / steps.count() * 100)) if steps.count() > 0 else 0,
    }
    return render(request, 'analysis/roadmap.html', context)
@login_required
def roadmap_step_toggle(request, pk, step_pk):
    analysis = get_object_or_404(GapAnalysis, pk=pk, entrepreneur=request.user)
    step = get_object_or_404(RoadmapStep, pk=step_pk, roadmap__analysis=analysis)

    if request.method == 'POST':
        step.is_completed = not step.is_completed
        step.completed_at = timezone.now() if step.is_completed else None
        step.save()

        roadmap = step.roadmap
        total = roadmap.steps.count()
        completed = roadmap.steps.filter(is_completed=True).count()
        progress = int(completed / total * 100) if total > 0 else 0

        return JsonResponse({
            'is_completed': step.is_completed,
            'progress': progress,
            'completed': completed,
            'total': total,
        })
    return redirect('roadmap', pk=pk)


@login_required
def analysis_delete(request, pk):
    analysis = get_object_or_404(GapAnalysis, pk=pk, entrepreneur=request.user)
    if request.method == 'POST':
        # Guard: prevent deleting analysis that has active (non-cancelled/non-completed) projects
        active_project = analysis.projects.exclude(status__in=['cancelled', 'completed']).first()
        if active_project:
            messages.error(request, 'Bu tahlil uchun faol loyiha mavjud. Avval loyihani yakunlang yoki bekor qiling!')
            return redirect('entrepreneur_dashboard')
        analysis.delete()
        messages.success(request, 'Tahlil o\'chirildi!')
    return redirect('entrepreneur_dashboard')
@login_required
def entrepreneur_projects(request):
    from experts.models import Project
    status_filter = request.GET.get('status', 'negotiating')

    all_projects = Project.objects.filter(
        entrepreneur=request.user
    ).order_by('-created_at')

    negotiating = all_projects.filter(status='negotiating')
    active = all_projects.filter(status__in=['accepted', 'in_progress', 'review'])
    completed = all_projects.filter(status='completed')

    context = {
        'status_filter': status_filter,
        'negotiating': negotiating,
        'active': active,
        'completed': completed,
    }
    return render(request, 'analysis/entrepreneur_projects.html', context)
@login_required
def entrepreneur_wallet(request):
    from experts.models import Payment, Project
    
    projects = Project.objects.filter(
        entrepreneur=request.user
    ).select_related('analysis', 'expert').order_by('-created_at')
    
    payments = Payment.objects.filter(
        entrepreneur=request.user
    ).select_related('project').order_by('-created_at')
    
    total_spent = sum(p.amount for p in payments.filter(status__in=['held', 'released']))
    held = sum(p.amount for p in payments.filter(status='held'))
    released = sum(p.amount for p in payments.filter(status='released'))
    
    return render(request, 'analysis/entrepreneur_wallet.html', {
        'payments': payments,
        'projects': projects,
        'total_spent': total_spent,
        'held': held,
        'released': released,
    })