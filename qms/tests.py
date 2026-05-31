"""qms ilovasi uchun testlar — NC kod, eksport, overdue, silent-fail tuzatish."""
from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from accounts.models import CustomUser
from .models import NonConformity, AuditSchedule, QMSDocument


class NonConformityTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='qmsuser', password='p', role='entrepreneur', company_name='Test MChJ',
        )
        self.client.force_login(self.user)

    def test_add_nc_generates_code(self):
        self.client.post(reverse('add_nonconformity'), {
            'title': 'Hujjat nazorati yo\'q', 'description': 'tavsif', 'severity': 'major',
        })
        nc = NonConformity.objects.get(company=self.user)
        self.assertTrue(nc.code.startswith('NC-'))

    def test_nc_codes_increment(self):
        for i in range(3):
            self.client.post(reverse('add_nonconformity'), {
                'title': f'NC {i}', 'description': 'd', 'severity': 'minor',
            })
        codes = list(NonConformity.objects.filter(company=self.user).values_list('code', flat=True))
        self.assertEqual(len(set(codes)), 3)  # hammasi noyob

    def test_empty_nc_rejected_no_crash(self):
        """Silent-fail tuzatildi: bo'sh forma NC yaratmaydi, lekin crash ham yo'q."""
        resp = self.client.post(reverse('add_nonconformity'), {'title': '', 'description': ''})
        self.assertIn(resp.status_code, (200, 302))
        self.assertEqual(NonConformity.objects.count(), 0)

    def test_overdue_property(self):
        nc = NonConformity.objects.create(
            company=self.user, title='t', description='d', severity='minor',
            status='open', due_date=timezone.now().date() - timedelta(days=2),
        )
        self.assertTrue(nc.is_overdue)
        nc.status = 'closed'
        self.assertFalse(nc.is_overdue)

    def test_export_nc_csv(self):
        NonConformity.objects.create(
            company=self.user, code='NC-2026-001', title='t', description='d', severity='major',
        )
        resp = self.client.get(reverse('export_nc_csv'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('text/csv', resp['Content-Type'])


class AuditScheduleTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='qa', password='p', role='entrepreneur')
        self.client.force_login(self.user)

    def test_audit_overdue_property(self):
        a = AuditSchedule.objects.create(
            company=self.user, audit_type='internal', standard='ISO 9001',
            planned_date=timezone.now().date() - timedelta(days=5), status='planned',
        )
        self.assertTrue(a.is_overdue)

    def test_empty_audit_rejected(self):
        resp = self.client.post(reverse('add_audit'), {'audit_type': '', 'standard': '', 'planned_date': ''})
        self.assertIn(resp.status_code, (200, 302))
        self.assertEqual(AuditSchedule.objects.count(), 0)


class DocumentExpiryTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='doc', password='p', role='entrepreneur')

    def test_is_expired_and_days_to_expiry(self):
        doc = QMSDocument(
            company=self.user, title='Sert', doc_type='certificate',
            expiry_date=timezone.now().date() - timedelta(days=1),
        )
        self.assertTrue(doc.is_expired)
        self.assertLess(doc.days_to_expiry, 0)
