"""expert_tools testlari — tahlil↔audit integratsiyasi (audit_from_analysis)."""
from django.test import TestCase
from django.urls import reverse
from accounts.models import CustomUser
from analysis.models import GapAnalysis, Standard, Industry, GapItem
from experts.models import Project
from .models import AuditChecklist, AuditChecklistItem


class AuditFromAnalysisTests(TestCase):
    def setUp(self):
        self.expert = CustomUser.objects.create_user(username='exp', password='p', role='expert')
        self.ent = CustomUser.objects.create_user(
            username='ent', password='p', role='entrepreneur', company_name='Oziq MChJ',
        )
        ind = Industry.objects.create(name='Oziq-ovqat')
        self.std = Standard.objects.create(code='ISO 22000', name='FS', type='international')
        self.analysis = GapAnalysis.objects.create(
            entrepreneur=self.ent, industry=ind, local_standard=self.std,
            target_standard=self.std, status='completed', ai_result={'summary': 't'},
        )
        GapItem.objects.create(analysis=self.analysis, title='Hujjat nazorati', description='d1', priority='critical')
        GapItem.objects.create(analysis=self.analysis, title='HACCP rejasi', description='d2', priority='medium')
        self.project = Project.objects.create(
            analysis=self.analysis, entrepreneur=self.ent, expert=self.expert, status='in_progress',
        )

    def test_creates_audit_from_gaps(self):
        self.client.force_login(self.expert)
        self.client.post(reverse('audit_from_analysis', args=[self.project.pk]))
        audit = AuditChecklist.objects.get(project=self.project)
        self.assertEqual(audit.standard, 'iso22000')  # ISO 22000 -> iso22000
        items = AuditChecklistItem.objects.filter(checklist=audit)
        self.assertEqual(items.count(), 2)
        # har band non_compliant + finding bilan
        for it in items:
            self.assertEqual(it.status, 'non_compliant')
            self.assertTrue(it.finding)

    def test_critical_gap_ordered_first(self):
        self.client.force_login(self.expert)
        self.client.post(reverse('audit_from_analysis', args=[self.project.pk]))
        audit = AuditChecklist.objects.get(project=self.project)
        first = AuditChecklistItem.objects.filter(checklist=audit).order_by('order').first()
        self.assertEqual(first.question, 'Hujjat nazorati')  # critical birinchi

    def test_other_expert_cannot_access_project(self):
        other = CustomUser.objects.create_user(username='exp2', password='p', role='expert')
        self.client.force_login(other)
        resp = self.client.post(reverse('audit_from_analysis', args=[self.project.pk]))
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(AuditChecklist.objects.count(), 0)
