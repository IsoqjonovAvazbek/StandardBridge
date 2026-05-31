"""experts ilovasi uchun testlar — hamyon va pul yechish (Decimal bug tuzatilgan joy)."""
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from accounts.models import CustomUser
from .models import Wallet, WithdrawalRequest


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
