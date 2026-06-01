"""accounts ilovasi uchun testlar — ro'yxatdan o'tish validatsiyasi (yaqinda tuzatilgan bug)."""
from django.test import TestCase
from django.urls import reverse
from .models import CustomUser, ExpertProfile, EntrepreneurProfile


class RegisterValidationTests(TestCase):
    def setUp(self):
        self.url = reverse('register')
        self.valid = {
            'first_name': 'Ali', 'last_name': 'Valiyev',
            'username': 'aliv', 'email': 'ali@test.uz',
            'password': 'parol12345', 'password2': 'parol12345',
            'role': 'entrepreneur',
        }

    def test_valid_registration_creates_user_and_profile(self):
        resp = self.client.post(self.url, self.valid)
        self.assertEqual(resp.status_code, 302)  # dashboardga redirect
        user = CustomUser.objects.get(username='aliv')
        self.assertEqual(user.role, 'entrepreneur')
        self.assertTrue(EntrepreneurProfile.objects.filter(user=user).exists())

    def test_expert_registration_creates_expert_profile(self):
        data = {**self.valid, 'username': 'expert1', 'email': 'e@test.uz', 'role': 'expert'}
        self.client.post(self.url, data)
        user = CustomUser.objects.get(username='expert1')
        self.assertTrue(ExpertProfile.objects.filter(user=user).exists())

    def test_empty_first_name_no_crash(self):
        """Avval first_name None bo'lsa 500 crash edi — endi xato xabari."""
        data = {**self.valid, 'first_name': ''}
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200)  # crash emas, formaga qaytadi
        self.assertFalse(CustomUser.objects.filter(username='aliv').exists())

    def test_short_password_rejected(self):
        data = {**self.valid, 'password': 'qisqa', 'password2': 'qisqa'}
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(username='aliv').exists())

    def test_password_mismatch_rejected(self):
        data = {**self.valid, 'password2': 'boshqaparol99'}
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(username='aliv').exists())

    def test_duplicate_username_rejected(self):
        CustomUser.objects.create_user(username='aliv', password='x', role='entrepreneur')
        resp = self.client.post(self.url, self.valid)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(CustomUser.objects.filter(username='aliv').count(), 1)

    def test_invalid_role_rejected(self):
        data = {**self.valid, 'role': 'hacker'}
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(username='aliv').exists())


class LoginTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='loginuser', password='parol12345', role='entrepreneur',
        )

    def test_login_success(self):
        resp = self.client.post(reverse('login'), {
            'username': 'loginuser', 'password': 'parol12345',
        })
        self.assertEqual(resp.status_code, 302)

    def test_login_wrong_password(self):
        resp = self.client.post(reverse('login'), {
            'username': 'loginuser', 'password': 'notri',
        })
        self.assertEqual(resp.status_code, 200)  # formaga qaytadi

    def test_login_no_role_needed_redirects_by_role(self):
        """Login'da rol tanlanmaydi — tizim rolga qarab yo'naltiradi."""
        expert = CustomUser.objects.create_user(
            username='exp_login', password='parol12345', role='expert',
        )
        # rol YUBORILMAYDI
        resp = self.client.post(reverse('login'), {
            'username': 'exp_login', 'password': 'parol12345',
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        # expert dashboard'ga yetib borishi kerak
        self.assertEqual(resp.request['PATH_INFO'], reverse('expert_dashboard'))
