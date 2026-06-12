"""accounts ilovasi uchun testlar — ro'yxatdan o'tish validatsiyasi."""
from django.test import TestCase
from django.urls import reverse
from .models import CustomUser, ExpertProfile, EntrepreneurProfile


class RegisterValidationTests(TestCase):
    def setUp(self):
        self.url = reverse('register')
        self.valid = {
            'first_name': 'Ali', 'last_name': 'Valiyev',
            'email': 'ali@test.uz',
            'password': 'parol12345', 'password2': 'parol12345',
            'role': 'entrepreneur',
        }

    def test_valid_registration_creates_user_and_profile(self):
        resp = self.client.post(self.url, self.valid)
        self.assertEqual(resp.status_code, 302)
        user = CustomUser.objects.get(email='ali@test.uz')
        self.assertEqual(user.role, 'entrepreneur')
        self.assertTrue(EntrepreneurProfile.objects.filter(user=user).exists())

    def test_username_auto_generated_from_email(self):
        self.client.post(self.url, self.valid)
        user = CustomUser.objects.get(email='ali@test.uz')
        self.assertTrue(len(user.username) > 0)
        self.assertIn('ali', user.username)

    def test_expert_registration_creates_expert_profile(self):
        data = {**self.valid, 'email': 'e@test.uz', 'role': 'expert', 'phone': '+998901234567'}
        self.client.post(self.url, data)
        user = CustomUser.objects.get(email='e@test.uz')
        self.assertTrue(ExpertProfile.objects.filter(user=user).exists())

    def test_empty_first_name_no_crash(self):
        data = {**self.valid, 'first_name': ''}
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(email='ali@test.uz').exists())

    def test_short_password_rejected(self):
        data = {**self.valid, 'password': 'qisqa', 'password2': 'qisqa'}
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(email='ali@test.uz').exists())

    def test_password_mismatch_rejected(self):
        data = {**self.valid, 'password2': 'boshqaparol99'}
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(email='ali@test.uz').exists())

    def test_duplicate_email_rejected(self):
        self.client.post(self.url, self.valid)
        self.client.logout()
        resp = self.client.post(self.url, {**self.valid})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(CustomUser.objects.filter(email='ali@test.uz').count(), 1)

    def test_username_collision_resolved_automatically(self):
        """Bir xil email prefixi bo'lsa username raqam qo'shib ajratiladi."""
        self.client.post(self.url, self.valid)
        self.client.logout()
        data2 = {**self.valid, 'email': 'ali@other.uz'}
        self.client.post(self.url, data2)
        u1 = CustomUser.objects.get(email='ali@test.uz')
        u2 = CustomUser.objects.get(email='ali@other.uz')
        self.assertNotEqual(u1.username, u2.username)

    def test_invalid_role_rejected(self):
        data = {**self.valid, 'role': 'hacker'}
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(email='ali@test.uz').exists())


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
        self.assertEqual(resp.status_code, 200)

    def test_login_no_role_needed_redirects_by_role(self):
        """Login'da rol tanlanmaydi — tizim rolga qarab yo'naltiradi."""
        CustomUser.objects.create_user(
            username='exp_login', password='parol12345', role='expert',
        )
        resp = self.client.post(reverse('login'), {
            'username': 'exp_login', 'password': 'parol12345',
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.request['PATH_INFO'], reverse('expert_dashboard'))


class AdminPanelAccessTests(TestCase):
    """Admin panel faqat admin/staff uchun ochiq bo'lishi kerak."""

    def test_entrepreneur_blocked_from_admin_panel(self):
        u = CustomUser.objects.create_user(username='ent_x', password='p', role='entrepreneur')
        self.client.force_login(u)
        resp = self.client.get(reverse('admin_panel'))
        self.assertEqual(resp.status_code, 302)

    def test_expert_blocked_from_admin_panel(self):
        u = CustomUser.objects.create_user(username='exp_x', password='p', role='expert')
        self.client.force_login(u)
        resp = self.client.get(reverse('admin_panel'))
        self.assertEqual(resp.status_code, 302)

    def test_admin_can_access(self):
        u = CustomUser.objects.create_user(
            username='adm_x', password='p', role='admin', is_staff=True, is_superuser=True,
        )
        self.client.force_login(u)
        resp = self.client.get(reverse('admin_panel'))
        self.assertEqual(resp.status_code, 200)
