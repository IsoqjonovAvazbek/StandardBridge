from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from django.db.models import Sum, Q
from .models import GapAnalysis, Standard, GapItem, Roadmap, RoadmapStep, Industry, Question, QuestionAnswer, DisclaimerAcceptance
from experts.models import Project, Notification, Payment
from core.translations import notif_text as _nl
from decimal import Decimal
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


def _sanitize_ai_description(text):
    """AI hallucination filteri.

    Quyidagi holatlarni tozalaydi:
    - Bo'sh yoki juda qisqa (<25 belgi)
    - URL yoki email — AI ixtiro qilgan ehtimol
    - Telefon raqami — ishonchsiz
    - Juda uzun (>450 belgi) — qisqartiradi
    """
    import re
    if not text or len(text.strip()) < 15:
        return ''
    text = text.strip()
    if re.search(r'https?://|www\.', text, re.IGNORECASE):
        return ''
    if re.search(r'[\w.+-]+@[\w-]+\.\w{2,}', text):
        return ''
    if re.search(r'\+\d{7,}|\b\d{9,}\b', text):
        return ''
    return text[:450] if len(text) > 450 else text


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


def get_ai_analysis(local_standards, target_standards, industry_name,
                    weak_answers, db_weak_questions=None,
                    company_context='', readiness=None, language='uz'):
    """Gap tahlil qiladi.

    Arxitektura — aniqlik uchun:
    - GAP NOMI: DB'dan (Question.text) — AI ixtiro qilmaydi
    - GAP PRIORITET: javob va clause bo'yicha hisoblangan
    - AI ROLI: har gap uchun 2-3 jumla izoh + roadmap qadamlari
    """
    from decimal import Decimal

    # ── 1. GAP'LARNI BAZADAN QURISH ──────────────────────────────────────────
    # Agar db_weak_questions bo'lsa (yangi oqim), gaplarni bazadan quramiz
    if db_weak_questions:
        def _priority_from_clause(clause, answer):
            """Clause va javob bo'yicha prioritet."""
            clause_lower = (clause or '').lower()
            if answer == 'no':
                # Rahbariyat, siyosat, qonuniy talablar → critical
                if any(k in clause_lower for k in ['policy', 'leadership', 'legal', 'management', '5.1', '5.2', '6.1']):
                    return 'critical'
                return 'high'
            else:  # partial
                if any(k in clause_lower for k in ['audit', 'review', 'monitoring']):
                    return 'medium'
                return 'medium'

        structured_gaps = []
        for question, answer in db_weak_questions:
            priority = _priority_from_clause(question.help_text, answer)
            structured_gaps.append({
                'title': question.text,           # DB'dan — o'zgarmas
                'clause': question.help_text or '',
                'standard': question.standard.code if question.standard else '',
                'answer': 'Yo\'q' if answer == 'no' else 'Qisman',
                'priority': priority,
            })
    else:
        structured_gaps = []

    lang_rule = AI_LANG_INSTRUCTION.get(language, AI_LANG_INSTRUCTION['uz'])
    context_block = f"Korxona ma'lumotlari:\n{company_context}\n" if company_context else ""
    readiness_block = f"Korxonaning hozirgi tayyorlik darajasi: {readiness}%\n" if readiness is not None else ""

    local_codes = ', '.join([s.code for s in local_standards])
    target_codes = ', '.join([s.code for s in target_standards])

    # Standart tavsiflarini bazadan olish
    target_descs = []
    for s in target_standards:
        if s.description:
            target_descs.append(f"- {s.code}: {s.description[:300]}")
    std_context = "\n".join(target_descs) if target_descs else ""

    # ── 2. ROADMAP QADAMLARINI BAZADAN OLISH (promptdan oldin) ───────────────
    from analysis.models import StandardRoadmapStep
    db_roadmap_steps = []
    for std in target_standards:
        steps = StandardRoadmapStep.objects.filter(
            standard=std, is_active=True
        ).order_by('order')
        if steps.exists():
            db_roadmap_steps = list(steps)
            break

    has_db_roadmap = len(db_roadmap_steps) > 0 and language == 'uz'

    # ── 3. AI PROMPTI — FAQAT IZOH VA SUMMARY ────────────────────────────────
    if structured_gaps:
        gaps_for_ai = "\n".join([
            f"{i+1}. [{g['standard']}] {g['clause']}\n   Savol: {g['title']}\n   Javob: {g['answer']}"
            for i, g in enumerate(structured_gaps)
        ])

        if has_db_roadmap:
            roadmap_json_block = ""
            roadmap_rule = "- roadmap_steps ni YOZMA — bazadan keladi, sen tegma"
        else:
            roadmap_json_block = """,
  "roadmap_steps": [
    {{
      "order": 1,
      "title": "Qadam nomi",
      "description": "Nima qilinadi, qaysi hujjat, natija",
      "deliverables": ["Hujjat 1", "Hujjat 2"],
      "duration_days": 14
    }}
  ]"""
            roadmap_rule = "- roadmap_steps: 4-7 ta aniq bosqich"

        prompt = f"""Sen {target_codes} standarti bo'yicha sertifikatlash mutaxassisisisan.
Korxona quyidagi talablarga javob bermagan. Har bir gap uchun FAQAT standart talabi asosida izoh yoz.

Soha: {industry_name} | Standart: {target_codes}
{readiness_block}{context_block}

ANIQLANGAN GAP'LAR:
{gaps_for_ai}

{lang_rule}

QATTIQ CHEKLASHLAR (buzma):
1. Har bir description: 2-3 jumla, faqat standart talabi haqida
2. URL, email, telefon, kompaniya nomi YOZMA
3. Aniq narx, muddatni (3 oy, 2 yil) da'vo qilma
4. Yangi gap ixtiro qilma — faqat yuqoridagi ro'yxatga izoh
5. "Mutaxassis bilan maslahatlashing" — oxirgi jumlada yozishing MUMKIN

JSON (faqat bu, boshqa hech narsa):
{{
  "gap_descriptions": [
    {{
      "index": 1,
      "description": "Standart talabi nimani talab qiladi va bu talabni qondirish uchun nima qilish kerak — 2-3 jumla"
    }}
  ],
  "summary": "Umumiy holat — 2 jumla, da'vosiz"
}}

QOIDALAR:
- gap_descriptions soni: {len(structured_gaps)} ta (aniqlangan gaplar soni)
- estimated_cost, total_days, roadmap_steps YOZMA — bular alohida hisoblanadi
- {roadmap_rule}"""

    else:
        # Gap yo'q — korxona yaxshi holatda
        weak_text = '\n'.join([f"- {q}: {a}" for q, a in weak_answers]) if weak_answers else "Barcha savollarga ijobiy javob berildi"

        if has_db_roadmap:
            roadmap_json_block = ""
            roadmap_note = ""
        else:
            roadmap_json_block = """,
  "roadmap_steps": [
    {{
      "order": 1,
      "title": "Hujjatlarni tekshirish",
      "description": "Mavjud hujjatlarni standart talablariga muvofiqligini tekshirish",
      "deliverables": ["Tekshiruv hisoboti"],
      "duration_days": 14
    }}
  ]"""
            roadmap_note = ""

        prompt = f"""Sen sertifikatlash bo'yicha maslahatchi.

Soha: {industry_name}, Maqsad: {target_codes}
{readiness_block}{context_block}
Holat: {weak_text}

{lang_rule}

JSON:
{{
  "gap_descriptions": [],
  "total_days": 30,
  "estimated_cost": 1000,
  "cost_breakdown": {{"consulting": 700, "certification_body": 300}}{roadmap_json_block},
  "summary": "Korxona yaxshi holatda. Audit tayyor."
}}"""

    client = Groq(api_key=settings.GROQ_API_KEY, timeout=settings.AI_TIMEOUT, max_retries=1)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=2500,
    )
    ai_data = _extract_json(response.choices[0].message.content)

    # ── 5. GAP NOMLARINI BAZADAN OLIB, AI IZOHINI QO'SHISH ───────────────────
    if structured_gaps:
        desc_map = {}
        for item in ai_data.get('gap_descriptions', []):
            idx = item.get('index', 0)
            if 1 <= idx <= len(structured_gaps):
                desc_map[idx] = item

        final_gaps = []
        total_days_calc = 0
        for i, gap in enumerate(structured_gaps, start=1):
            ai_item = desc_map.get(i, {})
            estimated_days = ai_item.get('estimated_days', 14 if gap['answer'] == 'Qisman' else 21)
            total_days_calc += estimated_days
            raw_desc = ai_item.get('description', '')
            final_gaps.append({
                'title': gap['title'],           # ← DB'dan, o'zgarmas
                'description': _sanitize_ai_description(raw_desc),
                'clause': gap.get('clause', ''), # ← DB'dan, standart bo'limi
                'priority': gap['priority'],     # ← DB'dan hisoblangan
                'estimated_days': estimated_days,
            })

        ai_data['gaps'] = final_gaps
        ai_data['total_days'] = ai_data.get('total_days') or total_days_calc
    else:
        ai_data['gaps'] = []

    # ── 6. ROADMAP DB'DAN (AI TEGMAYDI) ──────────────────────────────────────
    if has_db_roadmap:
        ai_data['roadmap_steps'] = [
            {
                'order': step.order,
                'title': step.title,                  # ← DB'dan, o'zgarmas
                'description': step.description,     # ← DB'dan, o'zgarmas
                'deliverables': step.deliverables,   # ← DB'dan, o'zgarmas
                'duration_days': step.duration_days, # ← DB'dan, o'zgarmas
            }
            for step in db_roadmap_steps
        ]
        ai_data['total_days'] = ai_data.get('total_days') or sum(
            s.duration_days for s in db_roadmap_steps
        )

    return ai_data


@login_required
def entrepreneur_dashboard(request):
    if request.user.is_expert():
        return redirect('expert_dashboard')
    from experts.models import Project

    all_projects = Project.objects.filter(
        entrepreneur=request.user
    ).select_related(
        'expert', 'analysis__local_standard', 'analysis__target_standard'
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
    ).prefetch_related('gaps').order_by('-created_at')

    pending_projects = all_projects.filter(status='pending')
    negotiating_projects = all_projects.filter(status='negotiating')
    active_projects = all_projects.filter(status__in=['accepted', 'in_progress', 'review'])
    completed_projects = all_projects.filter(status='completed')

    # F-8: AI xato yoki pending tahlillarni ko'rsatish
    pending_analyses = GapAnalysis.objects.filter(
        entrepreneur=request.user,
        status__in=['pending', 'in_progress'],
    ).order_by('-created_at')

    # Readiness trend grafigi uchun (oxirgi 6 ta completed tahlil, eskidan yangi tartibda)
    trend_analyses = list(
        GapAnalysis.objects.filter(entrepreneur=request.user, status='completed')
        .select_related('target_standard')
        .prefetch_related('answers')
        .order_by('created_at')[:6]
    )
    readiness_trend = []
    for a in trend_analyses:
        answers_map = {str(ans.question_id): ans.answer for ans in a.answers.all()}
        r = _compute_readiness(answers_map)
        readiness_trend.append({
            'label': f"{a.target_standard.code if a.target_standard else '#'+str(a.pk)} ({a.created_at.strftime('%d.%m')})",
            'value': r if r is not None else 0,
        })

    import json
    context = {
        'analyses': analyses,
        'pending_analyses': pending_analyses,
        'project_analysis_ids': project_analysis_ids,
        'total': analyses.count(),
        'pending_projects': pending_projects,
        'negotiating_projects': negotiating_projects,
        'active_projects': active_projects,
        'completed_projects': completed_projects,
        'readiness_trend_json': json.dumps(readiness_trend),
        'show_trend': len(readiness_trend) >= 2,
    }
    return render(request, 'analysis/entrepreneur_dashboard.html', context)
@login_required
def select_industry(request):
    lang = request.session.get('lang', 'uz')
    industries = list(Industry.objects.filter(is_active=True))
    for ind in industries:
        ind.display_name = ind.get_name(lang)
        ind.display_description = ind.get_description(lang)
    return render(request, 'analysis/select_industry.html', {'industries': industries})


@login_required
def select_standards(request, industry_id):
    from django.db.models import Q
    lang = request.session.get('lang', 'uz')
    industry = get_object_or_404(Industry, pk=industry_id)
    industry.display_name = industry.get_name(lang)

    # Universal ("Ko'p soha") standartlarni ham qo'shish
    universal = Industry.objects.filter(name__icontains='universal').first()
    local_q = Q(type='local', is_active=True, industry=industry)
    if universal and universal != industry:
        local_q |= Q(type='local', is_active=True, industry=universal)
    local_standards = list(Standard.objects.filter(local_q).order_by('code'))

    intl_q = Q(type='international', is_active=True, industry=industry)
    if universal and universal != industry:
        intl_q |= Q(type='international', is_active=True, industry=universal)
    target_standards = list(Standard.objects.filter(intl_q).order_by('code'))

    for std in local_standards + target_standards:
        std.display_name = std.get_name(lang)
        std.display_description = std.get_description(lang)

    if request.method == 'POST':
        local_ids = request.POST.getlist('local_standards')
        target_ids = request.POST.getlist('target_standards')

        valid_local_pks = set(s.pk for s in local_standards)
        valid_target_pks = set(s.pk for s in target_standards)
        local_ids = [i for i in local_ids if i.isdigit() and int(i) in valid_local_pks]
        target_ids = [i for i in target_ids if i.isdigit() and int(i) in valid_target_pks]

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
    lang = request.session.get('lang', 'uz')
    industry = get_object_or_404(Industry, pk=industry_id)
    industry.display_name = industry.get_name(lang)
    target_ids = request.session.get('target_ids', [])

    target_standards = list(Standard.objects.filter(pk__in=target_ids))
    questions = list(Question.objects.filter(
        standard__in=target_standards,
        is_active=True
    ).select_related('standard'))

    # UzDST/GOST standartlar uchun fallback: ISO kalit raqamiga qarab tegishli ISO savollarni olish
    if not questions:
        ISO_CODE_MAP = {
            '9001': '9001', '14001': '14001', '45001': '45001',
            '22000': '22000', '27001': '27001', '50001': '50001',
        }
        fallback_codes = []
        for std in target_standards:
            for key in ISO_CODE_MAP:
                if key in std.code:
                    iso_std = Standard.objects.filter(
                        code__icontains=f'ISO {key}', type='international'
                    ).first()
                    if iso_std:
                        fallback_codes.append(iso_std.pk)
        if fallback_codes:
            questions = list(Question.objects.filter(
                standard__pk__in=fallback_codes, is_active=True
            ).select_related('standard'))

    if not questions:
        messages.warning(request, 'Bu standart uchun savollar hali tayyor emas. Boshqa standart tanlang yoki admin bilan bog\'laning.')
        return redirect('select_industry')

    for std in target_standards:
        std.display_name = std.get_name(lang)
    for q in questions:
        q.display_text = q.get_text(lang)
        q.display_help = q.get_help(lang)

    if request.method == 'POST':
        answers = {
            str(question.pk): request.POST.get(f'question_{question.pk}', 'no')
            for question in questions
        }
        request.session['question_answers'] = answers
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
                        company_context='', readiness=None, language='uz',
                        weak_question_ids=None):
    """AI tahlilni background threadda bajaradi.

    Arxitektura:
    - Gap nomlari → DB'dan (Question.text) — hech qachon AI to'qimaydi
    - Gap prioritet → javob turiga qarab (no=yuqori, partial=o'rta)
    - AI roli → faqat qisqa izoh va roadmap yozish
    """
    import django
    django.db.close_old_connections()
    try:
        analysis = GapAnalysis.objects.get(pk=analysis_id)
        local_standards = Standard.objects.filter(pk__in=local_ids)
        target_standards = Standard.objects.filter(pk__in=target_ids)

        # Zaif savollarga mos Question obyektlarini bazadan olamiz
        db_weak_questions = []
        if weak_question_ids:
            for q_id, answer in weak_question_ids:
                try:
                    q = Question.objects.select_related('standard').get(pk=q_id)
                    db_weak_questions.append((q, answer))
                except Question.DoesNotExist:
                    pass

        ai_result = get_ai_analysis(
            local_standards, target_standards, industry_name,
            weak_answers, db_weak_questions,
            company_context=company_context, readiness=readiness, language=language,
        )

        if readiness is not None:
            ai_result['readiness'] = readiness
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
                clause=gap_data.get('clause', '')[:100],
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

        # Remove pending (unassigned) projects — but NOT projects whose expert was later deleted
        Project.objects.filter(analysis=analysis, expert__isnull=True, status='pending').delete()

        # Tahlil tayyor — tadbirkorga email yuborish
        try:
            from experts.emails import send_analysis_ready_email
            send_analysis_ready_email(analysis)
        except Exception:
            pass  # Email xatosi asosiy jarayonni to'xtatmasin

    except Exception as e:
        logger.exception('AI tahlil xatosi (analysis_id=%s): %s', analysis_id, e)
        try:
            analysis = GapAnalysis.objects.get(pk=analysis_id)
            analysis.status = 'pending'
            analysis.ai_result = {'error': str(e)}
            analysis.save()
            # F-8: AI xato bo'lganda foydalanuvchiga notification
            from experts.models import Notification
            Notification.objects.create(
                user=analysis.entrepreneur,
                title=_nl(analysis.entrepreneur, 'AI tahlil xatosi', 'Ошибка AI анализа', 'AI analysis error'),
                message=_nl(analysis.entrepreneur,
                    f'Tahlil #{analysis.pk} ishlov berishda xatolik yuz berdi. Sahifaga kirib qayta urining.',
                    f'При обработке анализа #{analysis.pk} произошла ошибка. Попробуйте снова.',
                    f'Analysis #{analysis.pk} encountered an error. Please retry.'),
                link=f'/analysis/{analysis.pk}/processing/',
            )
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

    if not question_answers:
        return redirect('answer_questions', industry_id=industry_id)

    local_standards = Standard.objects.filter(pk__in=local_ids)
    target_standards = Standard.objects.filter(pk__in=target_ids)

    # Zaif javoblarni Question ID bilan birga saqlaymiz (baza birlamchi manba uchun)
    weak_answers = []
    weak_question_ids = []
    for q_id, answer in question_answers.items():
        if answer in ['no', 'partial']:
            try:
                question = Question.objects.get(pk=int(q_id))
                weak_answers.append((question.text, 'Yo\'q' if answer == 'no' else 'Qisman'))
                weak_question_ids.append((int(q_id), answer))
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
        language=language,
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
        args=(analysis.pk, list(local_ids), list(target_ids), industry.name,
              weak_answers, company_context, readiness, language, weak_question_ids),
        daemon=True,
    )
    thread.start()

    return redirect('analysis_processing', pk=analysis.pk)


def _sanitize_for_prompt(text: str, max_len: int = 200) -> str:
    """Strip prompt-injection markers from user-supplied text before embedding in AI prompt."""
    import re
    import unicodedata
    # Unicode normalizatsiya — unicode trick bilan bypass'ni oldini oladi
    text = unicodedata.normalize('NFKD', str(text).strip())
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = text[:max_len]
    # Remove common injection markers including variations with spaces/chars between letters
    text = re.sub(
        r'(?i)\b(ignore|forget|disregard|override|jailbreak|dan\s*mode|system\s*prompt)\b',
        '[filtered]', text
    )
    text = re.sub(r'(?i)(#{2,}|={2,}|-{2,}|system\s*:)', '', text)
    # Collapse newlines so user can't inject multi-line instructions
    text = ' '.join(text.splitlines())
    return text.strip()


def _build_company_context(user, ctx):
    """Build a human-readable company context block from profile + form input."""
    parts = []
    if user.company_name:
        parts.append(f"Korxona: {_sanitize_for_prompt(user.company_name)}")
    if ctx.get('employee_count'):
        parts.append(f"Xodimlar soni: {ctx['employee_count']}")
    if ctx.get('current_state'):
        parts.append(f"Hozirgi holat: {_sanitize_for_prompt(ctx['current_state'])}")
    if ctx.get('export_markets'):
        parts.append(f"Eksport bozorlari: {_sanitize_for_prompt(ctx['export_markets'])}")
    if ctx.get('existing_certs'):
        parts.append(f"Mavjud sertifikatlar: {_sanitize_for_prompt(ctx['existing_certs'])}")
    return '\n'.join(parts)


def _relaunch_analysis(analysis):
    """Re-run the AI task for an existing analysis using its saved data (for retry)."""
    answers = {str(a.question_id): a.answer for a in analysis.answers.all()}
    weak_answers = []
    weak_question_ids = []
    for a in analysis.answers.select_related('question').all():
        if a.answer in ('no', 'partial'):
            weak_answers.append((a.question.text, 'Yo\'q' if a.answer == 'no' else 'Qisman'))
            weak_question_ids.append((a.question_id, a.answer))
    readiness = _compute_readiness(answers)
    local_ids = [analysis.local_standard_id] if analysis.local_standard_id else []
    target_ids = [analysis.target_standard_id] if analysis.target_standard_id else []
    industry_name = analysis.industry.name if analysis.industry else 'Umumiy'
    language = analysis.language or 'uz'

    analysis.status = 'in_progress'
    analysis.ai_result = None
    analysis.save(update_fields=['status', 'ai_result'])
    analysis.gaps.all().delete()
    Roadmap.objects.filter(analysis=analysis).delete()

    thread = threading.Thread(
        target=_ai_background_task,
        args=(analysis.pk, local_ids, target_ids, industry_name, weak_answers,
              analysis.company_info or '', readiness, language, weak_question_ids),
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
def analysis_retake(request, pk):
    """Start a brand-new analysis pre-filled with the same industry + standards."""
    old = get_object_or_404(GapAnalysis, pk=pk, entrepreneur=request.user)
    if not old.industry or not old.target_standard:
        return redirect('select_industry')
    request.session['target_ids'] = [old.target_standard.pk]
    if old.local_standard:
        request.session['local_ids'] = [old.local_standard.pk]
    else:
        request.session.pop('local_ids', None)  # eski sessiya qoldig'ini tozalash
    request.session.pop('question_answers', None)
    request.session.modified = True
    return redirect('answer_questions', industry_id=old.industry.pk)


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
    # Standartga mos top-3 ekspert (specializations ichida standart kodi bor)
    std_code = (analysis.target_standard.code if analysis.target_standard else '').strip()
    matched_experts = ExpertProfile.objects.filter(
        is_available=True, is_verified=True,
        specializations__icontains=std_code.split()[0] if std_code else 'ISO',
    ).select_related('user').order_by('-rating')[:3]
    # Agar mos ekspert kam bo'lsa, rating bo'yicha to'ldiramiz
    if matched_experts.count() < 3:
        matched_experts = ExpertProfile.objects.filter(
            is_available=True, is_verified=True,
        ).select_related('user').order_by('-rating')[:3]

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

    # Gap prioritetiga qarab narx va muddat taxmini
    cost_per_gap = {'critical': 400, 'high': 250, 'medium': 150, 'low': 80}
    days_per_gap  = {'critical': 30,  'high': 21,  'medium': 14,  'low': 7}
    smart_cost = sum(cost_per_gap.get(g.priority, 150) for g in gaps)
    smart_days = sum(days_per_gap.get(g.priority, 14) for g in gaps)
    # Boshlang'ich xarajat (consulting + sertifikatsiya organi)
    smart_cost_min = int(smart_cost * 0.8)
    smart_cost_max = int(smart_cost * 1.3)

    # Sertifikatlash sanasi taxmini
    from datetime import date, timedelta
    cert_date = (date.today() + timedelta(days=smart_days)).strftime('%d.%m.%Y') if smart_days else None

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
        'experts': matched_experts,
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
        'matched_experts': matched_experts,
        'smart_cost_min': smart_cost_min,
        'smart_cost_max': smart_cost_max,
        'smart_days': smart_days,
        'cert_date': cert_date,
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
        from django.db.models import Count, Q as _Q
        agg = analysis.gaps.aggregate(
            total=Count('id'),
            resolved=Count('id', filter=_Q(is_resolved=True))
        )
        total, resolved = agg['total'], agg['resolved']
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
    """Record disclaimer acceptance. Returns JSON for AJAX calls, redirect for regular forms."""
    if request.method != 'POST':
        return redirect('entrepreneur_dashboard')

    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    ip = x_forwarded.split(',')[0].strip() if x_forwarded else request.META.get('REMOTE_ADDR', '')

    DisclaimerAcceptance.objects.get_or_create(
        user=request.user,
        version=DisclaimerAcceptance.CURRENT_VERSION,
        defaults={'ip_address': ip},
    )

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.http import JsonResponse as _JR
        return _JR({'status': 'ok'})

    next_url = request.POST.get('next', '')
    if next_url and next_url.startswith('/') and not next_url.startswith('//'):
        return redirect(next_url)
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
        'progress': int(steps.filter(is_completed=True).count() / steps.count() * 100) if steps.exists() else 0,
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
            'order': step.order,
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
    ).select_related(
        'analysis__local_standard', 'analysis__target_standard', 'expert'
    ).prefetch_related('analysis__gaps', 'updates').order_by('-created_at')

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
    projects = Project.objects.filter(
        entrepreneur=request.user
    ).select_related('analysis', 'expert').order_by('-created_at')
    
    payments = Payment.objects.filter(
        entrepreneur=request.user
    ).select_related('project').order_by('-created_at')

    totals = Payment.objects.filter(entrepreneur=request.user).aggregate(
        total_spent=Sum('amount', filter=Q(status__in=['held', 'released'])),
        held=Sum('amount', filter=Q(status='held')),
        released=Sum('amount', filter=Q(status='released')),
    )
    total_spent = totals['total_spent'] or Decimal('0')
    held = totals['held'] or Decimal('0')
    released = totals['released'] or Decimal('0')
    
    return render(request, 'analysis/entrepreneur_wallet.html', {
        'payments': payments,
        'projects': projects,
        'total_spent': total_spent,
        'held': held,
        'released': released,
    })