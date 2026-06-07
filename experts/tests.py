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
        from experts.models import Payment
        p = self._project()
        # To'lov held bo'lishi kerak (yangi guard)
        Payment.objects.create(project=p, entrepreneur=self.ent, amount=100, status='held')
        rm = Roadmap.objects.create(analysis=self.analysis, total_days=10)
        RoadmapStep.objects.create(roadmap=rm, title='Q1', order=1, duration_days=5, is_completed=True)
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


class DeclineAndCancelTests(TestCase):
    """project_decline va project_cancel guard'lari."""

    def setUp(self):
        self.ent = CustomUser.objects.create_user(username='ent_dc', password='p', role='entrepreneur')
        self.exp = CustomUser.objects.create_user(username='exp_dc', password='p', role='expert')
        ind = Industry.objects.create(name='SohaDC')
        std = Standard.objects.create(code='ISO-DC', name='Test', type='international')
        self.analysis = GapAnalysis.objects.create(
            entrepreneur=self.ent, industry=ind, local_standard=std,
            target_standard=std, status='completed', ai_result={'s': 1},
        )

    def test_expert_can_decline_pending(self):
        """Expert pending loyihani rad eta oladi."""
        p = Project.objects.create(
            analysis=self.analysis, entrepreneur=self.ent, expert=self.exp, status='pending'
        )
        self.client.force_login(self.exp)
        self.client.post(reverse('project_decline', args=[p.pk]))
        p.refresh_from_db()
        self.assertEqual(p.status, 'cancelled')

    def test_expert_cannot_decline_non_pending(self):
        """in_progress loyihani rad etib bo'lmaydi."""
        p = Project.objects.create(
            analysis=self.analysis, entrepreneur=self.ent, expert=self.exp, status='in_progress'
        )
        self.client.force_login(self.exp)
        self.client.post(reverse('project_decline', args=[p.pk]))
        p.refresh_from_db()
        self.assertNotEqual(p.status, 'cancelled')

    def test_entrepreneur_can_cancel_pending(self):
        """Tadbirkor pending loyihani bekor qila oladi."""
        p = Project.objects.create(
            analysis=self.analysis, entrepreneur=self.ent, expert=self.exp, status='pending'
        )
        self.client.force_login(self.ent)
        self.client.post(reverse('project_cancel', args=[p.pk]))
        p.refresh_from_db()
        self.assertEqual(p.status, 'cancelled')

    def test_entrepreneur_can_cancel_negotiating(self):
        """Tadbirkor negotiating loyihani bekor qila oladi."""
        p = Project.objects.create(
            analysis=self.analysis, entrepreneur=self.ent, expert=self.exp, status='negotiating'
        )
        self.client.force_login(self.ent)
        self.client.post(reverse('project_cancel', args=[p.pk]))
        p.refresh_from_db()
        self.assertEqual(p.status, 'cancelled')

    def test_entrepreneur_cannot_cancel_in_progress(self):
        """To'lov amalga oshgandan keyin bekor qilib bo'lmaydi."""
        p = Project.objects.create(
            analysis=self.analysis, entrepreneur=self.ent, expert=self.exp, status='in_progress'
        )
        self.client.force_login(self.ent)
        self.client.post(reverse('project_cancel', args=[p.pk]))
        p.refresh_from_db()
        self.assertNotEqual(p.status, 'cancelled')


class PaymentFlowTests(TestCase):
    """To'lov oqimi: MOCK confirm, release, escrow mantiq."""

    def setUp(self):
        self.ent = CustomUser.objects.create_user(username='ent_p', password='p', role='entrepreneur')
        self.exp = CustomUser.objects.create_user(username='exp_p', password='p', role='expert')
        self.wallet = Wallet.objects.create(user=self.exp, balance=Decimal('0'))
        ind = Industry.objects.create(name='Soha2')
        std = Standard.objects.create(code='ISO 9001:2015', name='QMS2', type='international')
        self.analysis = GapAnalysis.objects.create(
            entrepreneur=self.ent, industry=ind, local_standard=std,
            target_standard=std, status='completed', ai_result={'s': 1},
        )

    def _accepted_project(self):
        p = Project.objects.create(
            analysis=self.analysis, entrepreneur=self.ent, expert=self.exp,
            status='accepted', expert_price=Decimal('1000'),
        )
        return p

    def test_payment_confirm_mock_creates_payment_and_starts_project(self):
        """MOCK to'lov payment yaratadi va loyihani in_progress qiladi."""
        p = self._accepted_project()
        self.client.force_login(self.ent)
        resp = self.client.post(reverse('payment_confirm', args=[p.pk]))
        self.assertEqual(resp.status_code, 302)
        p.refresh_from_db()
        self.assertEqual(p.status, 'in_progress')
        payment = Payment.objects.get(project=p)
        self.assertEqual(payment.status, 'held')
        self.assertEqual(payment.amount, Decimal('1000'))

    def test_payment_confirm_double_payment_blocked(self):
        """Ikkinchi to'lov rad etiladi (held payment mavjud)."""
        p = self._accepted_project()
        Payment.objects.create(project=p, entrepreneur=self.ent, amount=Decimal('1000'), status='held')
        p.status = 'in_progress'
        p.save()
        self.client.force_login(self.ent)
        resp = self.client.post(reverse('payment_confirm', args=[p.pk]))
        self.assertEqual(Payment.objects.filter(project=p).count(), 1)

    def test_payment_release_happy_path(self):
        """Review statusdagi loyiha uchun pul release bo'ladi, expert walletga tushadi."""
        p = Project.objects.create(
            analysis=self.analysis, entrepreneur=self.ent, expert=self.exp,
            status='review', expert_price=Decimal('1000'),
        )
        payment = Payment.objects.create(
            project=p, entrepreneur=self.ent, amount=Decimal('1000'), status='held'
        )
        self.client.force_login(self.ent)
        resp = self.client.post(reverse('payment_release', args=[p.pk]))
        self.assertEqual(resp.status_code, 302)
        p.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(p.status, 'completed')
        self.assertEqual(payment.status, 'released')
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, payment.expert_amount)

    def test_payment_release_blocked_before_review(self):
        """in_progress loyihada pul chiqarib bo'lmaydi."""
        p = Project.objects.create(
            analysis=self.analysis, entrepreneur=self.ent, expert=self.exp,
            status='in_progress', expert_price=Decimal('1000'),
        )
        Payment.objects.create(project=p, entrepreneur=self.ent, amount=Decimal('1000'), status='held')
        self.client.force_login(self.ent)
        self.client.post(reverse('payment_release', args=[p.pk]))
        p.refresh_from_db()
        self.assertNotEqual(p.status, 'completed')


class DisputeResolutionTests(TestCase):
    """Admin nizo hal qilish — pul oqimi."""

    def setUp(self):
        self.ent = CustomUser.objects.create_user(username='ent_d', password='p', role='entrepreneur')
        self.exp = CustomUser.objects.create_user(username='exp_d', password='p', role='expert')
        self.admin = CustomUser.objects.create_user(
            username='adm_d', password='p', role='admin', is_staff=True,
        )
        self.wallet = Wallet.objects.create(user=self.exp, balance=Decimal('0'))
        ind = Industry.objects.create(name='Soha3')
        std = Standard.objects.create(code='ISO 14001', name='EMS', type='international')
        self.analysis = GapAnalysis.objects.create(
            entrepreneur=self.ent, industry=ind, local_standard=std,
            target_standard=std, status='completed', ai_result={'s': 1},
        )
        self.project = Project.objects.create(
            analysis=self.analysis, entrepreneur=self.ent, expert=self.exp,
            status='in_progress', expert_price=Decimal('500'),
        )
        self.payment = Payment.objects.create(
            project=self.project, entrepreneur=self.ent, amount=Decimal('500'), status='held',
        )
        self.dispute = Dispute.objects.create(
            project=self.project, opened_by=self.ent, reason='Sifatsiz ish',
        )

    def test_resolve_favor_expert_releases_payment(self):
        """Expert foydasiga hal qilinsa, pul expertga o'tadi."""
        self.client.force_login(self.admin)
        self.client.post(
            reverse('admin_resolve_dispute', args=[self.dispute.pk]),
            {'decision': 'Expert to\'g\'ri', 'status': 'resolved', 'favor': 'expert'},
        )
        self.wallet.refresh_from_db()
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'released')
        self.assertEqual(self.wallet.balance, self.payment.expert_amount)

    def test_resolve_favor_entrepreneur_refunds_payment(self):
        """Tadbirkor foydasiga hal qilinsa, payment refunded bo'ladi."""
        self.client.force_login(self.admin)
        self.client.post(
            reverse('admin_resolve_dispute', args=[self.dispute.pk]),
            {'decision': 'Tadbirkor to\'g\'ri', 'status': 'resolved', 'favor': 'entrepreneur'},
        )
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'refunded')

    def test_resolve_no_favor_no_payment_change(self):
        """Pulsiz hal qilinsa payment held qoladi."""
        self.client.force_login(self.admin)
        self.client.post(
            reverse('admin_resolve_dispute', args=[self.dispute.pk]),
            {'decision': 'Hal qilindi', 'status': 'resolved', 'favor': 'none'},
        )
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'held')

    def test_double_resolve_blocked(self):
        """Allaqachon hal qilingan nizo qayta hal qilinmaydi."""
        self.dispute.status = 'resolved'
        self.dispute.save()
        self.client.force_login(self.admin)
        resp = self.client.post(
            reverse('admin_resolve_dispute', args=[self.dispute.pk]),
            {'decision': 'qayta', 'status': 'resolved', 'favor': 'expert'},
        )
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'held')


class ScopeRequestTests(TestCase):
    def setUp(self):
        self.ent = CustomUser.objects.create_user(username='ent_sr', password='pass', role='entrepreneur')
        self.exp = CustomUser.objects.create_user(username='exp_sr', password='pass', role='expert')
        ind = Industry.objects.create(name='Test')
        std = Standard.objects.create(code='ISO 9001', name='ISO 9001', type='international')
        analysis = GapAnalysis.objects.create(
            entrepreneur=self.ent, industry=ind,
            target_standard=std, status='completed',
        )
        self.project = Project.objects.create(
            analysis=analysis,
            entrepreneur=self.ent,
            expert=self.exp,
            status='in_progress',
            expert_price=Decimal('500'),
        )
        Payment.objects.create(
            project=self.project,
            entrepreneur=self.ent,
            amount=Decimal('500'),
            status='held',
        )

    def test_expert_can_send_scope_request(self):
        self.client.force_login(self.exp)
        url = reverse('scope_request_send', kwargs={'pk': self.project.pk})
        resp = self.client.post(url, {'extra_price': '150', 'reason': 'Ko\'shimcha ish topildi'})
        self.assertEqual(resp.status_code, 302)
        from .models import ScopeRequest
        self.assertEqual(ScopeRequest.objects.filter(project=self.project).count(), 1)
        sr = ScopeRequest.objects.get(project=self.project)
        self.assertEqual(sr.status, 'pending')
        self.assertEqual(sr.extra_price, Decimal('150'))

    def test_entrepreneur_cannot_send_scope_request(self):
        self.client.force_login(self.ent)
        url = reverse('scope_request_send', kwargs={'pk': self.project.pk})
        resp = self.client.post(url, {'extra_price': '100', 'reason': 'test'})
        # Redirect back with error (not expert)
        self.assertEqual(resp.status_code, 302)
        from .models import ScopeRequest
        self.assertEqual(ScopeRequest.objects.count(), 0)

    def test_duplicate_pending_request_blocked(self):
        from .models import ScopeRequest
        ScopeRequest.objects.create(
            project=self.project, expert=self.exp,
            reason='first', extra_price=Decimal('100'),
        )
        self.client.force_login(self.exp)
        url = reverse('scope_request_send', kwargs={'pk': self.project.pk})
        self.client.post(url, {'extra_price': '50', 'reason': 'second'})
        self.assertEqual(ScopeRequest.objects.count(), 1)

    def test_entrepreneur_can_accept_scope_request(self):
        from .models import ScopeRequest
        sr = ScopeRequest.objects.create(
            project=self.project, expert=self.exp,
            reason='Ko\'shimcha', extra_price=Decimal('200'),
        )
        self.client.force_login(self.ent)
        url = reverse('scope_request_respond', kwargs={'pk': self.project.pk, 'sr_pk': sr.pk})
        resp = self.client.post(url, {'action': 'accept'})
        self.assertEqual(resp.status_code, 302)
        sr.refresh_from_db()
        self.assertEqual(sr.status, 'accepted')

    def test_entrepreneur_can_reject_scope_request(self):
        from .models import ScopeRequest
        sr = ScopeRequest.objects.create(
            project=self.project, expert=self.exp,
            reason='Ko\'shimcha', extra_price=Decimal('200'),
        )
        self.client.force_login(self.ent)
        url = reverse('scope_request_respond', kwargs={'pk': self.project.pk, 'sr_pk': sr.pk})
        resp = self.client.post(url, {'action': 'reject'})
        self.assertEqual(resp.status_code, 302)
        sr.refresh_from_db()
        self.assertEqual(sr.status, 'rejected')

    def test_invalid_extra_price_rejected(self):
        self.client.force_login(self.exp)
        url = reverse('scope_request_send', kwargs={'pk': self.project.pk})
        self.client.post(url, {'extra_price': '-50', 'reason': 'test'})
        from .models import ScopeRequest
        self.assertEqual(ScopeRequest.objects.count(), 0)

    def test_wrong_status_project_blocked(self):
        self.project.status = 'completed'
        self.project.save()
        self.client.force_login(self.exp)
        url = reverse('scope_request_send', kwargs={'pk': self.project.pk})
        self.client.post(url, {'extra_price': '100', 'reason': 'test'})
        from .models import ScopeRequest
        self.assertEqual(ScopeRequest.objects.count(), 0)
