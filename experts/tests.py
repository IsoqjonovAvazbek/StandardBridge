"""experts ilovasi uchun testlar — hamyon va pul yechish (Decimal bug tuzatilgan joy)."""
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from accounts.models import CustomUser
from analysis.models import GapAnalysis, Standard, Industry, Roadmap, RoadmapStep
from .models import Wallet, WithdrawalRequest, Project, Dispute, Payment


class WalletWithdrawTests(TestCase):
    def setUp(self):
        self.expert = CustomUser.objects.create_user(
            username='exp', password='parol12345', role='expert',
        )
        self.wallet = Wallet.objects.create(user=self.expert, balance=Decimal('500000'))
        self.client.force_login(self.expert)
        self.url = reverse('wallet')

    def test_withdraw_reserves_balance_and_creates_request(self):
        """Pul yechish so'rovi balansni darrov kamaytiradi (rezerv)."""
        self.client.post(self.url, {
            'action': 'withdraw', 'amount': '200000',
            'withdraw_card': '8600123412341234', 'withdraw_holder': 'EXP',
        })
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('300000'))
        self.assertEqual(WithdrawalRequest.objects.filter(wallet=self.wallet).count(), 1)

    def test_withdraw_over_balance_rejected(self):
        """Balansdan ko'p yechib bo'lmaydi (avval Decimal-float crash edi)."""
        self.client.post(self.url, {
            'action': 'withdraw', 'amount': '999999999',
            'withdraw_card': '8600123412341234',
        })
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('500000'))  # o'zgarmadi
        self.assertEqual(WithdrawalRequest.objects.count(), 0)

    def test_withdraw_zero_rejected(self):
        self.client.post(self.url, {
            'action': 'withdraw', 'amount': '0',
            'withdraw_card': '8600123412341234',
        })
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('500000'))

    def test_withdraw_invalid_amount_no_crash(self):
        """Harf kiritilsa crash bo'lmasligi kerak."""
        resp = self.client.post(self.url, {
            'action': 'withdraw', 'amount': 'abc',
            'withdraw_card': '8600123412341234',
        })
        self.assertIn(resp.status_code, (200, 302))
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('500000'))

    def test_withdraw_no_card_rejected(self):
        self.client.post(self.url, {'action': 'withdraw', 'amount': '100000', 'withdraw_card': ''})
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('500000'))


class WithdrawalAdminTests(TestCase):
    def setUp(self):
        self.expert = CustomUser.objects.create_user(username='exp2', password='p', role='expert')
        self.admin = CustomUser.objects.create_user(
            username='adm', password='p', role='admin', is_staff=True, is_superuser=True,
        )
        self.wallet = Wallet.objects.create(user=self.expert, balance=Decimal('300000'))
        self.wr = WithdrawalRequest.objects.create(
            wallet=self.wallet, amount=Decimal('200000'), card_number='8600000011112222',
        )

    def test_reject_refunds_balance(self):
        """Rad etilgan so'rov pulni hamyonga qaytaradi."""
        self.client.force_login(self.admin)
        self.client.post(
            reverse('admin_process_withdrawal', args=[self.wr.pk]),
            {'action': 'reject', 'admin_note': 'test'},
        )
        self.wallet.refresh_from_db()
        self.wr.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('500000'))
        self.assertEqual(self.wr.status, 'rejected')

    def test_approve_keeps_balance(self):
        """Tasdiqlangan so'rov balansni o'zgartirmaydi (allaqachon rezervda)."""
        self.client.force_login(self.admin)
        self.client.post(
            reverse('admin_process_withdrawal', args=[self.wr.pk]),
            {'action': 'approve'},
        )
        self.wallet.refresh_from_db()
        self.wr.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('300000'))
        self.assertEqual(self.wr.status, 'approved')


class ProjectLifecycleTests(TestCase):
    """Loyiha biznes-mantiq qoidalari (revision, dispute, guard'lar)."""

    def setUp(self):
        self.ent = CustomUser.objects.create_user(username='ent', password='p', role='entrepreneur')
        self.exp = CustomUser.objects.create_user(username='exp', password='p', role='expert')
        ind = Industry.objects.create(name='Soha')
        std = Standard.objects.create(code='ISO 9001', name='QMS', type='international')
        self.analysis = GapAnalysis.objects.create(
            entrepreneur=self.ent, industry=ind, local_standard=std,
            target_standard=std, status='completed', ai_result={'s': 1},
        )

    def _project(self, status='in_progress'):
        return Project.objects.create(
            analysis=self.analysis, entrepreneur=self.ent, expert=self.exp, status=status,
        )

    def test_expert_cannot_complete_without_progress(self):
        """Roadmap bor, hech qadam bajarilmagan — yakunlab bo'lmaydi."""
        p = self._project()
        rm = Roadmap.objects.create(analysis=self.analysis, total_days=10)
        RoadmapStep.objects.create(roadmap=rm, title='Q1', order=1, duration_days=5)
        self.client.force_login(self.exp)
        self.client.post(reverse('project_complete', args=[p.pk]))
        p.refresh_from_db()
        self.assertEqual(p.status, 'in_progress')  # yakunlanmadi

    def test_expert_can_complete_after_progress(self):
        p = self._project()
        rm = Roadmap.objects.create(analysis=self.analysis, total_days=10)
        s = RoadmapStep.objects.create(roadmap=rm, title='Q1', order=1, duration_days=5, is_completed=True)
        self.client.force_login(self.exp)
        self.client.post(reverse('project_complete', args=[p.pk]))
        p.refresh_from_db()
        self.assertEqual(p.status, 'review')

    def test_entrepreneur_request_revision(self):
        """review -> in_progress qaytaradi (sabab bilan)."""
        p = self._project('review')
        self.client.force_login(self.ent)
        self.client.post(reverse('project_request_revision', args=[p.pk]), {'reason': 'Hujjat yetishmaydi'})
        p.refresh_from_db()
        self.assertEqual(p.status, 'in_progress')

    def test_revision_requires_reason(self):
        p = self._project('review')
        self.client.force_login(self.ent)
        self.client.post(reverse('project_request_revision', args=[p.pk]), {'reason': ''})
        p.refresh_from_db()
        self.assertEqual(p.status, 'review')  # sababsiz — qaytmaydi

    def test_open_dispute_blocks_payment_release(self):
        """Ochiq nizo bo'lsa pul release bo'lmaydi."""
        p = self._project('review')
        Payment.objects.create(project=p, entrepreneur=self.ent, amount=Decimal('1000'), status='held')
        Dispute.objects.create(project=p, opened_by=self.ent, reason='sifatsiz')
        self.client.force_login(self.ent)
        self.client.post(reverse('payment_release', args=[p.pk]))
        p.refresh_from_db()
        self.assertEqual(p.status, 'review')  # completed bo'lmadi

    def test_cannot_change_price_after_payment(self):
        """To'langan (in_progress) loyiha narxini o'zgartirib bo'lmaydi."""
        p = self._project('in_progress')
        self.client.force_login(self.exp)
        self.client.post(reverse('project_set_price', args=[p.pk]), {'price': '500', 'days': '10'})
        p.refresh_from_db()
        self.assertEqual(p.status, 'in_progress')  # negotiating ga qaytmadi

    def test_set_price_rejects_invalid_input(self):
        """Harf/bo'sh narx crash bermaydi."""
        p = self._project('pending')
        self.client.force_login(self.exp)
        resp = self.client.post(reverse('project_set_price', args=[p.pk]), {'price': 'abc', 'days': 'xyz'})
        self.assertIn(resp.status_code, (200, 302))
        p.refresh_from_db()
        self.assertEqual(p.status, 'pending')  # o'zgarmadi
