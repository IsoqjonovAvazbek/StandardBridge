"""analysis ilovasi uchun testlar — loyihaning yuragi (readiness, gap toggle, gaps→QMS, JSON)."""
from django.test import TestCase
from django.urls import reverse
from accounts.models import CustomUser
from .models import GapAnalysis, Standard, Industry, GapItem
from .views import _compute_readiness, _extract_json
from qms.models import NonConformity


class HelperTests(TestCase):
    def test_compute_readiness(self):
        self.assertEqual(_compute_readiness({'1': 'yes', '2': 'no'}), 50)
        self.assertEqual(_compute_readiness({'1': 'yes', '2': 'yes'}), 100)
        self.assertEqual(_compute_readiness({'1': 'no'}), 0)
        self.assertEqual(_compute_readiness({'1': 'partial'}), 50)
        self.assertIsNone(_compute_readiness({}))

    def test_extract_json_fenced(self):
        self.assertEqual(_extract_json('```json\n{"a": 1}\n```'), {'a': 1})

    def test_extract_json_in_prose(self):
        self.assertEqual(_extract_json('Mana natija: {"b": 2} rahmat'), {'b': 2})

    def test_extract_json_invalid_raises(self):
        with self.assertRaises(ValueError):
            _extract_json('hech qanday json yo\'q')


class GapToggleTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='ent', password='p', role='entrepreneur')
        self.other = CustomUser.objects.create_user(username='ent2', password='p', role='entrepreneur')
        ind = Industry.objects.create(name='Test soha')
        std = Standard.objects.create(code='ISO 9001', name='QMS', type='international')
        self.analysis = GapAnalysis.objects.create(
            entrepreneur=self.user, industry=ind, local_standard=std,
            target_standard=std, status='completed', ai_result={'summary': 't'},
        )
        self.gap = GapItem.objects.create(
            analysis=self.analysis, title='Gap', description='d', priority='critical',
        )

    def test_toggle_marks_resolved(self):
        self.client.force_login(self.user)
        resp = self.client.post(
            reverse('gap_toggle_resolved', args=[self.analysis.pk, self.gap.pk])
        )
        self.assertEqual(resp.status_code, 200)
        self.gap.refresh_from_db()
        self.assertTrue(self.gap.is_resolved)
        self.assertEqual(resp.json()['pct'], 100)

    def test_toggle_twice_reverts(self):
        self.client.force_login(self.user)
        url = reverse('gap_toggle_resolved', args=[self.analysis.pk, self.gap.pk])
        self.client.post(url)
        self.client.post(url)
        self.gap.refresh_from_db()
        self.assertFalse(self.gap.is_resolved)

    def test_other_user_cannot_toggle(self):
        self.client.force_login(self.other)
        resp = self.client.post(
            reverse('gap_toggle_resolved', args=[self.analysis.pk, self.gap.pk])
        )
        self.assertEqual(resp.status_code, 404)


class GapsToQmsTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='ent3', password='p', role='entrepreneur', company_name='X MChJ',
        )
        ind = Industry.objects.create(name='Soha')
        std = Standard.objects.create(code='ISO 22000', name='FS', type='international')
        self.analysis = GapAnalysis.objects.create(
            entrepreneur=self.user, industry=ind, local_standard=std,
            target_standard=std, status='completed', ai_result={'summary': 't'},
        )
        GapItem.objects.create(analysis=self.analysis, title='G1', description='d', priority='critical')
        GapItem.objects.create(analysis=self.analysis, title='G2', description='d', priority='medium')

    def test_gaps_copied_to_qms_with_severity_map(self):
        self.client.force_login(self.user)
        self.client.post(reverse('gaps_to_qms', args=[self.analysis.pk]))
        ncs = NonConformity.objects.filter(company=self.user)
        self.assertEqual(ncs.count(), 2)
        self.assertEqual(ncs.get(title='G1').severity, 'critical')  # critical -> critical
        self.assertEqual(ncs.get(title='G2').severity, 'minor')     # medium -> minor

    def test_no_duplicates_on_rerun(self):
        self.client.force_login(self.user)
        url = reverse('gaps_to_qms', args=[self.analysis.pk])
        self.client.post(url)
        self.client.post(url)
        self.assertEqual(NonConformity.objects.filter(company=self.user).count(), 2)
